from typing import Annotated, get_type_hints

from pydantic_annotated import (
    GE,
    Alias,
    BaseModel,
    Default,
    Description,
    FieldAnnotationModel,
    _pydantic_is_annotated_aware,
    named_field_annotation,
)


def test_annotation():
    x_hint = Annotated[int, Alias("x"), Default(5)]

    class FooBar(BaseModel):
        x: x_hint

    assert FooBar().x == 5
    if _pydantic_is_annotated_aware:
        assert get_type_hints(FooBar, include_extras=True)["x"] == x_hint


def test_custom_annotation():
    PII = named_field_annotation("PII")

    class FooBar(BaseModel):
        x: Annotated[int, PII(True)]

    assert FooBar.schema() == {
        "title": "FooBar",
        "type": "object",
        "properties": {"x": {"title": "X", "PII": True, "type": "integer"}},
        "required": ["x"],
    }


def test_nested_annotations():
    # Nested annotations should prefer the last value. We may consider supporting multiple instances
    # for certain annotations (ex: Alias), but that would require upstream pydantic support.
    class FooBar(BaseModel):
        x: Annotated[Annotated[int, Default(5)], Default(10)]

    assert FooBar().x == 10


def test_field_annotation_model():
    class PII(FieldAnnotationModel):
        status: bool

    class ComplexAnnotation(FieldAnnotationModel):
        x: int
        y: int

    class FooBar(BaseModel):
        count: Annotated[
            int,
            Alias("cnt"),
            ComplexAnnotation(x=1, y=2),
            Description("Count of FooBars"),
            GE(0),
            PII(status=True),
        ]

    assert FooBar.schema() == {
        "title": "FooBar",
        "type": "object",
        "properties": {
            "cnt": {
                "title": "Cnt",
                "description": "Count of FooBars",
                "minimum": 0,
                "ComplexAnnotation": ComplexAnnotation(x=1, y=2),
                "PII": PII(status=True),
                "type": "integer",
            }
        },
        "required": ["cnt"],
    }
