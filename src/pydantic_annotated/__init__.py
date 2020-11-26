from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional, get_args, get_origin, no_type_check

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


class FieldAnnotation:
    name: Optional[str] = None

    def __init__(self, value: Any):
        self.value = value

    def populate_field_info(self, field_info: FieldInfo):
        if hasattr(field_info, self.name):
            setattr(field_info, self.name, self.value)
        else:  # Add to extra
            field_info.extra[self.name] = self.value

    @classmethod
    def create_field_info(cls, annotation, value=Undefined):
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

    @classmethod
    def named(cls, name: str) -> type[FieldAnnotation]:
        return type(
            "".join(part.title() for part in name.split("_")), (cls,), {"name": name},
        )


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


# Built in field params.
Default = FieldAnnotation.named("default")
DefaultFactory = FieldAnnotation.named("default_factory")
Alias = FieldAnnotation.named("alias")
Title = FieldAnnotation.named("title")
Description = FieldAnnotation.named("description")
Const = FieldAnnotation.named("const")
GT = FieldAnnotation.named("gt")
GE = FieldAnnotation.named("ge")
LT = FieldAnnotation.named("lt")
LE = FieldAnnotation.named("le")
MultipleOf = FieldAnnotation.named("multiple_of")
MinItems = FieldAnnotation.named("min_items")
MaxItems = FieldAnnotation.named("max_items")
MinLength = FieldAnnotation.named("min_length")
MaxLength = FieldAnnotation.named("max_length")
Regex = FieldAnnotation.named("regex")
