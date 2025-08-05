
import logging
from polynom.model.model import BaseModel

logger = logging.getLogger(__name__)

_registered_models_by_fqname = {}

def polynom_model(cls):
    if not issubclass(cls, BaseModel):
        raise TypeError(f"@polynom_model can only be applied to subclasses of BaseModel, got {cls}")

    fq_name = f"{cls.__module__}.{cls.__name__}"
    if fq_name in _registered_models_by_fqname:
        logger.warning(f"Model '{fq_name}' is already registered. Overwriting the existing entry.")
    else:
        logger.debug(f"Registering model '{fq_name}'")
    
    _registered_models_by_fqname[fq_name] = cls
    return cls

def _get_model_by_fqname(fq_name: str) -> type[BaseModel] | None:
    return _registered_models_by_fqname.get(fq_name)

def _get_registered_models() -> dict[str, type[BaseModel]]:
    return dict(_registered_models_by_fqname)
