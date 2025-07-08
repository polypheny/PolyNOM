---
layout: page
title: "Models and Schemas"
toc: true
docs_area: "PolyNOM"
tags: schema, model, fields, types
lang: en
---

## Models and Schema

In PolyNOM, application-specific data structures are modeled using **schemas** and **models**. These are user-defined Python classes built on top of PolyNOM base classes.

- **Schemas** define the structure of the data adn thus the fields of the underlying entity. This would correspond to a table definitions on a relational system.
- **Models** represent single entries within these schemas with entries corresponding to the columns of a traditional relaitonal system.

### Step 1: Define a Schema

A schema defines:

- The name of the entity.
- The fields, their data types, and constraints.
- Optional: primary keys, foreign keys, unique constraints, etc.

Each schema class must inherit from `BaseSchema` and must be registered using `register_schema()`. An example of a schema to store road bikes is given below.

```python
from polynom.schema.schema_registry import register_schema
from polynom.schema.field import Field
from polynom.schema.polytypes import VarChar, Decimal
from polynom.schema.schema import BaseSchema

class BikeSchema(BaseSchema):
    entity_name = 'Bike'
    fields = [
        Field('brand', VarChar(50), nullable=False),
        Field('series', VarChar(50), nullable=False),
        Field('model', VarChar(50), nullable=False, unique=True),
        Field('weight', Decimal(), nullable=False),
        Field('price', Decimal())
    ]

# Make schemas discoverable by PolyNOM
register_schema(UserSchema)
register_schema(BikeSchema)
```
It can be seen that no primary key is defined in this schema. This is permitted as PolyNOM automatically creates a entry identifier of very high probabilistic uniqueness (the probability to find a duplicate within 103 trillion entries is one in a billion) for each inserted entry. This identifier field is not listed in the schema but is accessible on the corresponding model class. We encurage the use of these internal identifiers as an alternative to autoincrement or manualy managed id fields. 

### Step 2: Define a Model

A model represents a single entry for a given schema. Each model must:

- Inherit from `BaseModel`
- Declare its `schema` as a class attribute
- Define an `__init__` constructor that initializes field values
- Must provide a constructor matching the fields specified in the correposnding schema
- Offers the hidden field `_entry_id` which returns a unique identifier for the given entry. These identifiers are handled by PolyNOM and should not be modified or set by the application.

The following model matches our `BikeSchema` from step one.

```python
from polynom.model import BaseModel
from myproject.bike.model import Bike

class Bike(BaseModel):
    schema = BikeSchema()

    def __init__(self, brand, series, model, weight, price, _entry_id=None):
        super().__init__(_entry_id)
        self.brand = brand
        self.series = series
        self.model = model
        self.weight = weight
        self.price = price
```

With step 1 and 2 the application-specific data structure is ready to be used as follows:
```python
from polynom.application import Application
from polynom.session import Session
from myproject.bike.model import Bike

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

with Application(APP_UUID, ('localhost', 20590)) as app:
    with Session(app, log_user="alice") as session:
        bike = Bike('Canyon', 'Aeroad', 'CFR Di2', 7.04, 8849)
        session.add(bike)
        session.commit()
```

### Field Types
When defining a schema, the following field classes are provided to describe the structure and constraints of its fields. The different field types expose specific behaviors for primary keys, foreign keys, and general-purpose fields.

#### `Field`

Defines a standard database field.

```python
Field(
    db_field_name: str,
    polytype: Type[_BaseType],
    nullable: bool = True,
    default: Any = None,
    unique: bool = False,
    python_field_name: str = None,
    previous_name: str = None
)
```
