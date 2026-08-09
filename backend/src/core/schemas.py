from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    """
    Base model that automatically converts Python snake_case 
    to JSON camelCase during serialization.
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )