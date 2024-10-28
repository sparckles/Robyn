from abc import ABC, abstractmethod

from jinja2 import Environment, FileSystemLoader

from robyn import status_codes

from .robyn import Headers, Response

def url_for() -> str:
    """Creates a link to an endpoint function name

    NOT YET IMPLEMENTED
    #TODO
    #FIXME
    Returns:
        str: the url for the function
    """
    return "called new url_for"

class TemplateInterface(ABC):
    def __init__(self): ...

    @abstractmethod
    def render_template(self, *args, **kwargs) -> Response: ...


class JinjaTemplate(TemplateInterface):
    def __init__(self, directory, encoding="utf-8", followlinks=False):
        self.env = Environment(loader=FileSystemLoader(searchpath=directory, encoding=encoding, followlinks=followlinks))
        self.env.globals['url_for'] = url_for

    def render_template(self, template_name, **kwargs) -> Response:
        rendered_template = self.env.get_template(template_name).render(**kwargs)
        return Response(
            status_code=status_codes.HTTP_200_OK,
            description=rendered_template,
            headers=Headers({"Content-Type": "text/html; charset=utf-8"}),
        )


__all__ = ["TemplateInterface", "JinjaTemplate"]
