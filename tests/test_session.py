import pytest
from polynom.session.session import Session, _SessionState
from polynom.session.initializer import Initializer

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

@pytest.fixture(scope='module', autouse=True)
def initialize_polynom():
    Initializer(APP_UUID, 'localhost', 20590, deploy_on_docker=False).run()
    yield

def test_session_empty_commit():
    s = Session('localhost', 20590, 'pytest')
    with s:
        s.commit()
        
def test_session_empty_rollback():
    s = Session('localhost', 20590, 'pytest')
    with s:
        s.rollback()

def test_session_state_after_initialization():
    s = Session('localhost', 20590, 'pytest')
    assert s._state == _SessionState.INITIALIZED
        
def test_session_state_after_commit():
    s = Session('localhost', 20590, 'pytest')
    with s:
        assert s._state == _SessionState.ACTIVE
        s.commit()
        assert s._state == _SessionState.COMPLETED
        
def test_session_state_after_rollback():
    s = Session('localhost', 20590, 'pytest')
    with s:
        assert s._state == _SessionState.ACTIVE
        s.commit()
        assert s._state == _SessionState.COMPLETED
        

