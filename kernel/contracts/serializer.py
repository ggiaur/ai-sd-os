from pathlib import Path
from typing import Type, TypeVar, Union
import yaml
from pydantic import BaseModel
from kernel.contracts.validator import validate_contract

T = TypeVar("T", bound=BaseModel)

def load_yaml_contract(file_path: Union[str, Path], model_cls: Type[T]) -> T:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return validate_contract(model_cls, data)

def dump_yaml_contract(instance: BaseModel) -> str:
    data = instance.model_dump(mode="json")
    return yaml.dump(data, sort_keys=False, allow_unicode=True)

def save_yaml_contract(instance: BaseModel, file_path: Union[str, Path]) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = dump_yaml_contract(instance)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
