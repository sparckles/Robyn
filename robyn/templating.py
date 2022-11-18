from abc import ABC, abstractmethod


class TemplateInterface(ABC):
    def __init__(self, template):
        ...

    @abstractmethod
    def render_template(self, *args, **kwargs):
        ...


class JinjaTemplate(TemplateInterface):
    def __init__(self, directory, encoding="utf-8", followlinks=False):
        from jinja2 import Environment, FileSystemLoader
        self.env = Environment(loader=FileSystemLoader(searchpath=directory, encoding=encoding, followlinks=followlinks))

    def render_template(self, template_name, **kwargs):
        return self.env.get_template(template_name).render(**kwargs)


__all__ = ["TemplateInterface", "JinjaTemplate"]
