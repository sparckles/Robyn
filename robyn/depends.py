import inspect
import logging
from typing import Any, Callable, Dict

_logger = logging.getLogger(__name__)


class Depends:
    """Mark a handler parameter as a dependency to be resolved at request time.

    Usage::

        async def get_db():
            db = create_connection()
            try:
                yield db
            finally:
                db.close()

        def get_current_user(request: Request):
            token = request.headers.get("Authorization")
            return verify_token(token)

        @app.get("/items")
        async def list_items(db=Depends(get_db), user=Depends(get_current_user)):
            return db.query("SELECT * FROM items WHERE user_id = ?", user.id)
    """

    def __init__(self, dependency: Callable, *, use_cache: bool = True) -> None:
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        return f"Depends({self.dependency.__name__})"


def _detect_depends_params(handler_params: dict) -> Dict[str, "Depends"]:
    """Find parameters with Depends() as their default value."""
    depends_params = {}
    for name, param in handler_params.items():
        if isinstance(param.default, Depends):
            depends_params[name] = param.default
    return depends_params


async def _resolve_dependency(dep: Depends, request, cache: dict) -> Any:
    """Resolve a single dependency, handling both sync and async callables,
    and generator-based dependencies (for cleanup support)."""
    dep_id = id(dep.dependency)

    if dep.use_cache and dep_id in cache:
        return cache[dep_id]

    func = dep.dependency
    sig = inspect.signature(func)
    kwargs = {}

    for param_name, param in sig.parameters.items():
        if param_name in ("request", "req", "r"):
            kwargs[param_name] = request
        elif isinstance(param.default, Depends):
            kwargs[param_name] = await _resolve_dependency(param.default, request, cache)

    if inspect.isasyncgenfunction(func):
        gen = func(**kwargs)
        value = await gen.__anext__()
        cache[f"__cleanup_{dep_id}"] = gen
    elif inspect.isgeneratorfunction(func):
        gen = func(**kwargs)
        value = next(gen)
        cache[f"__cleanup_{dep_id}"] = gen
    elif inspect.iscoroutinefunction(func):
        value = await func(**kwargs)
    else:
        value = func(**kwargs)

    if dep.use_cache:
        cache[dep_id] = value

    return value


async def resolve_dependencies(depends_params: Dict[str, Depends], request) -> tuple:
    """Resolve all dependencies for a handler.

    Returns:
        (resolved_kwargs, cache) - the resolved values and the cache (for cleanup)
    """
    cache: dict = {}
    resolved = {}

    for param_name, dep in depends_params.items():
        resolved[param_name] = await _resolve_dependency(dep, request, cache)

    return resolved, cache


async def cleanup_dependencies(cache: dict) -> None:
    """Clean up generator-based dependencies."""
    for key, value in list(cache.items()):
        if not str(key).startswith("__cleanup_"):
            continue
        try:
            if inspect.isasyncgen(value):
                try:
                    await value.__anext__()
                except StopAsyncIteration:
                    pass
            elif inspect.isgenerator(value):
                try:
                    next(value)
                except StopIteration:
                    pass
        except Exception:
            _logger.exception("Error during dependency cleanup for %s", key)
