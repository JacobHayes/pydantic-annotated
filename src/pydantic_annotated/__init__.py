from __future__ import annotations

from copy import deepcopy
from typing import Any, ClassVar, get_args, get_origin, no_type_check

from pydantic import BaseModel as _BaseModel
from pydantic.fields import FieldInfo, Undefined
from pydantic.main import ModelMetaclass as _ModelMetaclass
from pydantic.typing import resolve_annotations

try:
    from pydantic.typing import Annotated

    _pydantic_is_annotated_aware = True
except ImportError:
    from typing import Annotated

    _pydantic_is_annotated_aware = False


class ClassName:
    def __get__(self, obj: Any, type_: Any) -> str:
        return type_.__name__


class FieldAnnotation:
    _annotation_name: ClassVar[str] = ClassName()
    _annotation_value: Any

    def __init__(self, value: Any):
        self._annotation_value = value

    def populate_field_info(self, field_info: FieldInfo):
        if hasattr(field_info, type(self).__name__):
            setattr(field_info, self._annotation_name, self._annotation_value)
        else:  # Add to extra
            field_info.extra[self._annotation_name] = self._annotation_value

    @classmethod
    def create_field_info(cls, annotation: dict[str, Any], value: Any = Undefined):
        if isinstance(value, FieldInfo):
            # Annotations override the existing FieldInfo. Use deepcopy in case the FieldInfo is
            # used multiple times with different annotations.
            field_info, value = deepcopy(value), Undefined
        else:
            field_info = FieldInfo()
        # Populate the FieldInfo instance with our FieldAnnotations
        field_annotations = cls.collect_from_annotation(annotation)
        for field_annotation in field_annotations:
            field_annotation.populate_field_info(field_info)
        # If the value is set, use that as the default over any Default annotation.
        if value is not Undefined:
            field_info.default = value
        if (
            field_info.default is not Undefined
            and field_info.default_factory is not None
        ):
            raise ValueError("cannot specify both default and default_factory")
        return field_info

    @classmethod
    def collect_from_annotation(cls, value: Any) -> list[FieldAnnotation]:
        if get_origin(value) is not Annotated:
            raise ValueError("value must be an Annotated value!")
        # Filter to a single instance per FieldAnnotation subclass. With upstream pydantic support
        # and some tweaks here, we could support multiple of the same type (ex: Alias).
        return list(
            {type(arg): arg for arg in get_args(value) if isinstance(arg, cls)}.values()
        )


def named_field_annotation(name: str):
    return type(name, (FieldAnnotation,), {},)


# Built in field params - the names must match the FieldInfo attributes. Ideally these could be
# typed (like the FieldAnnotationModel below), but that would require more wrappers.
Default = named_field_annotation("default")
DefaultFactory = named_field_annotation("default_factory")
Alias = named_field_annotation("alias")
Title = named_field_annotation("title")
Description = named_field_annotation("description")
Const = named_field_annotation("const")
GT = named_field_annotation("gt")
GE = named_field_annotation("ge")
LT = named_field_annotation("lt")
LE = named_field_annotation("le")
MultipleOf = named_field_annotation("multiple_of")
MinItems = named_field_annotation("min_items")
MaxItems = named_field_annotation("max_items")
MinLength = named_field_annotation("min_length")
MaxLength = named_field_annotation("max_length")
Regex = named_field_annotation("regex")


class ModelMetaclass(_ModelMetaclass):
    @no_type_check  # noqa C901
    def __new__(cls, name, bases, namespace, **kwargs):  # noqa C901
        annotations = resolve_annotations(
            namespace.get("__annotations__", {}), namespace.get("__module__", None)
        )
        for field, annotation in annotations.items():
            if get_origin(annotation) is not Annotated:
                continue
            namespace[field] = FieldAnnotation.create_field_info(
                annotation=annotation, value=namespace.get(field, Undefined)
            )
            # Pydantic doesn't yet support Annotated annotations [1], so we'll unwrap the root type.
            # This prevents later inspection of the annotations with `get_type_hints`, so we'll
            # preferably avoid.
            #
            # 1: https://github.com/samuelcolvin/pydantic/pull/2147
            if not _pydantic_is_annotated_aware:
                namespace["__annotations__"][field] = get_args(annotation)[0]
        return super().__new__(cls, name, bases, namespace, **kwargs)


class BaseModel(_BaseModel, metaclass=ModelMetaclass):
    pass


class FieldAnnotationModel(BaseModel, FieldAnnotation):
    @property
    def _annotation_value(self):
        return self
