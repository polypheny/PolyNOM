import pytest
from polynom.session.session import Session
from polynom.session.initializer import Initializer
from polynom.schema.schema_registry import register_schema
from polynom.schema.field import Field, PrimaryKeyField, ForeignKeyField
from polynom.schema.polytypes import VarChar, Integer, Boolean
from polynom.schema.schema import BaseSchema
from polynom.model import BaseModel
from polynom.schema.relationship import Relationship

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

# schema and models for test data
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

class User(BaseModel):
    schema = UserSchema()

    def __init__(self, username, email, first_name, last_name, active, is_admin, _entry_id = None):
        super().__init__(_entry_id)
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.active = active
        self.is_admin = is_admin

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
        
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

class Bike(BaseModel):
    schema = BikeSchema()
    user: User = Relationship(User, back_populates="bikes")

    def __init__(self, brand, model, owner_id, _entry_id=None):
        super().__init__(_entry_id)
        self.brand = brand
        self.model = model
        self.owner_id = owner_id

    def __repr__(self):
        return f"<Bike brand={self.brand!r}, model={self.model!r}, owner={self.owner_id!r}>"
        
register_schema(UserSchema)
register_schema(BikeSchema)

# test data
users = [
            User('testuser', 'u1@demo.ch', 'max', 'muster', True, False),
            User('testuser2', 'u2@demo.ch', 'mira', 'muster', False, True),
            User('testuser3', 'u3@demo.ch', 'miraculix', 'musterin', False, True),
            User('testuser4', 'u4@demo.ch', 'maxine', 'meier', True, False),
            User('testuser5', 'u5@demo.ch', 'mia', 'müller', False, False),
        ]

bikes = [
            Bike('Trek', 'Marlin 7', users[0]._entry_id),
            Bike('Specialized', 'Rockhopper', users[0]._entry_id),
            Bike('Cannondale', 'Trail 8', users[2]._entry_id),
            Bike('Giant', 'Talon 3', users[3]._entry_id),
        ]

@pytest.fixture(scope='module', autouse=True)
def initialize_polynom():
    Initializer(APP_UUID, ('localhost', 20590), use_docker=False).run()
    
    # insert test data
    session = Session(('localhost', 20590), 'test')
    with session:
        session.add_all(users)
        session.add_all(bikes)
        session.commit()
    yield
    
def test_query_all():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_all_filtered1():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).filter_by(last_name="muster").all()
        expected_entry_ids = [users[0]._entry_id, users[1]._entry_id]
        
        assert len(result) == 2
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_all_filtered2():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).filter_by(active=True).all()
        expected_entry_ids = [users[0]._entry_id, users[3]._entry_id]
        
        assert len(result) == 2
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_all_filtered3():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).filter_by(email="u4@demo.ch").all()
        
        assert len(result) == 1
        assert result[0]._entry_id == users[3]._entry_id
            
def test_query_first_filtered():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).filter_by(is_admin=True).first()
        expected_entry_ids = [users[1]._entry_id, users[2]._entry_id]
        
        assert isinstance(result, User)
        assert result in expected_entry_ids
            
def test_query_limit_single():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).limit(1).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == 1
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_limit_in_range():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).limit(3).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == 3
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_limit_out_of_range():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).limit(300).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_count():
    session = Session(('localhost', 20590), 'test')
    with session:
        count = User.query(session).count()
        assert count == len(users)
        
def test_query_count_after_limit():
    session = Session(('localhost', 20590), 'test')
    with session:
        count = User.query(session).limit(3).count()
        assert count == 3
        
def test_query_count_after_filter():
    session = Session(('localhost', 20590), 'test')
    with session:
        count = User.query(session).filter_by(active=True).count()
        assert count == 2
        
def test_query_get():
    entry_id = users[0]._entry_id

    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).get(entry_id)
        assert isinstance(result, User)
        assert result._entry_id == entry_id

def test_query_exists_present():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).filter_by(first_name="max").exists()
        assert result == True
        
def test_query_exists_absent():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).filter_by(first_name="chris").exists()
        assert result == False
        
def test_query_add_flush_rollback():
    expected_entry_ids = [u._entry_id for u in users]

    session1 = Session(('localhost', 20590), 'test')
    with session1:
        result = User.query(session1).all()
        assert len(result) == 5
        for user in result:
            assert user._entry_id in expected_entry_ids
            
    session2 = Session(('localhost', 20590), 'test')
    with session2:
        new_user = User('new_user', 'new_u6@demo.ch', 'noah', 'newman', False, False)
        session2.add(new_user) 

        result = User.query(session2).all()
        assert len(result) == len(users) + 1
        for user in result:
            assert user._entry_id in expected_entry_ids or user._entry_id == new_user._entry_id
            
        session2.rollback()
        
    session3 = Session(('localhost', 20590), 'test')
    with session3:
        result = User.query(session3).all()
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
        
def test_query_delete():
    expected_entry_ids = [u._entry_id for u in users]
    new_user = User('new_user', 'new_u6@demo.ch', 'noah', 'newman', False, False)

    session1 = Session(('localhost', 20590), 'test')
    with session1:
        result = User.query(session1).all()
        assert len(result) == 5
        for user in result:
            assert user._entry_id in expected_entry_ids
            
    session2 = Session(('localhost', 20590), 'test')
    with session2:
        session2.add(new_user)
        session2.commit()
        
    session3 = Session(('localhost', 20590), 'test')
    with session3:
        result = User.query(session3).all()
        assert len(result) == len(users) + 1
        for user in result:
            assert user._entry_id in expected_entry_ids or user._entry_id == new_user._entry_id
        
        delete_count = User.query(session3).filter_by(last_name="newman").delete()
        assert delete_count == 1
        
        result2 = User.query(session3).all()
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
        session.commit()
        
def test_query_update():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
        update_count = User.query(session).filter_by(last_name="muster").update({"active": False})
        assert update_count == 1
        result2 = User.query(session).get(users[1])
        assert result2.active == False
