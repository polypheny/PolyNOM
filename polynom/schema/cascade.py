
class Cascade:
    def __init__(self):
        self._original_relations = {}

    def track_initial_state(self):
        for attr, value in self.__dict__.items():
            if isinstance(value, list):
                self._original_relations[attr] = list(value)
            else:
                self._original_relations[attr] = value

    def detect_orphans(self):
        orphans = []
        for attr, old_value in self._original_relations.items():
            current_value = getattr(self, attr, None)
            if isinstance(old_value, list) and isinstance(current_value, list):
                orphans.extend([x for x in old_value if x not in current_value])
        return orphans