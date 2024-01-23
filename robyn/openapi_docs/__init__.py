from robyn.responses import html


def return_swagger_docs():
    return html(
        """
<!DOCTYPE html>
<html>
<head>
<title>Swagger UI</title>
<link
rel="stylesheet"
type="text/css"
href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css"
/>
<script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
<script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-standalone-preset.js"></script>
</head>
<body>
<div id="swagger-ui"></div>
<script>
window.onload = function () {
    SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: "#swagger-ui",
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
        layout: "StandaloneLayout",
    });
};
</script>
</body>
</html>
            """
    )
