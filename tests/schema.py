from polynom.schema.schema_registry import polynom_schema
from polynom.schema.field import Field, ForeignKeyField
from polynom.schema.polytypes import VarChar, Boolean
from polynom.schema.schema import BaseSchema

@polynom_schema
class UserSchema(BaseSchema):
    entity_name = 'User'
    fields = [
        Field('username', VarChar(80), nullable=False, unique=True, previous_name='username2'),
        Field('email', VarChar(80), nullable=False, unique=True),
        Field('first_name', VarChar(30), nullable=True),
        Field('last_name', VarChar(30), nullable=True),
        Field('active', Boolean()),
        Field('is_admin', Boolean()),
    ]

@polynom_schema
class BikeSchema(BaseSchema):
    entity_name = 'Bike'
    fields = [
        Field('brand', VarChar(50), nullable=False),
        Field('model', VarChar(50), nullable=False),
        ForeignKeyField(
            db_field_name='owner_id',
            referenced_schema=UserSchema,
            nullable=False,
        ),
    ]
