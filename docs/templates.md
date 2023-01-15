## Creating a custom Template

Robyn supports `Jinja2` templates by default. However, Robyn believes in allowing the user to have customisability.

Hence, you can create your own renderer.

To do that, you need to import the `TemplateInterface` from `robyn.templating`

```python
from robyn.templating import TemplateInterface
```

You need to have a `render_template` method inside your implementation. So, an example would look like the following:

```python
class JinjaTemplate(TemplateInterface):
    def __init__(self, directory, encoding="utf-8", followlinks=False):
        self.env = Environment(
            loader=FileSystemLoader(
                searchpath=directory, encoding=encoding, followlinks=followlinks
            )
        )

    def render_template(self, template_name, **kwargs):
        return self.env.get_template(template_name).render(**kwargs)
```
