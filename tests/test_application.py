import pytest
from polynom.session import Session
from tests.model import User, Bike

pytestmark = pytest.mark.integration

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
        Bike.query(cleanup_session).delete()
        User.query(cleanup_session).delete()
        cleanup_session.commit()

def test_dump(setup_test, tmp_path):
    users, bikes, app = setup_test

    with Session(app, 'test') as session:
        result = User.query(session).all()
        expected_entry_ids = [u._entry_id for u in users]
    
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids

        result = Bike.query(session).all()
        expected_entry_ids = [b._entry_id for b in bikes]
        
        assert len(result) == len(bikes)
        for user in result:
            assert user._entry_id in expected_entry_ids
        
    file = tmp_path / 'test_dump.sql'
    app.dump(file)
    app.load(file)

    with Session(app, 'test') as session:
        result = User.query(session).all()
        expected_entry_ids = [u._entry_id for u in users]
        
        assert len(result) == len(users)
        for user in result:
            assert user._entry_id in expected_entry_ids

        result = Bike.query(session).all()
        expected_entry_ids = [b._entry_id for b in bikes]
        
        assert len(result) == len(bikes)
        for user in result:
            assert user._entry_id in expected_entry_ids

