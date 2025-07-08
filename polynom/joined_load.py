from typing import Any, Tuple
from polynom.query import Query

"""
Encapsulates content to eagerly load a relationship 
"""
class JoinedLoad:
    def __init__(self, relationship_attr: Any):
        self.attr = relationship_attr  # e.g. Bike.user

    def apply(self, query: Query):
        related_model = self.attr.get_target_model()
        query.join(related_model)
        alias = f"{related_model.schema.entity_name}_{len(query._joins)}"
        query._eager_loads.append((self.attr._key, related_model, alias))
