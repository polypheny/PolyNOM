from polynom.schema.schema_registry import register_schema
from polynom.schema.field import Field, PrimaryKeyField, ForeignKeyField
from polynom.schema.polytypes import VarChar, Integer, Boolean
from polynom.model import BaseModel
from polynom.schema.relationship import Relationship
from tests.schema import UserSchema, BikeSchema

class User(BaseModel):
    schema = UserSchema()

    def __init__(self, username, email, first_name, last_name, active, is_admin, _entry_id = None):
        super().__init__(_entry_id)
        self.username: str = username
        self.email: str = email
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.active: bool = active
        self.is_admin: str = is_admin

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
        
class Bike(BaseModel):
    schema = BikeSchema()
    user: User = Relationship(User, back_populates="bikes")

    def __init__(self, brand, model, owner_id, _entry_id=None):
        super().__init__(_entry_id)
        self.brand: str = brand
        self.model: str = model
        self.owner_id: str = owner_id

    def __repr__(self):
        return f"<Bike brand={self.brand!r}, model={self.model!r}, owner={self.owner_id!r}>"
