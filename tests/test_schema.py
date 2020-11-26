from typing import Annotated, get_origin, get_type_hints

from pydantic_annotated import Alias, BaseModel, Default, _pydantic_is_annotated_aware


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
