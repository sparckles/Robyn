import importlib.util

from robyn.templating import render


def test_render_with_explicit_templates_dir(tmp_path):
    """render() uses an absolute templates_dir as-is and returns an HTML 200 Response."""
    templates_dir = tmp_path / "tpl"
    templates_dir.mkdir()
    (templates_dir / "page.html").write_text("<h1>{{ title }}</h1>")

    response = render("page.html", templates_dir=str(templates_dir), title="Hello")

    assert response.status_code == 200
    assert "<h1>Hello</h1>" in response.description
    assert response.headers.get("Content-Type") == "text/html; charset=utf-8"


def test_render_resolves_templates_relative_to_caller(tmp_path):
    """A relative templates_dir is resolved next to the *calling* module, not the cwd."""
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "index.html").write_text("Hello {{ name }}")

    module_file = tmp_path / "app_module.py"
    module_file.write_text("from robyn.templating import render\n\n\ndef view():\n    return render('index.html', name='Robyn')\n")

    spec = importlib.util.spec_from_file_location("app_module_under_test", module_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    response = module.view()
    assert "Hello Robyn" in response.description


def test_render_autoescapes_html(tmp_path):
    """Autoescaping is inherited from JinjaTemplate, so user values are escaped."""
    templates_dir = tmp_path / "tpl"
    templates_dir.mkdir()
    (templates_dir / "page.html").write_text("{{ value }}")

    response = render("page.html", templates_dir=str(templates_dir), value="<script>")

    assert "<script>" not in response.description
    assert "&lt;script&gt;" in response.description


def test_render_uses_custom_template_engine(tmp_path):
    """A custom TemplateInterface can be supplied via template_engine; Jinja stays the default."""
    from robyn.robyn import Headers, Response
    from robyn.templating import TemplateInterface

    class EchoEngine(TemplateInterface):
        def __init__(self, directory):
            self.directory = directory

        def render_template(self, template_name, **kwargs):
            return Response(status_code=200, headers=Headers({}), description=f"{template_name}|{kwargs.get('who')}")

    response = render("x.html", templates_dir=str(tmp_path), template_engine=EchoEngine, who="Batman")

    assert response.description == "x.html|Batman"
