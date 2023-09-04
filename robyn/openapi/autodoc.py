import inspect
import warnings

import yaml


class OpenAPIDocstringParser:
    def __init__(self, docstring: str):
        """
        Args:
            docstring (str): docstring of function to be parsed
        """
        if docstring is None:
            docstring = ""
        self.docstring = inspect.cleandoc(docstring)

    def to_openAPI_2(self) -> dict:
        """
        Returns:
            json style dict: dict to be read for the path by swagger 2.0 UI
        """
        raise NotImplementedError()

    def to_openAPI_3(self) -> dict:
        """
        Returns:
            json style dict: dict to be read for the path by swagger 3.0.0 UI
        """
        raise NotImplementedError()


class YamlStyleParametersParser(OpenAPIDocstringParser):
    def _parse_no_yaml(self, doc: str) -> dict:
        """
        Args:
            doc (str): section of doc before yaml, or full section of doc
        Returns:
            json style dict: dict to be read for the path by swagger UI
        """
        # clean again in case further indentation can be removed,
        # usually this do nothing...
        doc = inspect.cleandoc(doc)

        if len(doc) == 0:
            return {}

        lines = doc.split("\n")

        if len(lines) == 1:
            return {"summary": lines[0]}
        else:
            summary = lines.pop(0)

            # remove empty lines at the beginning of the description
            while len(lines) and lines[0].strip() == "":
                lines.pop(0)

            if len(lines) == 0:
                return {"summary": summary}
            else:
                # use html tag to preserve linebreaks
                return {"summary": summary, "description": "<br>".join(lines)}

    def _parse_yaml(self, doc: str) -> dict:
        """
        Args:
            doc (str): section of doc detected as openapi yaml
        Returns:
            json style dict: dict to be read for the path by swagger UI
        Warns:
            UserWarning if the yaml couldn't be parsed
        """
        try:
            return yaml.safe_load(doc)
        except Exception as e:
            warnings.warn("error parsing openAPI yaml, ignoring it. ({})".format(e))
            return {}

    def _parse_all(self) -> dict:
        if "openapi:\n" not in self.docstring:
            return self._parse_no_yaml(self.docstring)

        predoc, yamldoc = self.docstring.split("openapi:\n", 1)

        conf = self._parse_no_yaml(predoc)
        conf.update(self._parse_yaml(yamldoc))
        return conf

    def to_openAPI_2(self) -> dict:
        return self._parse_all()

    def to_openAPI_3(self) -> dict:
        return self._parse_all()
