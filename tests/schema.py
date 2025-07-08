from polynom.schema.schema_registry import register_schema
from polynom.schema.field import Field, PrimaryKeyField, ForeignKeyField
from polynom.schema.polytypes import VarChar, Integer, Boolean
from polynom.schema.schema import BaseSchema
from polynom.schema.relationship import Relationship

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

class BikeSchema(BaseSchema):
    entity_name = 'Bike'
    fields = [
        Field('brand', VarChar(50), nullable=False),
        Field('model', VarChar(50), nullable=False),
        ForeignKeyField(
            db_field_name='owner_id',
            polytype=VarChar(36),
            referenced_entity_name='User',
            referenced_db_field_name='_entry_id',
            nullable=False,
            python_field_name='owner_id'
        ),
    ]

register_schema(UserSchema)
register_schema(BikeSchema)
