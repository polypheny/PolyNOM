import pytest
from polynom.model.relationship import Relationship
from polynom.model.model import BaseModel
from polynom.model.model_registry import polynom_model

@polynom_model
class Cyclist(BaseModel):
    def __init__(self, name):
        self.name = name
        self.bikes = []
        self.teams = []
        self.primary_sponsor = None

class RoadBike:
    owner: Cyclist = Relationship(Cyclist, back_populates="bikes")

    def __init__(self, brand, model):
        self.brand = brand
        self.model = model


class Team:
    member: Cyclist = Relationship("tests.test_relationship.Cyclist", back_populates="teams")

    def __init__(self, name):
        self.name = name

class Sponsor:
    cyclist: Cyclist = Relationship("tests.test_relationship.Cyclist")

    def __init__(self, name):
        self.name = name


class TestRelationship:
    def test_bike_assignment_and_backref(self):
        """
        RoadBike assigned to Cyclist updates both forward and back references.
        """
        rider = Cyclist("Tadej Pogačar")
        bike = RoadBike("Colnago", "V4Rs")

        assert bike.owner is None
        assert rider.bikes == []

        bike.owner = rider

        assert bike.owner is rider
        assert bike in rider.bikes

    def test_bike_reassignment_removes_old_backref(self):
        """
        When a bike is reassigned to another Cyclist, the old backref is removed.
        """
        rider1 = Cyclist("Jonas Vingegaard")
        rider2 = Cyclist("Remco Evenepoel")
        bike = RoadBike("Cervélo", "R5")

        bike.owner = rider1
        assert bike in rider1.bikes

        bike.owner = rider2
        assert bike in rider2.bikes
        assert bike not in rider1.bikes

    def test_team_bidirectional_membership(self):
        """
        Cyclist assigned to Team updates both team.member and cyclist.teams list.
        """
        cyclist = Cyclist("Primož Roglič")
        team = Team("BORA-hansgrohe")

        assert team.member is None
        assert cyclist.teams == []

        team.member = cyclist

        assert team.member is cyclist
        assert team in cyclist.teams

    def test_team_reassignment(self):
        """
        Team reassigned to a different Cyclist updates membership cleanly.
        """
        rider1 = Cyclist("Geraint Thomas")
        rider2 = Cyclist("Tom Pidcock")
        team = Team("INEOS Grenadiers")

        team.member = rider1
        assert team in rider1.teams

        team.member = rider2
        assert team in rider2.teams
        assert team not in rider1.teams

    def test_unidirectional_sponsorship(self):
        """
        Sponsor assigned to Cyclist (without back_populates) does not update cyclist.
        """
        cyclist = Cyclist("Mathieu van der Poel")
        sponsor = Sponsor("Alpecin-Deceuninck")

        assert sponsor.cyclist is None

        sponsor.cyclist = cyclist
        assert sponsor.cyclist is cyclist

        # No reverse relationship defined
        assert cyclist.primary_sponsor is None

    def test_null_assignment_removes_bike_backref(self):
        """
        Setting bike.owner to None removes it from cyclist.bikes.
        """
        cyclist = Cyclist("Wout van Aert")
        bike = RoadBike("Canyon", "Aeroad")

        bike.owner = cyclist
        assert bike in cyclist.bikes

        bike.owner = None
        assert bike.owner is None
        assert bike not in cyclist.bikes

    def test_invalid_relationship_type_raises(self):
        """
        Assigning the wrong type to a relationship should raise TypeError.
        """
        bike = RoadBike("Specialized", "Tarmac")
        with pytest.raises(TypeError):
            bike.owner = "NotACyclist"

    def test_relationship_type_check_fails_for_wrong_class(self):
        """
        Relationship should raise TypeError if the assigned value is not of the correct type.
        """
        class NotACyclist:
            def __init__(self, name):
                self.name = name

        outsider = NotACyclist("Random Person")
        team = Team("Team Jumbo-Visma")

        with pytest.raises(TypeError):
            team.member = outsider

    def test_multiple_bikes_same_cyclist(self):
        """
        One cyclist can have multiple bikes (many-to-one relationship).
        """
        cyclist = Cyclist("Filippo Ganna")
        bike1 = RoadBike("Pinarello", "Dogma F")
        bike2 = RoadBike("Pinarello", "Bolide TT")

        bike1.owner = cyclist
        bike2.owner = cyclist

        assert bike1.owner is cyclist
        assert bike2.owner is cyclist
        assert bike1 in cyclist.bikes
        assert bike2 in cyclist.bikes
    
    def test_relationship_create_backref_if_attribute_missing(self):
        """
        If the target object lacks the back_populates attribute, Relationship should raise an AttributeError.
        """
        cyclist = Cyclist("Mark Cavendish")
        del cyclist.teams  # Simulate missing backref attribute

        team = Team("Astana Qazaqstan")

        with pytest.raises(AttributeError, match="Backref attribute 'teams' not found on Cyclist"):
            team.member = cyclist

