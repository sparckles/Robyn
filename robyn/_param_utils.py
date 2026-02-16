"""
Shared utilities for resolving individual query/path parameters
from handler function signatures, with type coercion.

Used by both robyn/router.py (HTTP handlers) and robyn/ws.py (WebSocket handlers).
"""

import inspect
import logging
from typing import Any, Dict, Optional, Set, Tuple, Union

_logger = logging.getLogger(__name__)

_MISSING = object()

# Values that map to True/False from query string bool params
_BOOL_TRUE_STRINGS = frozenset({"true", "1", "yes", "on"})
_BOOL_FALSE_STRINGS = frozenset({"false", "0", "no", "off", ""})


class QueryParamValidationError(Exception):
    """Raised when a query or path parameter cannot be coerced to the expected type,
    or when a required parameter is missing."""

    def __init__(self, param_name: str, value: Optional[str], expected_type: type, message: Optional[str] = None):
        self.param_name = param_name
        self.value = value
        self.expected_type = expected_type
        if message:
            self.detail = message
        elif value is None:
            self.detail = f"Missing required parameter: '{param_name}'"
        else:
            self.detail = f"Invalid value '{value}' for parameter '{param_name}': expected {expected_type.__name__}"
        super().__init__(self.detail)


def unwrap_optional(annotation) -> Tuple[Any, bool]:
    """
    If annotation is Optional[T] (i.e. Union[T, None]), return (T, True).
    Otherwise return (annotation, False).
    """
    origin = getattr(annotation, "__origin__", None)
    if origin is Union:
        args = annotation.__args__
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1 and type(None) in args:
            return non_none_args[0], True
    return annotation, False


def is_list_type(annotation) -> bool:
    """Check if annotation is List[T] or list[T]."""
    origin = getattr(annotation, "__origin__", None)
    return origin is list


def get_list_element_type(annotation) -> type:
    """Get the element type from List[T]. Defaults to str if not specified."""
    args = getattr(annotation, "__args__", None)
    if args and len(args) > 0:
        return args[0]
    return str


def coerce_value(value: str, target_type: type, param_name: str):
    """
    Convert a string value to the target type.
    Raises QueryParamValidationError on failure.
    """
    if target_type is str or target_type is inspect.Parameter.empty:
        return value

    try:
        if target_type is int:
            return int(value)
        if target_type is float:
            return float(value)
        if target_type is bool:
            lower = value.lower()
            if lower in _BOOL_TRUE_STRINGS:
                return True
            if lower in _BOOL_FALSE_STRINGS:
                return False
            raise ValueError(f"Cannot interpret '{value}' as bool")
        # Fallback: try calling the type constructor (covers Enum, UUID, etc.)
        return target_type(value)
    except (ValueError, TypeError) as e:
        raise QueryParamValidationError(param_name, value, target_type) from e


def resolve_individual_params(
    unresolved_params: Dict[str, inspect.Parameter],
    query_params,
    path_params: Optional[Dict[str, str]],
    route_param_names: Set[str],
) -> Dict[str, Any]:
    """
    Resolve handler parameters as individual path or query parameters.

    For each unresolved parameter:
      1. If its name matches a route param name (from the endpoint pattern), look it up in path_params.
      2. Otherwise, look it up in query_params.
      3. Apply type coercion based on the parameter's annotation.
      4. Fall back to the parameter's default value, or None for Optional types.
      5. Raise QueryParamValidationError if a required parameter is missing.

    Args:
        unresolved_params: dict of param_name -> inspect.Parameter for params not yet resolved.
        query_params: QueryParams object with .get() and .get_all() methods.
        path_params: dict of path parameter values (may be None for WebSocket).
        route_param_names: set of parameter names declared in the route pattern (e.g. from /:id).

    Returns:
        dict mapping param names to their resolved values.
    """
    resolved = {}

    for param_name, param in unresolved_params.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            annotation = str

        inner_type, is_optional = unwrap_optional(annotation)
        is_list = is_list_type(inner_type)

        raw_value = _MISSING

        # 1. Check path params first
        if path_params is not None and param_name in route_param_names:
            pv = path_params.get(param_name)
            if pv is not None:
                raw_value = pv

        # 2. Check query params
        if raw_value is _MISSING and query_params is not None:
            if is_list:
                all_values = query_params.get_all(param_name)
                if all_values is not None:
                    elem_type = get_list_element_type(inner_type)
                    resolved[param_name] = [coerce_value(v, elem_type, param_name) for v in all_values]
                    continue
            else:
                qp_value = query_params.get(param_name, None)
                if qp_value is not None:
                    raw_value = qp_value

        # 3. Got a value — coerce it
        if raw_value is not _MISSING:
            resolved[param_name] = coerce_value(raw_value, inner_type, param_name)
            continue

        # 4. Use default value if available
        if param.default is not inspect.Parameter.empty:
            resolved[param_name] = param.default
            continue

        # 5. Optional with no default -> None
        if is_optional:
            resolved[param_name] = None
            continue

        # 6. Truly missing required parameter
        raise QueryParamValidationError(param_name, None, inner_type)

    return resolved


def parse_route_param_names(endpoint: str) -> Set[str]:
    """
    Extract parameter names from a route endpoint pattern.
    e.g. "/users/:id/posts/:post_id" -> {"id", "post_id"}

    Walks the string character by character looking for ':' followed by
    word characters (alphanumeric + underscore).
    """
    names = set()
    i = 0
    length = len(endpoint)
    while i < length:
        if endpoint[i] == ":":
            # Start of a param name — collect word characters
            i += 1
            start = i
            while i < length and (endpoint[i].isalnum() or endpoint[i] == "_"):
                i += 1
            if i > start:
                names.add(endpoint[start:i])
        else:
            i += 1
    return names
