from abc import ABC, abstractmethod
from typing import Callable

from robyn import status_codes

from robyn import Headers, Response

from jinja2 import Environment, FileSystemLoader
from typing import Optional


class TemplateInterface(ABC):
    def __init__(self):
        ...

    @abstractmethod
    def render_template(self, *args, **kwargs) -> Response:
        ...


class JinjaTemplate(TemplateInterface):
    def __init__(self, directory, encoding="utf-8", followlinks=False):
        self.env = Environment(loader=FileSystemLoader(searchpath=directory, encoding=encoding, followlinks=followlinks))

    def render_template(self, template_name, **kwargs) -> Response:
        rendered_template = self.env.get_template(template_name).render(**kwargs)
        return Response(
            status_code=status_codes.HTTP_200_OK,
            description=rendered_template,
            headers=Headers({"Content-Type": "text/html; charset=utf-8"}),
        )

    def add_template_global(self, func: Callable, name: Optional[str] = None):
        """
        Add a global function to the Jinja environment.

        This method allows adding a global function to the Jinja environment,
        which can be accessed from any template rendered by that environment.

        Args:
            func (callable): The function to be added as a global.
            name (str, optional): The name under which the function will be
                accessible in the Jinja environment. If not provided, the name
                of the function will be used. Defaults to None.

        Raises:
            TypeError: If `func` is not callable.

        Example:
            Assuming `your_class_instance` is an instance of YourClassName:
            >>> def custom_function():
            >>>     return "Hello, world!"
            >>> your_class_instance.add_template_global(custom_function, 'hello')
            >>> # Now 'custom_function' can be accessed in Jinja templates as '{{ hello() }}'
        """
        if not callable(func):
            raise TypeError("Must be callable.")
        self.env.globals[name or func.__name__] = func

    def url_for(self, endpoint: str, **kwargs) -> str:
        """
        Generate a URL for a static resource.

        Args:
            endpoint (str): The endpoint to generate the URL for.
            **kwargs: Additional parameters such as filename or path.

        Returns:
            str: The URL for the static resource.
        """
        if endpoint == "static":
            if "filename" in kwargs:
                return f"/static/{kwargs['filename']}"
            elif "path" in kwargs:
                return f"/static/{kwargs['path']}"
        elif endpoint == "/":
            return "/"
        raise ValueError("Invalid endpoint")

    def __init__(self, directory, encoding="utf-8", followlinks=False):
        self.env = Environment(loader=FileSystemLoader(searchpath=directory, encoding=encoding, followlinks=followlinks))
        self.add_template_global(self.url_for, 'url_for')

__all__ = ["TemplateInterface", "JinjaTemplate"]
