"""
Optional Pydantic integration for Robyn.

This module is never imported at the top level of any Robyn module.
It is only loaded when a handler's type annotations reference a Pydantic BaseModel.
When pydantic is not installed, the detection functions return False and
the validation functions are never called.
"""

import inspect
from typing import Any, Optional, Tuple

_BaseModel = None
_ValidationError = None
_pydantic_checked = False


def _ensure_pydantic():
    """Lazy-load pydantic classes. Called at most once."""
    global _BaseModel, _ValidationError, _pydantic_checked
    if _pydantic_checked:
        return
    _pydantic_checked = True
    try:
        from pydantic import BaseModel, ValidationError

        _BaseModel = BaseModel
        _ValidationError = ValidationError
    except ImportError:
        _BaseModel = None
        _ValidationError = None


def is_pydantic_available() -> bool:
    _ensure_pydantic()
    return _BaseModel is not None


def is_pydantic_model(annotation) -> bool:
    """Check if an annotation is a pydantic BaseModel subclass.
    Returns False if pydantic is not installed or annotation is not a class."""
    _ensure_pydantic()
    if _BaseModel is None:
        return False
    return inspect.isclass(annotation) and issubclass(annotation, _BaseModel)


def detect_pydantic_params(handler) -> dict:
    """Inspect a handler's signature at registration time.
    Returns a dict mapping param_name -> model_class for params annotated with
    a Pydantic BaseModel subclass. Returns empty dict if pydantic is not installed
    or no params use Pydantic models."""
    _ensure_pydantic()
    if _BaseModel is None:
        return {}

    result = {}
    for name, param in inspect.signature(handler).parameters.items():
        ann = param.annotation
        if ann is inspect.Parameter.empty:
            continue
        if inspect.isclass(ann) and issubclass(ann, _BaseModel):
            result[name] = ann
    return result


def _sanitize_errors(errors: list) -> list:
    """Make pydantic error dicts JSON-serializable.
    Pydantic v2 error dicts can contain bytes, tuples, and other
    non-JSON-serializable values in 'input', 'loc', and 'ctx' fields."""
    sanitized = []
    for err in errors:
        clean = {}
        for key, val in err.items():
            if key == "input" and isinstance(val, bytes):
                clean[key] = val.decode("utf-8", errors="replace")
            elif key == "loc":
                clean[key] = list(val)
            elif key == "ctx" and isinstance(val, dict):
                clean[key] = {k: str(v) for k, v in val.items()}
            else:
                clean[key] = val
        sanitized.append(clean)
    return sanitized


def validate_pydantic_body(model_class, body: Any) -> Tuple[Any, Optional[dict]]:
    """Validate request body against a Pydantic model.

    Uses model_validate_json when possible (bytes/str input) for maximum
    performance — single-pass parse+validate without an intermediate dict.

    Returns:
        (validated_model_instance, None) on success
        (None, error_detail_dict) on failure
    """
    _ensure_pydantic()
    try:
        if isinstance(body, (bytes, str)):
            if isinstance(body, str):
                body = body.encode("utf-8")
            return model_class.model_validate_json(body), None
        elif isinstance(body, dict):
            return model_class.model_validate(body), None
        else:
            raw = bytes(body) if not isinstance(body, (bytes, str)) else body
            return model_class.model_validate_json(raw), None
    except _ValidationError as e:
        return None, {
            "detail": _sanitize_errors(e.errors()),
            "error": "Validation Error",
        }
    except Exception as e:
        return None, {
            "detail": str(e),
            "error": "Invalid request body",
        }


class PydanticBodyValidationError(Exception):
    """Raised at request time when Pydantic body validation fails.
    Carries the serializable error dict for the 422 response."""

    def __init__(self, error_detail: dict):
        self.error_detail = error_detail
        super().__init__(error_detail.get("error", "Validation Error"))


class PydanticNotInstalledError(ImportError):
    """Raised at route registration when a handler uses a Pydantic model
    but pydantic is not installed."""

    def __init__(self, handler_name: str, param_name: str, model_name: str):
        super().__init__(
            f"Handler '{handler_name}' has parameter '{param_name}' annotated with "
            f"Pydantic model '{model_name}', but pydantic is not installed. "
            f"Install it with: pip install robyn[pydantic]"
        )


def check_pydantic_installed_for_handler(handler, pydantic_params: dict):
    """Raise a clear error at startup if a handler uses Pydantic models
    but pydantic is not installed."""
    if not pydantic_params:
        return
    if is_pydantic_available():
        return
    first_param = next(iter(pydantic_params))
    model = pydantic_params[first_param]
    raise PydanticNotInstalledError(handler.__name__, first_param, model.__name__)
