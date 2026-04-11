import asyncio
import inspect

from robyn.depends import Depends, _detect_depends_params, cleanup_dependencies, resolve_dependencies


def test_depends_repr():
    def my_dep():
        return 42

    d = Depends(my_dep)
    assert "my_dep" in repr(d)


def test_detect_depends_params():
    def get_db():
        return "db"

    def handler(request, db=Depends(get_db)):
        pass

    params = dict(inspect.signature(handler).parameters)
    detected = _detect_depends_params(params)
    assert "db" in detected
    assert detected["db"].dependency is get_db
    assert "request" not in detected


def test_resolve_simple_dependency():
    def get_value():
        return 42

    depends_params = {"value": Depends(get_value)}

    loop = asyncio.new_event_loop()
    resolved, cache = loop.run_until_complete(resolve_dependencies(depends_params, None))
    loop.close()

    assert resolved["value"] == 42


def test_resolve_generator_dependency():
    cleanup_called = False

    def get_resource():
        nonlocal cleanup_called
        yield "resource"
        cleanup_called = True

    depends_params = {"res": Depends(get_resource)}

    loop = asyncio.new_event_loop()
    resolved, cache = loop.run_until_complete(resolve_dependencies(depends_params, None))
    assert resolved["res"] == "resource"
    assert not cleanup_called

    loop.run_until_complete(cleanup_dependencies(cache))
    loop.close()
    assert cleanup_called


def test_resolve_async_dependency():
    async def get_async_value():
        return "async_result"

    depends_params = {"val": Depends(get_async_value)}

    loop = asyncio.new_event_loop()
    resolved, cache = loop.run_until_complete(resolve_dependencies(depends_params, None))
    loop.close()

    assert resolved["val"] == "async_result"


def test_sub_dependencies():
    def dep_a():
        return "a"

    def dep_b(a=Depends(dep_a)):
        return f"b({a})"

    depends_params = {"result": Depends(dep_b)}

    loop = asyncio.new_event_loop()
    resolved, cache = loop.run_until_complete(resolve_dependencies(depends_params, None))
    loop.close()

    assert resolved["result"] == "b(a)"


def test_dependency_caching():
    call_count = 0

    def expensive():
        nonlocal call_count
        call_count += 1
        return "value"

    depends_params = {
        "a": Depends(expensive),
        "b": Depends(expensive),
    }

    loop = asyncio.new_event_loop()
    resolved, cache = loop.run_until_complete(resolve_dependencies(depends_params, None))
    loop.close()

    assert resolved["a"] == "value"
    assert resolved["b"] == "value"
    assert call_count == 1


def test_depends_no_cache():
    call_count = 0

    def counter():
        nonlocal call_count
        call_count += 1
        return call_count

    depends_params = {
        "a": Depends(counter, use_cache=False),
        "b": Depends(counter, use_cache=False),
    }

    loop = asyncio.new_event_loop()
    resolved, cache = loop.run_until_complete(resolve_dependencies(depends_params, None))
    loop.close()

    assert call_count == 2
