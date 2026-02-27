from abc import ABC, abstractmethod

from jinja2 import Environment, FileSystemLoader, select_autoescape

from robyn import status_codes

from .robyn import Headers, Response


class TemplateInterface(ABC):
    def __init__(self): ...

    @abstractmethod
    def render_template(self, *args, **kwargs) -> Response: ...


class JinjaTemplate(TemplateInterface):
    def __init__(self, directory, encoding="utf-8", followlinks=False):
        """
        Initializes the Jinja2 template environment with autoescape enabled for HTML and XML files.

        Args:
            directory (str): The directory where templates are located.
            encoding (str): The encoding to use when loading templates.
            followlinks (bool): Whether to follow symbolic links in the template directory.
        """
        self.env = Environment(
            loader=FileSystemLoader(searchpath=directory, encoding=encoding, followlinks=followlinks),
            autoescape=select_autoescape(["html", "htm", "xml"], default=True),
        )

    def render_template(self, template_name, **kwargs) -> Response:
        rendered_template = self.env.get_template(template_name).render(**kwargs)
        return Response(
            status_code=status_codes.HTTP_200_OK,
            description=rendered_template,
            headers=Headers({"Content-Type": "text/html; charset=utf-8"}),
        )


__all__ = ["TemplateInterface", "JinjaTemplate"]
