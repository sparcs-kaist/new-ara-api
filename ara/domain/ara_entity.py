from typing import Any

from pydantic import BaseModel, PrivateAttr


class NewAraEntity(BaseModel):
    _updated_fields: set[str] = PrivateAttr(set())

    @property
    def updated_fields(self):
        return self._updated_fields

    @property
    def updated_values(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self._updated_fields}

    def set_attribute(self, field_name: str, value: Any):
        self.__dict__[field_name] = value
        is_private_field = field_name.startswith("_") or field_name.startswith("__")
        if is_private_field is False:
            self._updated_fields.add(field_name)

    def __setattr__(self, name: str, value: Any) -> None:
        is_private_field = name.startswith("_") or name.startswith("_")
        if is_private_field is False:
            self._updated_fields.add(name)
        return super().__setattr__(name, value)

    class Config:
        arbitrary_types_allowed = True


class NewAraEntityCreateInput(BaseModel):
    class Config:
        arbitrary_types_allowed = True
