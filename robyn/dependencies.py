
from typing import Any, Callable, List, Dict, Union, ForwardRef, cast, get_type_hints
from inspect import signature, Signature, Parameter, getmembers, isfunction
import msgspec
import sys

sequence_types = (set, list, tuple)
defaults = (int, float, str, bool, bytes, bytearray)

class BaseValidation(msgspec.Struct, forbid_unknown_fields=True):
    """
    Base class for validation, used to explicitly forbid unknown fields
    The response body MUST be exactly as the params specify,
    hence forbid_unknown_fields = True
    """
    # Create a metaclass so we can "vary" the arguments sent into msgspec.Struct
    # to increase user customizability?
    pass

def decode_bytearray(req):
    """
    Decodes a bytearray into a UTF-8 string
    """
    return bytearray(req["body"]).decode("utf-8")

if sys.version_info < (3, 9):
    # Credit to Pydantic

    def evaluate_forwardref(type_: ForwardRef, globalns: Any, localns: Any) -> Any:
        return type_._evaluate(globalns, localns)
else:

    def evaluate_forwardref(type_: ForwardRef, globalns: Any, localns: Any) -> Any:
        # Even though it is the right signature for python 3.9, mypy complains with
        # `error: Too many arguments for "_evaluate" of "ForwardRef"` hence the cast...
        return cast(Any, type_)._evaluate(globalns, localns, set())

def get_typed_annotation(annotation: Any, globalns: Dict[str, Any]) -> Any:
    # Credit to FastAPI
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(annotation, globalns, globalns)
    return annotation

def model_to_dict(model: object) -> dict:
    ret_val = dict()
    for key, value in getmembers(model):
        if not key.startswith('_'):
            ret_val[key] = value
    
    return ret_val

def check_custom_class(annotation) -> bool:
    """
    Checks if the given class/annotation is a user-defined class
    """
    # Check if annotation is a type at all, or if it is a Union first to avoid errors
    # somewhat hacky solution; refer to Pydantic's lenient_subclass function for improvements
    return isinstance(annotation, type) and not (annotation is Union) \
        and not issubclass(annotation, sequence_types + (dict, )) \
        and not issubclass(annotation, defaults)

def get_class_signature(call: Callable[..., Any]):
    """
    Gets the signature of a class that has no constructor
    """
    # Get the type annotations of the class
    annotations = get_type_hints(call)
    actual_params = annotations.keys()
    globalns = getattr(call, "__globals__", {})

    # Get object representation as dictionary (to get the default values)
    class_dict = model_to_dict(call)

    # Generate the signature
    params = [
        Parameter(
            name = key,
            default = class_dict.get(key, Parameter.empty),
            kind = Parameter.POSITIONAL_OR_KEYWORD,
            annotation = get_typed_annotation(annotations[key], globalns),
        ) for key in actual_params
    ]

    return Signature(params)
    

def get_signature(call: Callable[..., Any]) -> Signature:
    """
    Gets the function signature wrapped by the routing decorators
    """
    # Credit to FastAPI
    sign = signature(call)
    globalns = getattr(call, "__globals__", {})
    params = [Parameter(
        name = param.name,
        kind = param.kind,
        default = param.default,
        annotation = get_typed_annotation(param.annotation, globalns),
    ) for param in sign.parameters.values()]

    return Signature(params)
        
def model_eval(param, custom_model=None):
    if not param.default == param.empty:
        return (param.name, param.annotation if custom_model is None else custom_model, param.default)
    return (param.name, param.annotation if custom_model is None else custom_model)

def create_model(call: Callable[..., Any]) -> msgspec.Struct:
    """
    Creates a validation model for a given handler function
    """
    sign: Any = Any
    # If constructor does not exist, and the class is a non-default class
    # then use get_class_signature. Otherwise, if the constructor exists, we
    # base the model off of the constructor's type annotations
    if check_custom_class(type(call)) and not isfunction(call.__init__):
        sign = get_class_signature(call)
    else:
        sign = get_signature(call)
    
    cstruct = list()
    for param in sign.parameters.values():
        cust_model = None
        if check_custom_class(param.annotation):
            cust_model = create_model(param.annotation)
        
        cstruct.append(model_eval(param, cust_model))

    return msgspec.defstruct(call.__name__, fields=cstruct, bases=(BaseValidation,))

def check_params_dependencies(call: Callable[..., Any], request: Dict[Any, Any]):
    """
    Checks if the params match the dependencies of the route
    """
    # Try to create a model from the given request args
    model = create_model(call)
    func_input = None
    try:
        # Find a way to globally cache decoder? Is it multiprocess safe?
        # Validate the model (annotations are only checked when decoding messages in msgspec)
        func_input = msgspec.json.decode(bytes(request['body']), type=model)
    except msgspec.ValidationError as exc:
        raise msgspec.ValidationError from exc
    
    return model_to_dict(func_input)




