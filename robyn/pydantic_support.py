"""
Optional Pydantic integration for Robyn.

All pydantic imports are lazy: pydantic is only loaded on the first call
to _ensure_pydantic(), so there is zero import-time overhead when pydantic
is not installed or not used.  The module itself is imported at the top
level by router.py and openapi.py, but this is safe because it contains
no pydantic imports at module scope.
"""

import inspect
from typing import Any, Optional, Tuple

import orjson

__all__ = [
    "is_pydantic_available",
    "is_pydantic_model",
    "detect_pydantic_params",
    "validate_pydantic_body",
    "get_pydantic_openapi_schema",
    "serialize_pydantic_response",
    "check_pydantic_installed_for_handler",
    "PydanticBodyValidationError",
    "PydanticNotInstalledError",
    "MultiplePydanticBodyError",
]

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


def detect_pydantic_params(handler_params) -> dict:
    """Scan pre-computed handler parameters for Pydantic BaseModel annotations.

    Accepts the ``parameters`` OrderedDict from ``inspect.signature(handler)``.
    Returns a dict mapping param_name -> model_class for params annotated with
    a Pydantic BaseModel subclass.  Returns empty dict if pydantic is not
    installed or no params use Pydantic models.
    """
    _ensure_pydantic()
    if _BaseModel is None:
        return {}

    result = {}
    for name, param in handler_params.items():
        ann = param.annotation
        if ann is inspect.Parameter.empty:
            continue
        if inspect.isclass(ann) and issubclass(ann, _BaseModel):
            result[name] = ann
    return result


def _sanitize_errors(errors: list) -> list:
    """Make pydantic error dicts JSON-serializable.

    Only copies dicts that actually contain non-serializable values.
    Pydantic v2 error dicts can contain bytes, tuples, and other
    non-JSON-serializable values in 'input', 'loc', and 'ctx' fields.
    """
    sanitized = []
    for err in errors:
        needs_copy = False
        for key, val in err.items():
            if (key == "input" and isinstance(val, bytes)) or key == "loc" or (key == "ctx" and isinstance(val, dict)):
                needs_copy = True
                break

        if not needs_copy:
            sanitized.append(err)
            continue

        clean = dict(err)
        if "input" in clean and isinstance(clean["input"], bytes):
            clean["input"] = clean["input"].decode("utf-8", errors="replace")
        if "loc" in clean:
            clean["loc"] = list(clean["loc"])
        if "ctx" in clean and isinstance(clean["ctx"], dict):
            clean["ctx"] = {k: str(v) for k, v in clean["ctx"].items()}
        sanitized.append(clean)
    return sanitized


def validate_pydantic_body(model_class, body: Any) -> Tuple[Any, Optional[dict]]:
    """Validate request body against a Pydantic model.

    Uses model_validate_json for maximum performance — single-pass
    parse+validate without an intermediate dict.  model_validate_json
    accepts str, bytes, and bytearray natively.

    This function is only called from the request hot path *after*
    _ensure_pydantic() has already been called at registration time,
    so we skip the redundant check here.

    Returns:
        (validated_model_instance, None) on success
        (None, error_detail_dict) on failure
    """
    try:
        return model_class.model_validate_json(body), None
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


def get_pydantic_openapi_schema(model_class) -> Tuple[dict, dict]:
    """Get OpenAPI-compatible JSON Schema from a Pydantic model.

    Uses ref_template so nested model references point to
    #/components/schemas/{ModelName} in the OpenAPI spec.

    Returns:
        (schema, component_schemas) where:
        - schema: the model's JSON Schema (without $defs)
        - component_schemas: dict of model_name -> schema for components/schemas
    """
    _ensure_pydantic()
    if _BaseModel is None or not (inspect.isclass(model_class) and issubclass(model_class, _BaseModel)):
        return {}, {}

    full_schema = model_class.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    component_schemas = full_schema.pop("$defs", {})
    return full_schema, component_schemas


def serialize_pydantic_response(res) -> Optional[str]:
    """Serialize a Pydantic model (or list of models) to a JSON string.

    Returns None when *res* is not a Pydantic type so the caller can fall
    through to other serialisation paths.

    This function is only called from the response hot path *after*
    _ensure_pydantic() has already been called at registration time,
    so we skip the redundant check here.
    """
    if _BaseModel is None:
        return None
    if isinstance(res, _BaseModel):
        return res.model_dump_json()
    if isinstance(res, list) and res and isinstance(res[0], _BaseModel):
        return orjson.dumps(
            [item.model_dump(mode="python") for item in res]
        ).decode("utf-8")
    return None


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
            f'Install it with: pip install "robyn[pydantic]" or pip install "robyn[all]"'
        )


class MultiplePydanticBodyError(TypeError):
    """Raised at route registration when a handler declares more than one
    Pydantic body parameter."""

    def __init__(self, handler_name: str, param_names: list):
        super().__init__(
            f"Handler '{handler_name}' has multiple Pydantic body parameters "
            f"{param_names}. Only one Pydantic body parameter per handler is "
            f"supported — the entire request body is parsed into that single model."
        )


def check_pydantic_installed_for_handler(handler, pydantic_params: dict):
    """Validate Pydantic usage at startup.

    Raises PydanticNotInstalledError if pydantic isn't available.
    Raises MultiplePydanticBodyError if more than one body param is declared.
    """
    if not pydantic_params:
        return
    if not is_pydantic_available():
        first_param = next(iter(pydantic_params))
        model = pydantic_params[first_param]
        raise PydanticNotInstalledError(handler.__name__, first_param, model.__name__)
    if len(pydantic_params) > 1:
        raise MultiplePydanticBodyError(handler.__name__, list(pydantic_params.keys()))
