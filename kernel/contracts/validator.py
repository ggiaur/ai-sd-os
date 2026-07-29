from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

class ContractValidationError(Exception):
    def __init__(self, contract_name: str, errors: ValidationError):
        super().__init__(f"Validation failed for contract {contract_name}: {errors}")
        self.contract_name = contract_name
        self.raw_errors = errors

def validate_contract(model_cls: Type[T], data: dict) -> T:
    try:
        return model_cls.model_validate(data)
    except ValidationError as e:
        raise ContractValidationError(model_cls.__name__, e)
