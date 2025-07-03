import pytest
from polynom.schema.relationship import Relationship

class User:
    def __init__(self, name):
        self.name = name
        self.bikes = []

class Bike:
    user = Relationship(User, back_populatesf="bikes")

    def __init__(self, brand, model, owner_id):
        self.brand = brand
        self.model = model
        self.owner_id = owner_id

# The actual test class
class TestRelationship:
    def test_relationship_assignment_and_backref(self):
        user = User("Alice")
        bike = Bike("Trek", "X500", owner_id=1)

        assert bike.user is None
        assert user.bikes == []

        bike.user = user
        assert bike.user is user
        assert bike in user.bikes

    def test_relationship_reassignment_updates_backrefs(self):
        user1 = User("Alice")
        user2 = User("Bob")
        bike = Bike("Trek", "X500", owner_id=1)

        bike.user = user1
        assert bike in user1.bikes
        assert bike not in user2.bikes

        bike.user = user2
        assert bike in user2.bikes
        assert bike not in user1.bikes

    def test_relationship_removal(self):
        user = User("Alice")
        bike = Bike("Trek", "X500", owner_id=1)

        bike.user = user
        assert bike in user.bikes

        bike.user = None
        assert bike.user is None
        assert bike not in user.bikes

    def test_invalid_relationship_assignment(self):
        bike = Bike("Trek", "X500", owner_id=1)
        with pytest.raises(TypeError):
            bike.user = "not a user instance"

