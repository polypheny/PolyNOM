import pytest
from polynom.session import Session
from polynom.application import Application
from tests.model import User, Bike
from tests.utils import APP_UUID

@pytest.fixture(scope='module')
def app():
    app = Application(APP_UUID, ('localhost', 20590), use_docker=True, stop_container=True, log_statements=True)
    with app:
        yield app

@pytest.fixture(autouse=True)
def setup_test(app):

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

    init_session = Session(app, 'test')
    with init_session:
        init_session.add_all(users)
        init_session.add_all(bikes)
        init_session.commit()

    yield users, bikes, app

    cleanup_session = Session(app, 'pytest')
    with cleanup_session:
        User.query(cleanup_session).delete()
        Bike.query(cleanup_session).delete()
        cleanup_session.commit()
    
def test_query_all(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_all_filtered1(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter_by(last_name="muster").all()
        expected_entry_ids = [users[0]._entry_id, users[1]._entry_id]
        
        assert len(result) == 2
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_all_filtered2(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter_by(active=True).all()
        expected_entry_ids = [users[0]._entry_id, users[3]._entry_id]
        
        assert len(result) == 2
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_all_filtered3(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter_by(email="u4@demo.ch").all()
        
        assert len(result) == 1
        assert result[0]._entry_id == users[3]._entry_id
        
def test_query_all_filtered4(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter_by(last_name="muster", email="u1@demo.ch").all()
        
        assert len(result) == 1
        assert result[0]._entry_id == users[0]._entry_id

def test_query_all_filtered5(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter(('=', 'active', True)).all()
        expected_entry_ids = [users[0]._entry_id, users[3]._entry_id]
        
        assert len(result) == 2
        for user in result:
            assert user._entry_id in expected_entry_ids

def test_query_all_filtered6(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter(('LIKE', 'first_name', 'mir_')).all()
        expected_entry_ids = users[1]._entry_id
        
        assert len(result) == 1
        for user in result:
            assert user._entry_id == expected_entry_ids
            
def test_query_first_filtered(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter_by(is_admin=True).first()
        expected_entry_ids = [users[1]._entry_id, users[2]._entry_id]
        
        assert isinstance(result, User)
        assert result._entry_id in expected_entry_ids
            
def test_query_limit_single(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).limit(1).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == 1
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_limit_in_range(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).limit(3).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == 3
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_limit_out_of_range(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).limit(300).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
def test_query_count(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        count = User.query(session).count()
        assert count == len(users)
        
def test_query_count_after_limit(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        count = User.query(session).limit(3).count()
        assert count == 5 # limit is applied after count
        
def test_query_count_after_filter(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        count = User.query(session).filter_by(active=True).count()
        assert count == 2
        
def test_query_get(setup_test):
    users, bikes, app = setup_test
    entry_id = users[0]._entry_id

    session = Session(app, 'test')
    with session:
        result = User.query(session).get(entry_id)
        assert isinstance(result, User)
        assert result._entry_id == entry_id

def test_query_exists_present(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter_by(first_name="max").exists()
        assert result == True
        
def test_query_exists_absent(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).filter_by(first_name="chris").exists()
        assert result == False
        
def test_query_add_flush_rollback(setup_test):
    users, bikes, app = setup_test
    expected_entry_ids = [u._entry_id for u in users]

    session1 = Session(app, 'test')
    with session1:
        result = User.query(session1).all()
        assert len(result) == 5
        for user in result:
            assert user._entry_id in expected_entry_ids
            
    session2 = Session(app, 'test')
    with session2:
        new_user = User('new_user', 'new_u6@demo.ch', 'noah', 'newman', False, False)
        session2.add(new_user) 

        result = User.query(session2).all()
        assert len(result) == len(users) + 1
        for user in result:
            assert user._entry_id in expected_entry_ids or user._entry_id == new_user._entry_id
            
        session2.rollback()
        
    session3 = Session(app, 'test')
    with session3:
        result = User.query(session3).all()
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
        
def test_query_delete(setup_test):
    users, bikes, app = setup_test
    expected_entry_ids = [u._entry_id for u in users]
    new_user = User('new_user', 'new_u6@demo.ch', 'noah', 'newman', False, False)

    session1 = Session(app, 'test')
    with session1:
        result = User.query(session1).all()
        assert len(result) == 5
        for user in result:
            assert user._entry_id in expected_entry_ids
            
    session2 = Session(app, 'test')
    with session2:
        session2.add(new_user)
        session2.commit()
        
    session3 = Session(app, 'test')
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
        
def test_query_update_single(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
    with session:
        result = User.query(session).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids
            
        update_count = User.query(session).filter_by(last_name="musterin").update({"active": True})
        session.commit()
    
    session = Session(app, 'test')
    with session:
        assert update_count == 1
        result = User.query(session).get(users[3]._entry_id)
        assert result.active == True
        
def test_query_update_multiple(setup_test):
    users, bikes, app = setup_test
    session = Session(app, 'test')
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

def test_query_init_session(setup_test):
    users, bikes, app = setup_test
    Bike('Giant', 'Defy Advanced 1', users[0]._entry_id),
    session = Session(app, 'test')
    with session:
        query = Bike.query(session)
        assert query._session == session

def test_query_init_model_cls(setup_test):
    users, bikes, app = setup_test
    Bike('Giant', 'Defy Advanced 1', users[0]._entry_id),
    session = Session(app, 'test')
    with session:
        query = Bike.query(session)
        assert query._model_cls == Bike

def test_query_init_distinct(setup_test):
    users, bikes, app = setup_test
    Bike('Giant', 'Defy Advanced 1', users[0]._entry_id),
    session = Session(app, 'test')
    with session:
        query = Bike.query(session)
        assert not query._distinct
        
