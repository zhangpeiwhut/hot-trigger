from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, get_args, get_origin, get_type_hints


class ValidationError(ValueError):
    pass


@dataclass
class _FieldInfo:
    default: Any = None
    default_factory: Any = None


def Field(*, default: Any = None, default_factory: Any = None):
    return _FieldInfo(default=default, default_factory=default_factory)


class BaseModel:
    def __init__(self, **kwargs):
        hints = get_type_hints(self.__class__)
        for name, ann in hints.items():
            if name in kwargs:
                value = kwargs[name]
            else:
                default = getattr(self.__class__, name, None)
                if isinstance(default, _FieldInfo):
                    if default.default_factory is not None:
                        value = default.default_factory()
                    else:
                        value = default.default
                else:
                    value = default
            setattr(self, name, self._convert_value(ann, value))

    @classmethod
    def model_validate(cls, data: dict[str, Any]):
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict for {cls.__name__}")
        return cls(**data)

    def model_dump(self, mode: str | None = None):
        result = {}
        hints = get_type_hints(self.__class__)
        for name in hints:
            value = getattr(self, name)
            result[name] = self._serialize(value, mode=mode)
        return result

    @classmethod
    def _convert_value(cls, ann, value):
        if value is None:
            return None
        origin = get_origin(ann)
        args = get_args(ann)

        if isinstance(ann, type) and issubclass(ann, BaseModel):
            return ann.model_validate(value) if isinstance(value, dict) else value
        if origin is list and args:
            return [cls._convert_value(args[0], item) for item in value]
        if origin is dict:
            return dict(value)
        if origin is not None and type(None) in args:
            target = next((a for a in args if a is not type(None)), Any)
            return cls._convert_value(target, value)
        if ann is datetime and isinstance(value, str):
            return datetime.fromisoformat(value)
        return value

    @classmethod
    def _serialize(cls, value, mode: str | None = None):
        if isinstance(value, BaseModel):
            return value.model_dump(mode=mode)
        if isinstance(value, list):
            return [cls._serialize(v, mode=mode) for v in value]
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime) and mode == "json":
            return value.isoformat()
        return value
