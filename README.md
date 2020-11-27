# pydantic-annotated

Proof of concept [Decomposing Field components into Annotated](https://github.com/samuelcolvin/pydantic/issues/2129).

```python
from typing import Annotated

from pydantic_annotated import BaseModel, Description, FieldAnnotationModel


class PII(FieldAnnotationModel):
    status: bool


class ComplexAnnotation(FieldAnnotationModel):
    x: int
    y: int


class Patient(BaseModel):
    name: str
    condition: Annotated[
        str,
        ComplexAnnotation(x=1, y=2),
        Description("Patient condition"),
        PII(status=True),
    ]
```
