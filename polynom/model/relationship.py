from polynom.model.model_registry import _get_model_by_fqname

class Relationship:
    def __init__(self, target_model: type["BaseModel"] | str, back_populates: str = None, cascade: str = None):
        if target_model is None:
            raise ValueError("target_model must be specified for Relationship")
        self._target_model = target_model
        self._back_populates = back_populates
        self._internal_name = None
        self._cascade = cascade or ""
        self._owner_class = None
        self._key = None

    def __set_name__(self, owner, name):
        self._internal_name = f'_{name}'
        self._key = name
        self._owner_class = owner

    @property
    def target_model(self):
        # Resolve string to actual model class once
        if isinstance(self._target_model, str):
            model_cls = _get_model_by_fqname(self._target_model)
            if model_cls is None:
                raise ValueError(f"Model '{self._target_model}' not found in registry for relationship '{self._key}'")
            self._target_model = model_cls
        return self._target_model

    def __set__(self, instance, value):
        tm = self.target_model  # resolve first

        if value and not isinstance(value, tm):
            raise TypeError(f'Value must be of {tm} but is of {type(value)}')
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

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._internal_name, None)
