
---
layout: page
title: "Relationships"
toc: true
docs_area: "PolyNOM"
tags: model, schema, reference, foreign, back_ref, child, parent
lang: en
---

## Relationships

Referencing between entities in PolyNOM can be achieved using two complementary mechanisms: The first one are database-level references using `ForeignKeyField`, which define relationships in the underlying Polypheny instance. The second one are model-level references using `Relationship`, which provide Pythonic, bidirectional access between model objects. This guide demonstrates both approaches using a simple example: an `Owner` who can own zero or more `Bike`s, and each `Bike` optionally being owned by a single `Owner`.

### Foreign Key References

Schema-level references define how entities relate at the database level. These do not automatically create any navigable object relationships in Python.

#### Step 1a: Define a Schema for the `Owner`

First, a simple schema for the `Owner` id created. No references are defined here yet.

```python
from polynom.schema.schema_registry import polynom_schema
from polynom.schema.field import Field
from polynom.schema.polytypes import VarChar
from polynom.schema.schema import BaseSchema

@polynom_schema
class OwnerSchema(BaseSchema):
    namespace_name = 'users'
    entity_name = 'Owner'

    fields = [
        Field('name', VarChar(100), nullable=False),
        Field('email', VarChar(100), nullable=False, unique=True),
    ]
```

#### Step 1b: Define a Schema for the `Bike`

This step creates the schema for the `Bike`. We use a `ForeignKeyField` to create a reference to the `OwnerSchema`. If a specific field is not provided in addition to the `referenced_schema`, PolyNOM falls back to the internal entry identifier, which functions like a unique ID.

```python
from polynom.schema.field import ForeignKeyField

@polynom_schema
class BikeSchema(BaseSchema):
    namespace_name = 'vehicles'
    entity_name = 'Bike'

    fields = [
        Field('brand', VarChar(50), nullable=False),
        Field('model', VarChar(50), nullable=False),
        Field('series', VarChar(50), nullable=False),
        Field('weight', Decimal(), nullable=False),
        Field('price', Decimal()),
        ForeignKeyField('owner_id', referenced_schema=OwnerSchema),
        # example for specific field: ForeignKeyField('owner_id', referenced_schema=OwnerSchema, referenced_db_field_name='name'),
    ]
```

### Object Relationships

To interact with related models naturally in Python, `Relationship` fields can be defined in the model classes. These work independently of `ForeignKeyField` and are purely for object-level navigation. No mapping onto the underlying polypheny instance is performed.

The `back_populates` parameter in a `Relationship` defines the name of the corresponding attribute on the related object that should be automatically synchronized. This creates a bidirectional link between two models, allowing changes on one side of the relationship to reflect on the other.

Use `back_populates` when:
- automatic synchronization between two related model attributes is required.
- a **two-way connection** (e.g., `bike.owner` and `owner.bikes`) is desired.
- consistency should be enforced by updating both sides: assigning one side updates the other.

One can ommit `back_populates` if:
- Only a one way reference is needed.
- The possibility for circular dependencies should be reduced.


#### Step 2a: One-Way Relationship on the `Bike` Model

By adding a `Relationship` on the `Bike` model (with `back_populates`), a link to its `Owner` is created.

```python
from polynom.model import BaseModel
from polynom.model.relationship import Relationship

class Bike(BaseModel):
    schema = BikeSchema()

    owner: Owner = Relationship(Owner, back_populates="bikes")

    def __init__(self, brand, model, series, weight, price, owner_id, _entry_id=None):
        super().__init__(_entry_id)
        self.brand = brand
        self.model = model
        self.series = series
        self.weight = weight
        self.price = price
        self.owner_id = owner_id
```
In this example, `back_populates="bikes"` specifies that the owner attribute on Bike corresponds to the bikes attribute on Owner. When an Owner is assigned to bike.owner, the bike will automatically be added to the owner’s bikes list.

#### Step 2b: Bidirectional Relationship on the `Owner` Model

To complete the two-way relationship, a `bikes` relationship is added to the `Owner` model that links back to the `Bike`'s `owner`. This allows seamless access in both directions:

- `bike.owner` → Owner instance
- `owner.bikes` → List of Bike instances

```python
class Owner(BaseModel):
    schema = OwnerSchema()

    bikes: Bike = Relationship("Bike", back_populates="owner")

    def __init__(self, name, email, _entry_id=None):
        super().__init__(_entry_id)
        self.name = name
        self.email = email
```
Here, the back_populates="owner" on the Owner side completes the bidirectional link. Both sides must specify back_populates with the matching attribute name to ensure automatic synchronization. Mismatched or missing back_populates may cause inconsistencies or runtime errors.

### Many-to-many Relationships
When a relationship involves multiple instances on both sides such as many `Cyclists` belonging to many `Teams` a simple foreign key in one schema is not sufficient. In these cases, an association entity can be used at the schema level to map the many-to-many relationship. This entity contains foreign keys pointing to each related schema to link them.

An example of an association entity to link `Cyclists` and `Teams` is given below:

```python
class TeamCyclistAssocSchema(BaseSchema):
    fields = [
        ForeignKeyField('team_id', referenced_schema=TeamSchema),
        ForeignKeyField('cyclist_id', referenced_schema=CyclistSchema)
    ]
```

## Circular Dependencies

Consider a bidirectional relationship between two models, `Author` and `Book`. Model `Author` must define a relationship to `Book`, and `Book` must define a relationship back to `Author`. However, at the time `Author` is being defined, the `Book` class might not yet be declared. This results in a circular dependency issue if direct class references are used.
To circumvent this limitation, model classes can also be specified using their **fully qualified name** (FQN) as a string, instead of a direct class reference. The FQN follows Python's standard module path syntax, such as:

```
"myapp.models.author.Author"
```

All models intended to be used in this way must be registered using the `@polynom_model` decorator. The model can then be resolved lazily at runtime, avoiding import-time circular dependency errors.

### Example

```python
# myapp/models/author.py

from polynom.model import BaseModel, Relationship, polynom_model

@polynom_model
class Author(BaseModel):
    books = Relationship(
        target_model="myapp.models.book.Book",  # FQN string reference
        back_populates="author"
    )
```

```python
# myapp/models/book.py

from polynom.model import BaseModel, Relationship, polynom_model
from myapp.models.author import Author  # optional, needed only if directly referencing Author

@polynom_model
class Book(BaseModel):
    author = Relationship(
        target_model=Author,
        back_populates="books"
    )
```
