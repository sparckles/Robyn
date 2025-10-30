"""
Test routes for issue #1251: static files + API routes at same base path.

Notes:
1. No need to test every method, just one is enough to ensure no conflict.
2. The static files are served from ./integration_tests to avoid conflict with the /test_dir route in main app.
3. The static file serving route is defined in a separate SubRouter to isolate it from the main app routes.
4. Serving api & files from the same /static path to test the fix.
"""

from robyn import Request, SubRouter


static_router = SubRouter(__name__, "/static")


@static_router.get("/build")
@static_router.post("/build")
async def file_serve(request: Request):
    """
    - Test route to ensure no conflict with static file serving at /static
    - Though static files are served at /static, it should serve this api route, coz build is
        not a file, so fallback to api to serve the request.
    """
    return f"{request.method}:{request.url.path} works"
