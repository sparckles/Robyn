from abc import ABC, abstractmethod

from jinja2 import Environment, FileSystemLoader, select_autoescape

from robyn import status_codes

from .robyn import Headers, Response


class TemplateInterface(ABC):
    """
    Interface for implementing various template engines in Robyn.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes the template interface.
        """
        super().__init__()

    @abstractmethod
    def render_template(self, *args, **kwargs) -> Response:
        """
        Renders a template with the given arguments.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: The rendered template response.
        """
        ...


class JinjaTemplate(TemplateInterface):
    """
    Jinja2 implementation of the TemplateInterface.
    """

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
            autoescape=select_autoescape(enabled_extensions=("html", "htm", "xml"), default=True),
        )

    def render_template(self, template_name, **kwargs) -> Response:
        """
        Renders a Jinja2 template.

        Args:
            template_name (str): The name of the template file to render.
            **kwargs: Variables to pass to the template.

        Returns:
            Response: The rendered template as a Robyn Response object.
        """
        rendered_template = self.env.get_template(template_name).render(**kwargs)
        return Response(
            status_code=status_codes.HTTP_200_OK,
            description=rendered_template,
            headers=Headers({"Content-Type": "text/html; charset=utf-8"}),
        )


__all__ = ["TemplateInterface", "JinjaTemplate"]
