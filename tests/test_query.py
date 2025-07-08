import pytest
from polynom.session.session import Session
from polynom.session.initializer import Initializer
from polynom.query.query import Query
from tests.schema import UserSchema, BikeSchema
from tests.model import User, Bike

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

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
        
def test_query_all_filtered4():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).filter_by(last_name="muster", email="u1@demo.ch").all()
        
        assert len(result) == 1
        assert result[0]._entry_id == users[0]._entry_id
            
def test_query_first_filtered():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).filter_by(is_admin=True).first()
        expected_entry_ids = [users[1]._entry_id, users[2]._entry_id]
        
        assert isinstance(result, User)
        assert result._entry_id in expected_entry_ids
            
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
        assert count == 5 # limit is applied after count
        
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
        
        result = User.query(session3).all()
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
        session3.commit()
        
def test_query_update_single():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
        update_count = User.query(session).filter_by(last_name="musterin").update({"active": True})
        session.commit()
    
    session = Session(('localhost', 20590), 'test')
    with session:
        assert update_count == 1
        result = User.query(session).get(users[3]._entry_id)
        assert result.active == True
        
def test_query_update_multiple():
    session = Session(('localhost', 20590), 'test')
    with session:
        result = User.query(session).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
        update_count = User.query(session).filter_by(last_name="musterin").update({"active": True, "is_admin": False})
        assert update_count == 1
        result = User.query(session).get(users[3]._entry_id)
        assert result.active == True
        assert result.is_admin == False

def test_query_init_session():
    Bike('Giant', 'Defy Advanced 1', users[0]._entry_id),
    session = Session(('localhost', 20590), 'test')
    with session:
        query = Bike.query(session)
        assert query._session == session

def test_query_init_model_cls():
    Bike('Giant', 'Defy Advanced 1', users[0]._entry_id),
    session = Session(('localhost', 20590), 'test')
    with session:
        query = Bike.query(session)
        assert query._model_cls == Bike

def test_query_init_distinct():
    Bike('Giant', 'Defy Advanced 1', users[0]._entry_id),
    session = Session(('localhost', 20590), 'test')
    with session:
        query = Bike.query(session)
        assert not query._distinct
        
