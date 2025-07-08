---
layout: page
title: "Schemas and Models"
toc: true
docs_area: "PolyNOM"
tags: schema, model, fields, types
lang: en
---

## Schemas and Models

In PolyNOM, application-specific data structures are modeled using schemas and models. These are user-defined Python classes built on top of PolyNOM base classes.

- **Schemas** define the structure of the data and thus the fields of the underlying entity. This would correspond to a table definitions on a relational system.
- **Models** represent single entries within these schemas with entries corresponding to the columns of a traditional relational system.

### Step 1: Define a Schema

A schema defines:

- The name of the entity.
- The fields and their data types.
- The type and properties of the fields such as primary keys, foreign keys or unique constraints.

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
register_schema(BikeSchema)
```
It can be observed that no primary key is defined in this schema. This is permitted as PolyNOM automatically creates a entry identifier of very high probabilistic uniqueness for each inserted entry. Thereby the probability to find a duplicate within 103 trillion entries is one in a billion. This identifier field is not listed in the schema but is accessible on the corresponding model class. The use of these internal identifiers as an alternative to autoincrement or manualy managed id fields is strongly encouraged. 

### Step 2: Define a Model

A model represents a single entry for a given schema. Each model must:

- Inherit from `BaseModel`
- Declare its `schema` as a class attribute
- Define an `__init__` constructor that initializes values for all fields in the schema.

Further each model offers the field `_entry_id` which returns a unique identifier for the given entry. These identifiers are handled by PolyNOM and should not be modified or set manually.

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
    with Session(app) as session:
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

- `db_field_name` (`str`, required):  
  The name of the field in the entity on the database that will store the values of this schema field. In the normal case, this must be consistent with the name of the corresponding field in the model class.

- `polytype` (`Polytype`, required):  
  The database internal datatype to be used to store the values of that field. Te available datatypes are discussed in greated details in the next section.

- `nullable` (`bool`, optional):  
  Specifies wether the value of that field is allowed to be `None`. This defaults to `True`.

- `default` (`Any`, optional):  
  Specifies a default value to use for this field if no value had been specified. The value specified must be representable using the specified `Polytype`.

- `unique` (`bool`, optional):  
  Specifies wether the value of this field must be unique across all entries. This default to `False`.

- `python_field_name` (`str`, optional):  
  A situation might arise in which the field name used in the model class can not be used as a field name on the underlying Polypheny instance. This might be due to a conflict with a reserved key word or with data already present on the instance. In such cases an alias can be specified using this parameter. The parameter `db_field_name` then defines the name on the underlying Polypheny instance while `python_field_name` specifies the name of the corresponding field in the model class. This default to `None`.

- `previous_name` (`str`, optional):  
  This parameter is used in conjunction with automatic schema migration to rename this field. The field will be renamed from the value of this parameter to the name specified as the `db_field_name`. The default is `None`.

#### `PrimaryKeyField`

Field type specifying a field as part of the primary key. Fields of this type are not nullable.

```python
PrimaryKeyField(
    db_field_name: str,
    polytype: Type[_BaseType],
    unique: bool = False,
    python_field_name: str = None,
    previous_name: str = None
)
```

- `db_field_name` (`str`, required):  
  The name of the field in the entity on the database that will store the values of this schema field. In the normal case, this must be consistent with the name of the corresponding field in the model class.

- `polytype` (`Polytype`, required):  
  The database internal datatype to be used to store the values of that field. Te available datatypes are discussed in greated details in the next section.

- `unique` (`bool`, optional):  
  Specifies wether the value of this field must be unique across all entries. This default to `False`.

- `python_field_name` (`str`, optional):  
  A situation might arise in which the field name used in the model class can not be used as a field name on the underlying Polypheny instance. This might be due to a conflict with a reserved key word or with data already present on the instance. In such cases an alias can be specified using this parameter. The parameter `db_field_name` then defines the name on the underlying Polypheny instance while `python_field_name` specifies the name of the corresponding field in the model class. This default to `None`.

- `previous_name` (`str`, optional):  
  This parameter is used in conjunction with automatic schema migration to rename this field. The field will be renamed from the value of this parameter to the name specified as the `db_field_name`. The default is `None`.

#### `ForeignKeyField`

This field references a field of another entity.

```python
ForeignKeyField(
    db_field_name: str,
    polytype: Type[_BaseType],
    referenced_entity_name: str,
    referenced_db_field_name: str,
    nullable: bool = True,
    unique: bool = False,
    python_field_name: str = None,
    previous_name: str = None
)
```

- `db_field_name` (`str`, required):  
  The name of the field in the entity on the database that will store the values of this schema field. In the normal case, this must be consistent with the name of the corresponding field in the model class.

- `polytype` (`Polytype`, required):  
  The database internal datatype to be used to store the values of that field. Te available datatypes are discussed in greated details in the next section.

- `referenced_entity_name` (`str`, required):  
  The name of the entity from which the referenced field originates.

- `referenced_db_field_name` (`str`, required):  
  The name of the referenced field.

- `nullable` (`bool`, optional):  
  Specifies wether the value of that field is allowed to be `None`. This defaults to `True`.

- `unique` (`bool`, optional):  
  Specifies wether the value of this field must be unique across all entries. This default to `False`.

- `python_field_name` (`str`, optional):  
  A situation might arise in which the field name used in the model class can not be used as a field name on the underlying Polypheny instance. This might be due to a conflict with a reserved key word or with data already present on the instance. In such cases an alias can be specified using this parameter. The parameter `db_field_name` then defines the name on the underlying Polypheny instance while `python_field_name` specifies the name of the corresponding field in the model class. This default to `None`.

- `previous_name` (`str`, optional):  
  This parameter is used in conjunction with automatic schema migration to rename this field. The field will be renamed from the value of this parameter to the name specified as the `db_field_name`. The default is `None`.

### Data Types
These types can be specified for `Field`, `PrimaryKeyField`, and `ForeignKeyField` to define the data format and constraints in the schema. Each polytype maps to a specific Python type.

#### `VarChar(length: int)`
UTF-8 String with variable length. The maximum length is specified as parameter.
- **Python type**: `str`
- **Polytype**: `VARCHAR(length)`

#### `Text()`
UTF-8 String with a size of up to 1GB.
- **Python type**: `str`
- **Polytype**: `TEXT`

#### `Integer()`
4 bytes, signed (two’s complement). Covers a range from `-2,147,483,648` to `2,147,483,647`.
- **Python type**: `int`
- **Polytype**: `INTEGER`

#### `SmallInt()`
2 bytes, signed (two’s complement). Covers a range from `-32,768` to `32,767`.
- **Python type**: `int`
- **Polytype**: `SMALLINT`

#### `TinyInt()`
1 byte, signed (two’s complement). Covers a range from `-128` to `127`.
- **Python type**: `int`
- **Polytype**: `TINYINT`

#### `BigInt()`
8 bytes signed (two’s complement). Ranges from `-9,223,372,036,854,775,808` to `9,223,372,036,854,775,807`.
- **Python type**: `int`
- **Polytype**: `BIGINT`

#### `Double()`
8 bytes IEEE 754. Covers a range from `4.94065645841246544e-324d` to `1.79769313486231570e+308d` (positive or negative).
- **Python type**: `float`
- **Polytype**: `DOUBLE`

#### `Real()`
4 bytes, IEEE 754. Covers a range from `1.40129846432481707e-45` to `3.40282346638528860e+38` (positive or negative).
- **Python type**: `float`
- **Polytype**: `REAL`

#### `Decimal(precision=64, scale=32)`
A decimal number is a number that can have a decimal point in it. This type has two arguments: precision (max. 64) and scale (max. 64). Precision is the total number of digits, scale is the number of digits to the right of the decimal point. The scale can not exceed the precision. If no arguments are provided, the default is `64,32`.
- **Python type**: `decimal.Decimal`
- **Polytype**: `DECIMAL(precision, scale)`

#### `Boolean()`
1-bit. Takes the values `true` and `false`.
- **Python type**: `bool`
- **Polytype**: `BOOLEAN`

#### `Date()`
Represents a date. Format: `yyyy-mm-dd`
- **Python type**: `datetime.date`
- **Polytype**: `DATE`

#### `Time(precision=0)`
Represents a time of day without time zone. Optionally, precision can have a value between 0 and 3 specifying the number of fractional seconds. Format: `hh:mm:ss.f`
- **Python type**: `datetime.time`
- **Polytype**: `TIME(precision)`

#### `Timestamp(precision=0)`
Represents a combination of DATE and TIME values. Optionally, precision can have a value between 0 and 3 specifying the number of fractional seconds. Format: `yyyy-mm-dd hh:mm:ss.f`
- **Python type**: `datetime.datetime`
- **Polytype**: `TIMESTAMP(precision)`
- **Usage**: Stores date and time values with optional sub-second precision.

#### `Json()`
A wrapper provided by PolyNOM for the native `TEXT` type. Allowed values are all objects compatible with `json.dump()` and `json.load()`. This type can be used to persist arbitrary json serializable objects.

- **Python type**: `dict`
- **Polytype**: `TEXT`
- **Usage**: JSON-encoded dictionary.

#### `PolyEnum(python_enum: Type[Enum])`
A wrapper provided by PolyNOM for the native `TEXT` type. The name of the enum member is persisted on the underlying Polypheny instance while PolyNOM derives names from members and members from names.
- **Python type**: `enum.Enum`
- **Polytype**: `TEXT`

#### `File()`
Accepts arbitrary strings of binary data. 
- **Python type**: `bytes`
- **Polytype**: `File`

#### `Geometry()`
A wrapper provided by PolyNOM for the native `TEXT` type. Stores geometry objects of the shapely library. Those are converted to geo json and persisted on the underlying instance as `TEXT`. In the future this will push down the geometry handling to Polpyheny using the polypheny native geometry type. 
- **Python type**: `bytes`
- **Polytype**: `File`

