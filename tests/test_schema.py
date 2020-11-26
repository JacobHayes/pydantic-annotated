from typing import Annotated, get_origin, get_type_hints

from pydantic_annotated import (
    GE,
    Alias,
    BaseModel,
    Default,
    Description,
    FieldAnnotation,
    _pydantic_is_annotated_aware,
)


def test_model():
    class Model(BaseModel):
        x: Annotated[int, Alias("x"), Default(5)]

    assert Model().x == 5
    if _pydantic_is_annotated_aware:
        x_hint = get_type_hints(Model, include_extras=True)["x"]
        assert get_origin(x_hint) is Annotated


def test_nested_annotations():
    # Nested annotations should prefer the last value. We may consider supporting multiple instances
    # for certain annotations (ex: Alias), but that would require upstream pydantic support.
    class Model(BaseModel):
        x: Annotated[Annotated[int, Default(5)], Default(10)]

    assert Model().x == 10


def test_complex_annotations():
    PII = FieldAnnotation.named("PII")
    # Do we want to support linking a model/type with an annotation?
    ComplexAnnotation = FieldAnnotation.named("complex_annotation")

    class ComplexModel(BaseModel):
        x: int
        y: int

    class FooBar(BaseModel):
        count: Annotated[
            int,
            Alias("cnt"),
            Description("Count of FooBars"),
            GE(0),
            PII(False),
            ComplexAnnotation(ComplexModel(x=1, y=2)),
        ]

    assert FooBar.schema() == {
        "title": "FooBar",
        "type": "object",
        "properties": {
            "cnt": {
                "title": "Cnt",
                "description": "Count of FooBars",
                "minimum": 0,
                "PII": False,
                "complex_annotation": ComplexModel(x=1, y=2),
                "type": "integer",
            }
        },
        "required": ["cnt"],
    }
