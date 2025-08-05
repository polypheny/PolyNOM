from collections import defaultdict, deque
from polynom.schema.field import ForeignKeyField
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

_registered_schemas = set()
_sorted_schemas = None

def polynom_schema(cls):
    logger.debug(f'Schema registered: {str(cls)}')
    _registered_schemas.add(cls)
    return cls
    
def _get_ordered_schemas():
    global _sorted_schemas
    if _sorted_schemas:
        return _sorted_schemas
    _sorted_schemas = _sort_by_foreign_key(_registered_schemas)
    return _sorted_schemas
        
def _sort_by_foreign_key(schemas):
    schemas_by_name = {s.entity_name: s for s in schemas}
    dependencys = defaultdict(set)
    reverse_deps = defaultdict(set)
    for current_schema in schemas:
        name = current_schema.entity_name
        for f in current_schema.fields:
            if isinstance(f, ForeignKeyField):
                if f.referenced_entity_name not in schemas_by_name:
                    raise RuntimeError(
                        f"Referenced schema '{f.referenced_entity_name}'"
                        f"not found among input schemas"
                    )
                dependencys[name].add(f.referenced_entity_name)
                reverse_deps[f.referenced_entity_name].add(name)

    q = deque(name for name in schemas_by_name if not dependencys[name])
    ordered_names = []
    while q:
        table = q.popleft()
        ordered_names.append(table)
        for child in reverse_deps[table]:
            dependencys[child].remove(table)
            if not dependencys[child]:
                q.append(child)
                
    if len(ordered_names) != len(schemas_by_name):
        raise RuntimeError("Circular FK dependency")
    return [schemas_by_name[name] for name in ordered_names]
    
def _to_dict():
    return {
        "version": datetime.now().strftime("%Y%m%dT%H%M%S"),
        "schemas": [schema._to_dict() for schema in _get_ordered_schemas()]
    }
