class Relationship:
    def __init__(self, target_model: type["BaseModel"] = None, back_populates: str = None, cascade: str = None):
        self.target_model = target_model
        self._back_populates = back_populates
        self._internal_name = None
        self._cascade = cascade or ""
        self._owner_class = None
        self._key = None

    def __set_name__(self, owner, name):
        self._internal_name = f'_{name}'
        self._key = name
        self._owner_class = owner

    def __set__(self, instance, value):
        if value and not isinstance(value, self.target_model):
            raise TypeError(f'Value must be of {type[self.target_model]} but is of {type[value]}')
        old_value = getattr(instance, self._internal_name, None)
        if old_value is value:
            return

        # Remove old backref
        if old_value and self._back_populates:
            current_back = getattr(old_value, self._back_populates, None)
            if isinstance(current_back, list):
                if instance in current_back:
                    current_back.remove(instance)
            elif current_back is instance:
                setattr(old_value, self._back_populates, None)

            if "delete-orphan" in self._cascade and hasattr(instance, '_session') and instance._session:
                instance._session.delete(old_value)

        # Set new value
        setattr(instance, self._internal_name, value)

        # Set new backref
        if value and self._back_populates:
            if not hasattr(value, self._back_populates):
                raise AttributeError(
                f"Backref attribute '{self._back_populates}' not found on {value.__class__.__name__}"
            )
            current_back = getattr(value, self._back_populates, None)
            if isinstance(current_back, list):
                if instance not in current_back:
                    current_back.append(instance)
            elif current_back is not instance:
                setattr(value, self._back_populates, instance)

            if any(c in self._cascade for c in ("save-update", "all")):
                if hasattr(instance, "_session") and instance._session:
                    instance._session.add(value)

    def get_target_model(self):
        if not self._back_populates or not self._owner_class:
            raise ValueError("Cannot infer target_model without 'back_populates' and 'owner_class' set")

        from polynom.model import BaseModel
        for model_cls in BaseModel.__subclasses__():
            for attr_name, attr in vars(model_cls).items():
                if isinstance(attr, Relationship):
                    if attr._back_populates == self._key:
                        return model_cls

        raise ValueError(f"Could not infer target_model for relationship '{self._key}'")

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._internal_name, None)

