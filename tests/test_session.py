import pytest
from polynom.session.session import Session, _SessionState
from polynom.session.initializer import Initializer
from tests.model import User, Bike

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

@pytest.fixture(scope='module', autouse=True)
def setup_module():
    Initializer(APP_UUID, ('localhost', 20590), use_docker=False).run()
    yield
        
@pytest.fixture(autouse=True)
def setup_test():
    yield
    cleanup_session = Session(('localhost', 20590), 'pytest')
    with cleanup_session:
        User.query(cleanup_session).delete()
        cleanup_session.commit()

def test_session_empty_commit():
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.commit()
        
def test_session_empty_rollback():
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.rollback()

def test_session_state_after_initialization():
    s = Session(('localhost', 20590), 'pytest')
    assert s._state == _SessionState.INITIALIZED
        
def test_session_state_after_commit():
    s = Session(('localhost', 20590), 'pytest')
    with s:
        assert s._state == _SessionState.ACTIVE
        s.commit()
        assert s._state == _SessionState.COMPLETED
        
def test_session_state_after_rollback():
    s = Session(('localhost', 20590), 'pytest')
    with s:
        assert s._state == _SessionState.ACTIVE
        s.commit()
        assert s._state == _SessionState.COMPLETED
        
def test_session_add():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add(user)
        s.commit()
        
    s = Session(('localhost', 20590), 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result._entry_id == user._entry_id
        
def test_session_add_on_completed():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.add(user)
        assert 'completed Session' in str(e.value)
        
def test_session_add_outside_of_with():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    s = Session(('localhost', 20590), 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.add(user)
    assert 'must first be activated' in str(e.value)
    
def test_session_add_all():
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    expected_entry_ids = [u._entry_id for u in users]
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add_all(users)
        s.commit()
        
    s = Session(('localhost', 20590), 'pytest')
    with s:
        result = User.query(s).all()
        assert len(result) == 2
        for user in result:
            assert user._entry_id in expected_entry_ids
        
        
def test_session_add_all_on_completed():
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.add_all(users)
        assert 'completed Session' in str(e.value)
        
def test_session_add_all_outside_of_with():
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    s = Session(('localhost', 20590), 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.add_all(users)
    assert 'must first be activated' in str(e.value)
    
    
def test_session_delete():
    # add data to delete
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    expected_entry_ids = [u._entry_id for u in users]
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add_all(users)
        s.commit()
        
    # test deletion
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.delete(users[1])
        s.commit()
        
    s = Session(('localhost', 20590), 'pytest')
    with s:
        result = User.query(s).all()
        assert len(result) == 1
        assert result[0]._entry_id == users[0]._entry_id
        
def test_session_delete_on_completed():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.delete(user)
        assert 'completed Session' in str(e.value)
        
def test_session_delete_outside_of_with():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    s = Session(('localhost', 20590), 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.delete(user)
    assert 'must first be activated' in str(e.value)
    
def test_session_delete_all():
    # add data to delete
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add_all(users)
        s.commit()
        
    # test deletion
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.delete_all(users)
        s.commit()
        
    s = Session(('localhost', 20590), 'pytest')
    with s:
        result = User.query(s).all()
        assert len(result) == 0
        
def test_session_delete_all_on_completed():
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.delete_all(users)
        assert 'completed Session' in str(e.value)
        
def test_session_add_outside_of_with():
    users = [
        User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False),
        User('yami', 'foo@demo.ch', 'yamina', 'muster', True, False)
    ]
    
    s = Session(('localhost', 20590), 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.delete_all(users)
    assert 'must first be activated' in str(e.value)
    
def test_session_flush_simple():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s1 = Session(('localhost', 20590), 'pytest')
    
    with s1:
        s1.add(user)
        s1.flush()
        
        result = User.query(s1).get(user._entry_id)
        assert result
        assert result._entry_id == user._entry_id
        
def test_session_flush_on_completed():
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.commit()
        with pytest.raises(RuntimeError) as e:
            s.flush()
        assert 'completed Session' in str(e.value)

def test_session_flush_outside_of_with():
    s = Session(('localhost', 20590), 'pytest')
    with pytest.raises(RuntimeError) as e:
        s.flush()
    assert 'must first be activated' in str(e.value)
    
def test_session_tracking_no_read_own_writes():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        s.commit()
        assert not user._is_active
        
    s = Session(('localhost', 20590), 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result._is_active
        assert result.username == 'foo'
        assert result._entry_id == user._entry_id
        
        result.username = 'foo_the_second'
        s.commit()
        assert not result._is_active
        
    s = Session(('localhost', 20590), 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result.username == 'foo_the_second'
        assert result._entry_id == user._entry_id
        
def test_session_tracking_read_own_writes():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
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
        
    s = Session(('localhost', 20590), 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result.username == 'foo_the_second'
        assert result._entry_id == user._entry_id
        
def test_session_tracking_change_after_add():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        user.username = 'foo_the_second'
        s.commit()
        assert not user._is_active
        
    s = Session(('localhost', 20590), 'pytest')
    with s:
        result = User.query(s).get(user._entry_id)
        assert result
        assert result.username == 'foo_the_second'
        assert result._entry_id == user._entry_id
        
def test_session_tracking_change_after_add2():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
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

def test_session_tracking_newest_version():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
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

def test_session_tracking_empty_result():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        
        result = User.query(s).get('this_is_not_a_valid_entry_id')
        assert user._is_active
        assert not result
        
def test_session_invalidation_on_delete():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        s.delete(user)
        assert not user._is_active
        
def test_session_stays_valid_on_flush():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    
    s = Session(('localhost', 20590), 'pytest')
    with s:
        s.add(user)
        assert user._is_active
        s.flush()
        assert user._is_active
