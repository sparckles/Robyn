import inspect
import os
from abc import ABC, abstractmethod
from functools import lru_cache

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


@lru_cache(maxsize=None)
def _cached_jinja_template(directory: str) -> JinjaTemplate:
    """Builds and caches a JinjaTemplate per directory so repeated render() calls reuse the environment."""
    return JinjaTemplate(directory)


def render(template_name: str, *, templates_dir: str = "templates", **kwargs) -> Response:
    """Renders a template from a local ``templates`` directory.

    Convenience wrapper around :class:`JinjaTemplate` that resolves ``templates_dir``
    relative to the file calling ``render`` (defaulting to a ``templates`` folder next
    to it), so simple apps don't have to construct a :class:`JinjaTemplate` by hand::

        from robyn.templating import render

        @app.get("/frontend")
        async def get_frontend(request):
            return render("index.html", framework="Robyn")

    Args:
        template_name (str): The template file to render, e.g. ``"index.html"``.
        templates_dir (str): Directory holding the templates. Resolved relative to the
            caller's file when not absolute. Defaults to ``"templates"``.
        **kwargs: Variables passed to the template.

    Returns:
        Response: The rendered template as a Robyn Response object.
    """
    if not os.path.isabs(templates_dir):
        frame = inspect.currentframe()
        caller = frame.f_back if frame is not None else None
        caller_file = caller.f_globals.get("__file__") if caller is not None else None
        base_dir = os.path.dirname(os.path.abspath(caller_file)) if caller_file else os.getcwd()
        templates_dir = os.path.join(base_dir, templates_dir)

    return _cached_jinja_template(templates_dir).render_template(template_name, **kwargs)


__all__ = ["TemplateInterface", "JinjaTemplate", "render"]
