from typing import Callable, List
from abc import ABC, abstractmethod

from jinja2 import Environment, FileSystemLoader

from robyn import status_codes, HttpMethod, Robyn
from robyn.router import Route

from .robyn import Headers, Response


class TemplateInterface(ABC):
    def __init__(self): ...

    @abstractmethod
    def render_template(self, *args, **kwargs) -> Response: ...

    @abstractmethod
    def set_robyn(self, robyn: Robyn) -> None: ...

    @abstractmethod
    def url_for(self, function_name: str, route_type: HttpMethod = HttpMethod.GET) -> str: ...


class JinjaTemplate(TemplateInterface):
    def __init__(self, directory, encoding="utf-8", followlinks=False) -> None:
        self.env: Environment = Environment(loader=FileSystemLoader(searchpath=directory, encoding=encoding, followlinks=followlinks))
        self.add_function_to_globals("url_for", self.url_for)
        self.robyn: Robyn | None = None

    def add_function_to_globals(self, name: str, func: Callable):
        """
        Add a global function to a Jinja environment.
        """
        self.env.globals[name] = func

    def set_robyn(self, robyn: Robyn) -> None:
        """
        The url_for needs to have access to the list of routes stored in the apps Robyn object

        Args:
            robyn (Robyn): The top instance of the Robyn class for this app.
        """
        self.robyn = robyn

    def url_for(self, function_name: str, route_type: HttpMethod = HttpMethod.GET) -> str:
        """Creates a link to an endpoint function name

        Returns:
            str: the url for the function
        """

        if self.robyn is None:
            return "url_for needs set_robyn"

        routes: List[Route] = self.robyn.router.get_routes()

        for r in routes:
            if r.function.handler.__name__ == function_name and r.route_type == route_type:
                return r.route

        return "route not found in Robyn router"

    def render_template(self, template_name, **kwargs) -> Response:
        rendered_template = self.env.get_template(template_name).render(**kwargs)
        return Response(
            status_code=status_codes.HTTP_200_OK,
            description=rendered_template,
            headers=Headers({"Content-Type": "text/html; charset=utf-8"}),
        )


__all__ = ["TemplateInterface", "JinjaTemplate"]
