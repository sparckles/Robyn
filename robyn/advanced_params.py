import inspect
import json
from typing import Any, Dict, List, Optional, Union, get_type_hints, get_origin, get_args
from pydantic import BaseModel, ValidationError, create_model

from robyn.robyn import Request, QueryParams, Headers
from robyn.types import PathParams, Body


class Query:
    def __init__(self, default: Any = ..., description: str = None, alias: str = None, **extra):
        self.default = default
        self.description = description
        self.alias = alias
        self.extra = extra


class Path:
    def __init__(self, default: Any = ..., description: str = None, **extra):
        self.default = default
        self.description = description
        self.extra = extra


class Header:
    def __init__(self, default: Any = ..., description: str = None, alias: str = None, convert_underscores: bool = True, **extra):
        self.default = default
        self.description = description
        self.alias = alias
        self.convert_underscores = convert_underscores
        self.extra = extra


class Form:
    def __init__(self, default: Any = ..., description: str = None, alias: str = None, **extra):
        self.default = default
        self.description = description
        self.alias = alias
        self.extra = extra


def _extract_parameter_info(param: inspect.Parameter) -> Dict[str, Any]:
    """Extract parameter information including type annotations and advanced parameter metadata."""
    param_info = {
        'name': param.name,
        'annotation': param.annotation,
        'default': param.default,
        'kind': param.kind,
        'advanced_param': None,
        'is_required': param.default is param.empty
    }
    
    # Check if the default value is an advanced parameter (Query, Path, etc.)
    if isinstance(param.default, (Query, Path, Header, Form)):
        param_info['advanced_param'] = param.default
        param_info['is_required'] = param.default.default is ...
    
    return param_info


def _parse_query_params(query_params: QueryParams, param_info: Dict[str, Any]) -> Any:
    """Parse query parameters with advanced Query objects."""
    param_name = param_info['name']
    advanced_param = param_info['advanced_param']
    annotation = param_info['annotation']
    
    # Determine the key to look for in query params
    key = advanced_param.alias if advanced_param and advanced_param.alias else param_name
    
    # Get the value from query parameters
    value = query_params.get(key)
    
    # Handle missing required parameters
    if value is None:
        if param_info['is_required']:
            raise ValueError(f"Required query parameter '{key}' is missing")
        elif advanced_param and advanced_param.default is not ...:
            return advanced_param.default
        elif param_info['default'] is not param_info['default'].__class__.empty:
            return param_info['default']
        return None
    
    # Type conversion based on annotation
    if annotation and annotation != inspect.Parameter.empty:
        origin = get_origin(annotation)
        args = get_args(annotation)
        
        # Handle Optional types
        if origin is Union and len(args) == 2 and type(None) in args:
            target_type = args[0] if args[1] is type(None) else args[1]
        else:
            target_type = annotation
        
        # Handle List types
        if origin is list or (hasattr(annotation, '__origin__') and annotation.__origin__ is list):
            item_type = args[0] if args else str
            if isinstance(value, list):
                return [_convert_type(v, item_type) for v in value]
            else:
                return [_convert_type(value, item_type)]
        
        # Single value conversion
        return _convert_type(value, target_type)
    
    return value


def _parse_path_params(path_params: PathParams, param_info: Dict[str, Any]) -> Any:
    """Parse path parameters with advanced Path objects."""
    param_name = param_info['name']
    advanced_param = param_info['advanced_param']
    annotation = param_info['annotation']
    
    # Get the value from path parameters
    value = path_params.get(param_name)
    
    # Handle missing required parameters
    if value is None:
        if param_info['is_required']:
            raise ValueError(f"Required path parameter '{param_name}' is missing")
        elif advanced_param and advanced_param.default is not ...:
            return advanced_param.default
        return None
    
    # Type conversion based on annotation
    if annotation and annotation != inspect.Parameter.empty:
        origin = get_origin(annotation)
        args = get_args(annotation)
        
        # Handle Optional types
        if origin is Union and len(args) == 2 and type(None) in args:
            target_type = args[0] if args[1] is type(None) else args[1]
        else:
            target_type = annotation
        
        return _convert_type(value, target_type)
    
    return value


def _parse_headers(headers: Headers, param_info: Dict[str, Any]) -> Any:
    """Parse headers with advanced Header objects."""
    param_name = param_info['name']
    advanced_param = param_info['advanced_param']
    annotation = param_info['annotation']
    
    # Determine the key to look for in headers
    key = param_name
    if advanced_param:
        if advanced_param.alias:
            key = advanced_param.alias
        elif advanced_param.convert_underscores:
            key = param_name.replace('_', '-')
    
    # Get the value from headers
    value = headers.get(key)
    
    # Handle missing required parameters
    if value is None:
        if param_info['is_required']:
            raise ValueError(f"Required header '{key}' is missing")
        elif advanced_param and advanced_param.default is not ...:
            return advanced_param.default
        elif param_info['default'] is not param_info['default'].__class__.empty:
            return param_info['default']
        return None
    
    # Type conversion based on annotation
    if annotation and annotation != inspect.Parameter.empty:
        origin = get_origin(annotation)
        args = get_args(annotation)
        
        # Handle Optional types
        if origin is Union and len(args) == 2 and type(None) in args:
            target_type = args[0] if args[1] is type(None) else args[1]
        else:
            target_type = annotation
        
        return _convert_type(value, target_type)
    
    return value


def _parse_body(body: Body, param_info: Dict[str, Any]) -> Any:
    """Parse request body with Pydantic model validation."""
    annotation = param_info['annotation']
    
    # If annotation is a Pydantic model, validate the body
    if annotation and annotation != inspect.Parameter.empty:
        if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
            try:
                # Try to parse as JSON
                if isinstance(body, (bytes, str)):
                    body_data = json.loads(body) if isinstance(body, (bytes, str)) else body
                else:
                    body_data = body
                return annotation(**body_data)
            except (json.JSONDecodeError, ValidationError) as e:
                raise ValueError(f"Invalid request body: {e}")
    
    return body


def _convert_type(value: Any, target_type: type) -> Any:
    """Convert value to target type."""
    if target_type is str:
        return str(value)
    elif target_type is int:
        return int(value)
    elif target_type is float:
        return float(value)
    elif target_type is bool:
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    else:
        return value


def parse_advanced_params(handler: callable, request: Request) -> Dict[str, Any]:
    """
    Parse advanced-style parameters from a request.
    
    Supports:
    - Query parameters with Query()
    - Path parameters with Path() 
    - Headers with Header()
    - Request body with Pydantic models
    - Type annotations and validation
    """
    signature = inspect.signature(handler)
    parsed_params = {}
    
    for param_name, param in signature.parameters.items():
        param_info = _extract_parameter_info(param)
        
        # Skip request parameter itself
        if param_info['annotation'] is Request:
            parsed_params[param_name] = request
            continue
        
        # Handle different parameter types
        try:
            if isinstance(param_info['advanced_param'], Query):
                parsed_params[param_name] = _parse_query_params(request.query_params, param_info)
            elif isinstance(param_info['advanced_param'], Path):
                parsed_params[param_name] = _parse_path_params(request.path_params, param_info)
            elif isinstance(param_info['advanced_param'], Header):
                parsed_params[param_name] = _parse_headers(request.headers, param_info)
            elif isinstance(param_info['advanced_param'], Form):
                # Handle form data - similar to Query for now
                parsed_params[param_name] = _parse_query_params(request.query_params, param_info)
            else:
                # Check annotation for Pydantic models (body parsing)
                if (param_info['annotation'] and 
                    param_info['annotation'] != inspect.Parameter.empty and 
                    inspect.isclass(param_info['annotation']) and 
                    issubclass(param_info['annotation'], BaseModel)):
                    parsed_params[param_name] = _parse_body(request.body, param_info)
                else:
                    # Handle regular typed parameters by matching names
                    if param_name in ['query_params', 'path_params', 'headers', 'body', 'method', 'url']:
                        parsed_params[param_name] = getattr(request, param_name, None)
                    elif param_info['annotation'] is QueryParams:
                        parsed_params[param_name] = request.query_params
                    elif param_info['annotation'] is PathParams:
                        parsed_params[param_name] = request.path_params  
                    elif param_info['annotation'] is Headers:
                        parsed_params[param_name] = request.headers
                    elif param_info['annotation'] is Body:
                        parsed_params[param_name] = request.body
        except ValueError as e:
            raise ValueError(f"Parameter '{param_name}': {e}")
    
    return parsed_params