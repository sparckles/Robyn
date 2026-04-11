"""Parameter annotation markers for route handlers.

These markers provide validation constraints and OpenAPI metadata for
individual query, path, header, and cookie parameters.

Usage::

    from robyn import Query, Path

    @app.get("/users/:user_id")
    async def get_user(
        user_id: int = Path(description="The user's ID"),
        page: int = Query(default=1, ge=1, description="Page number"),
        limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ):
        ...
"""

from typing import Any, Optional


class _ParamMarker:
    """Base class for parameter markers.

    Subclassed by Query, Path, Header, Cookie to indicate where
    a parameter value should be sourced from.
    """

    __slots__ = ("default", "alias", "title", "description", "gt", "ge", "lt", "le",
                 "min_length", "max_length", "pattern", "deprecated", "example", "source")

    def __init__(
        self,
        default: Any = ...,
        *,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        deprecated: bool = False,
        example: Any = None,
    ) -> None:
        self.default = default
        self.alias = alias
        self.title = title
        self.description = description
        self.gt = gt
        self.ge = ge
        self.lt = lt
        self.le = le
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.deprecated = deprecated
        self.example = example
        self.source = self.__class__.__name__.lower()

    @property
    def required(self) -> bool:
        return self.default is ...

    def validate(self, value: Any, param_name: str) -> Any:
        """Validate a value against the constraints. Raises ValueError on failure."""
        if value is None:
            if self.required:
                raise ValueError(f"Parameter '{param_name}' is required")
            return self.default if self.default is not ... else None

        if self.gt is not None and value <= self.gt:
            raise ValueError(f"Parameter '{param_name}' must be greater than {self.gt}")
        if self.ge is not None and value < self.ge:
            raise ValueError(f"Parameter '{param_name}' must be greater than or equal to {self.ge}")
        if self.lt is not None and value >= self.lt:
            raise ValueError(f"Parameter '{param_name}' must be less than {self.lt}")
        if self.le is not None and value > self.le:
            raise ValueError(f"Parameter '{param_name}' must be less than or equal to {self.le}")

        if isinstance(value, str):
            if self.min_length is not None and len(value) < self.min_length:
                raise ValueError(f"Parameter '{param_name}' must have at least {self.min_length} characters")
            if self.max_length is not None and len(value) > self.max_length:
                raise ValueError(f"Parameter '{param_name}' must have at most {self.max_length} characters")
            if self.pattern is not None:
                import re
                if not re.match(self.pattern, value):
                    raise ValueError(f"Parameter '{param_name}' does not match pattern '{self.pattern}'")

        return value

    def to_openapi_param(self, name: str, annotation: type = str) -> dict:
        """Generate an OpenAPI parameter object."""
        type_mapping = {int: "integer", float: "number", str: "string", bool: "boolean"}
        schema: dict = {"type": type_mapping.get(annotation, "string")}

        if self.gt is not None:
            schema["exclusiveMinimum"] = self.gt
        if self.ge is not None:
            schema["minimum"] = self.ge
        if self.lt is not None:
            schema["exclusiveMaximum"] = self.lt
        if self.le is not None:
            schema["maximum"] = self.le
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
        if self.pattern is not None:
            schema["pattern"] = self.pattern

        param: dict = {
            "name": self.alias or name,
            "in": self.source,
            "required": self.required,
            "schema": schema,
        }

        if self.description:
            param["description"] = self.description
        if self.deprecated:
            param["deprecated"] = True
        if self.example is not None:
            param["example"] = self.example

        return param

    def __repr__(self) -> str:
        parts = [f"default={self.default!r}"]
        if self.description:
            parts.append(f"description={self.description!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"


class Query(_ParamMarker):
    """Mark a parameter as a query string parameter."""
    pass


class Path(_ParamMarker):
    """Mark a parameter as a path/URL parameter."""
    pass


class Header(_ParamMarker):
    """Mark a parameter as an HTTP header parameter."""
    pass


class Cookie(_ParamMarker):
    """Mark a parameter as a cookie parameter."""
    pass
