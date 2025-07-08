import pytest
from polynom.session import Session, _SessionState
from polynom.query import Query
from tests.model import User, Bike

def test_model_init_has_entry_id():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    assert user._entry_id
    
def test_model_init_has_unique_entry_id():
    user1 = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    user2 = User('mir', 'mir.s@demo.ch', 'miriam', 'schnyder', True, False)
    assert user1._entry_id
    assert user2._entry_id
    assert not user1._entry_id == user2._entry_id
    
def test_model_init_allows_duplication():
    user1 = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    user2 = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    assert user1._entry_id
    assert user2._entry_id
    assert not user1._entry_id == user2._entry_id
    
def test_model_init_is_active():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    assert user._is_active

def test_model_init_has_snapshot():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    assert user._snapshot
    
def test_model_init_diff():
    expected = {
        'active': (None, True),
        'email': (None, 'foo@demo.ch'),
        'first_name': (None, 'flo'),
        'last_name': (None, 'brugger'),
        'username': (None, 'foo'),
        'is_admin': (None, False)
    }
    
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    diff = user._diff()
    
    assert diff
    assert diff.keys() == expected.keys()
    for key in expected.keys():
        assert diff[key] == expected[key]

    
def test_model_snapshot_no_update():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    user._update_snapshot()
    diff = user._diff()
    assert not diff
    
def test_model_diff_update1():
    expected = {
        'active': (None, True),
        'email': (None, 'foo@demo.ch'),
        'first_name': (None, 'flo'),
        'last_name': (None, 'brugger'),
        'username': (None, 'new_foo'),
        'is_admin': (None, False)
    }
    
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    user.username = 'new_foo'
    diff = user._diff()
    assert 'username' in diff
    old, new = diff['username']
    assert old == None
    assert new == 'new_foo'
    
def test_model_diff_update2():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    user._update_snapshot()
    user.username = 'new_foo'
    diff = user._diff()
    assert 'username' in diff
    old, new = diff['username']
    assert old == 'foo'
    assert new == 'new_foo'
    
def test_model_diff_identity_update():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    user._update_snapshot()
    user.username = 'foo'
    diff = user._diff()
    assert not diff

def test_model_diff_reverted_update():
    user = User('foo', 'foo@demo.ch', 'flo', 'brugger', True, False)
    user._update_snapshot()
    user.username = 'new_foo'
    user.username = 'foo'
    diff = user._diff()
    assert not diff

