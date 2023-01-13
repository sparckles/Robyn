
from typing import Any, Callable, List, Dict
from inspect import signature, Signature, Parameter
from .utils import decode_bytearray
import json

def get_signature(call: Callable[..., Any]) -> Signature:
    """
    Gets the dependencies of the function wrapped by the routing decorators
    (stores the name of the )
    """
    sign = signature(call)
    params = [Parameter(
        name = param.name,
        kind = param.kind,
        default = param.default,
        # Add ForwardRef analysis here as the annotation value
        annotation = param.annotation,
    ) for param in sign.parameters.values()]

    return Signature(params)

def check_params_dependencies(expected: Signature, request: Dict[Any, Any]):
        """
        Checks if the params match the dependencies of the route
        """
        provided = json.loads(decode_bytearray(request))
        if len(expected.parameters) != len(provided):
            return False
        for arg_name, arg_val in provided.items():
            access = expected.parameters.get(arg_name, None)
            if not access or not isinstance(arg_val, access.annotation):
                return False
            
        return True



