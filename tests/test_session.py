import pytest
from polynom.session import Session, _SessionState
from polynom.application import Application
from tests.model import User, Bike
from tests.utils import APP_UUID

@pytest.fixture(scope='module')
def app():
    app = Application(APP_UUID, ('localhost', 20590), use_docker=True, stop_container=True)
    with app:
        yield app

@pytest.fixture(autouse=True)
def setup_test(app):
    yield
    cleanup_session = Session(app, 'pytest')
    with cleanup_session:
        User.query(cleanup_session).delete()
        cleanup_session.commit()

def test_session_empty_commit(app):
    s = Session(app, 'pytest')
    with s:
        s.commit()
        
def test_session_empty_rollback(app):
    s = Session(app, 'pytest')
    with s:
        s.rollback()

def test_session_state_after_initialization(app):
    s = Session(app, 'pytest')
    assert s._state == _SessionState.INITIALIZED
        
def test_session_state_after_commit(app):
    s = Session(app, 'pytest')
    with s:
        assert s._state == _SessionState.ACTIVE
        s.commit()
        assert s._state == _SessionState.COMPLETED
        
def test_session_state_after_rollback(app):
    s = Session(app, 'pytest')
    with s:
        assert s._state == _SessionState.ACTIVE
        s.commit()
        assert s._state == _SessionState.COMPLETED
        
def test_session_add(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        s.commit()
        
    s = Session(app, 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result._entry_id == user._entry_id
        
def test_session_add_on_completed(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.add(user)
        assert 'completed Session' in str(e.value)
        
def test_session_add_outside_of_with(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    s = Session(app, 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.add(user)
    assert 'must first be activated' in str(e.value)
    
def test_session_add_all(app):
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    expected_entry_ids = [u._entry_id for u in users]
    
    s = Session(app, 'pytest')
    with s:
        s.add_all(users)
        s.commit()
        
    s = Session(app, 'pytest')
    with s:
        result = User.query(s).all()
        assert len(result) == 2
        for user in result:
            assert user._entry_id in expected_entry_ids
        
        
def test_session_add_all_on_completed(app):
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    
    s = Session(app, 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.add_all(users)
        assert 'completed Session' in str(e.value)
        
def test_session_add_all_outside_of_with(app):
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    s = Session(app, 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.add_all(users)
    assert 'must first be activated' in str(e.value)
    
    
def test_session_delete(app):
    # add data to delete
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    expected_entry_ids = [u._entry_id for u in users]
    
    s = Session(app, 'pytest')
    with s:
        s.add_all(users)
        s.commit()
        
    # test deletion
    s = Session(app, 'pytest')
    with s:
        s.delete(users[1])
        s.commit()
        
    s = Session(app, 'pytest')
    with s:
        result = User.query(s).all()
        assert len(result) == 1
        assert result[0]._entry_id == users[0]._entry_id
        
def test_session_delete_on_completed(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.delete(user)
        assert 'completed Session' in str(e.value)
        
def test_session_delete_outside_of_with(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    s = Session(app, 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.delete(user)
    assert 'must first be activated' in str(e.value)
    
def test_session_delete_all(app):
    # add data to delete
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    
    s = Session(app, 'pytest')
    with s:
        s.add_all(users)
        s.commit()
        
    # test deletion
    s = Session(app, 'pytest')
    with s:
        s.delete_all(users)
        s.commit()
        
    s = Session(app, 'pytest')
    with s:
        result = User.query(s).all()
        assert len(result) == 0
        
def test_session_delete_all_on_completed(app):
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    
    s = Session(app, 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.delete_all(users)
        assert 'completed Session' in str(e.value)
        
def test_session_add_outside_of_with(app):
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    
    s = Session(app, 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.delete_all(users)
    assert 'must first be activated' in str(e.value)
    
def test_session_flush_simple(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s1 = Session(app, 'pytest')
    
    with s1:
        s1.add(user)
        s1.flush()
        
        result = User.query(s1).get(user._entry_id)
        assert result
        assert result._entry_id == user._entry_id
        
def test_session_flush_on_completed(app):
    s = Session(app, 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.flush()
        assert 'completed Session' in str(e.value)

def test_session_flush_outside_of_with(app):
    s = Session(app, 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.flush()
    assert 'must first be activated' in str(e.value)
    
def test_session_tracking_no_read_own_writes(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        s.commit()
        assert not user._is_active
        
    s = Session(app, 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result._is_active
        assert result.username == 'foo'
        assert result._entry_id == user._entry_id
        
        result.username = 'foo_the_second'
        s.commit()
        assert not result._is_active
        
    s = Session(app, 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result.username == 'foo_the_second'
        assert result._entry_id == user._entry_id
        
def test_session_tracking_read_own_writes(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        
        result = User.query(s).get(user._entry_id)
        assert not user._is_active
        assert result
        assert result._is_active
        assert result.username == 'foo'
        assert result._entry_id == user._entry_id
        
        result.username = 'foo_the_second'
        s.commit()
        assert not result._is_active
        
    s = Session(app, 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result.username == 'foo_the_second'
        assert result._entry_id == user._entry_id
        
def test_session_tracking_change_after_add(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        user.username = 'foo_the_second'
        s.commit()
        assert not user._is_active
        
    s = Session(app, 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result.username == 'foo_the_second'
        assert result._entry_id == user._entry_id
        
def test_session_tracking_change_after_add2(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        user.username = 'foo_the_second'
        
        result = User.query(s).get(user._entry_id)
        assert not user._is_active
        assert result
        assert result._is_active
        assert result.username == 'foo_the_second'
        assert result._entry_id == user._entry_id

def test_session_tracking_newest_version(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        
        result = User.query(s).get(user._entry_id)
        assert not user._is_active
        assert result
        assert result._is_active
        assert result.username == 'foo'
        assert result._entry_id == user._entry_id
        
        # user is no longer the newest version. this assignment should have no effect
        with pytest.raises(AttributeError) as e:
            user.username = 'foo_the_second'
        assert 'no longer mapped' in str(e.value)
        
        result = User.query(s).get(user._entry_id)
        assert result
        assert result.username == 'foo'
        assert result._entry_id == user._entry_id

def test_session_tracking_empty_result(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        
        result = User.query(s).get('this_is_not_a_valid_entry_id')
        assert user._is_active
        assert not result
        
def test_session_invalidation_on_delete(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        s.delete(user)
        assert not user._is_active
        
def test_session_stays_valid_on_flush(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        s.flush()
        assert user._is_active

def test_session_tracking_out_of_session_rollback(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        s.commit()
    
    s = Session(app, 'pytest')
    result = None
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result._is_active

    assert result
    assert not result._is_active

def test_session_tracking_out_of_session_commit(app):
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(app, 'pytest')
    with s:
        s.add(user)
        s.commit()
    
    s = Session(app, 'pytest')
    result = None
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result._is_active
        s.commit()

    assert result
    assert not result._is_active

