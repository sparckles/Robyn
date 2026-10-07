import asyncio

import pytest

from robyn.responses import AsyncGeneratorWrapper


def test_wrapper_drives_generator_on_constructing_loop():
    """The async generator must run on the loop that was active at construction
    (the handler's loop), so async resources bound to it work (#1219)."""
    captured = {}

    async def gen():
        captured["loop"] = asyncio.get_running_loop()
        yield "a"
        yield "b"

    async def main():
        wrapper = AsyncGeneratorWrapper(gen())  # constructed on THIS loop
        # Robyn drives __next__ from a worker thread, not the loop thread.
        chunks = await asyncio.to_thread(lambda: list(wrapper))
        return chunks, asyncio.get_running_loop()

    chunks, handler_loop = asyncio.run(main())
    assert chunks == ["a", "b"]
    assert captured["loop"] is handler_loop


def test_wrapper_propagates_generator_errors():
    """Errors inside the generator are raised, not silently swallowed."""

    async def gen():
        yield "ok"
        raise ValueError("boom")

    async def main():
        wrapper = AsyncGeneratorWrapper(gen())

        def drive():
            collected = []
            with pytest.raises(ValueError, match="boom"):
                for chunk in wrapper:
                    collected.append(chunk)
            return collected

        return await asyncio.to_thread(drive)

    assert asyncio.run(main()) == ["ok"]


def test_wrapper_without_running_loop_uses_background_loop():
    """When constructed outside an async context (sync handler), the wrapper
    runs the generator on its own background loop."""

    async def gen():
        yield "x"
        yield "y"

    wrapper = AsyncGeneratorWrapper(gen())  # no running loop here
    assert wrapper._owns_loop is True
    assert list(wrapper) == ["x", "y"]


def test_wrapper_supports_bytes_chunks():
    """The wrapper passes bytes chunks through unchanged (Rust encodes them)."""

    async def gen():
        yield b"\x00\x01"
        yield b"\x02"

    wrapper = AsyncGeneratorWrapper(gen())
    assert list(wrapper) == [b"\x00\x01", b"\x02"]


def test_owned_loop_thread_is_cleaned_up_when_dropped_early():
    """The background loop thread must not leak if the stream is abandoned
    before exhaustion (e.g. a client disconnect)."""
    import gc

    async def gen():
        yield "a"
        yield "b"
        yield "c"

    wrapper = AsyncGeneratorWrapper(gen())  # sync context -> owns a background loop
    assert wrapper._owns_loop is True
    thread = wrapper._thread
    assert thread.is_alive()

    assert next(wrapper) == "a"  # consume one chunk, then abandon the rest
    del wrapper
    gc.collect()

    thread.join(timeout=3)
    assert not thread.is_alive()


def test_abandoned_stream_runs_async_cleanup_on_handler_loop():
    """A client disconnect drops the wrapper before the generator is exhausted.
    The generator's ``finally`` must still run to completion on the handler's
    loop, including any ``await`` in it (e.g. returning a DB connection)."""

    async def main():
        handler_loop = asyncio.get_running_loop()
        cleaned_up = asyncio.Event()
        cleanup_loop = {}

        async def gen():
            try:
                yield "a"
                yield "b"
            finally:
                await asyncio.sleep(0)  # async cleanup, e.g. `await session.close()`
                cleanup_loop["loop"] = asyncio.get_running_loop()
                cleaned_up.set()

        holder = [AsyncGeneratorWrapper(gen())]

        def consume_one_then_disconnect():
            # Like the Rust driver: the worker thread holds the only reference
            # and drops it after the client goes away.
            wrapper = holder.pop()
            assert next(wrapper) == "a"

        await asyncio.to_thread(consume_one_then_disconnect)
        await asyncio.wait_for(cleaned_up.wait(), timeout=3)
        return handler_loop, cleanup_loop["loop"]

    handler_loop, cleanup_loop = asyncio.run(main())
    assert cleanup_loop is handler_loop


def test_abandoned_stream_runs_async_cleanup_on_background_loop():
    """Same as above for sync handlers: the generator's async cleanup completes
    on the background loop before that loop is stopped."""
    import gc
    import threading

    cleaned_up = threading.Event()

    async def gen():
        try:
            yield "a"
            yield "b"
        finally:
            await asyncio.sleep(0)
            cleaned_up.set()

    wrapper = AsyncGeneratorWrapper(gen())  # sync context -> owns a background loop
    thread = wrapper._thread
    assert next(wrapper) == "a"
    del wrapper
    gc.collect()

    assert cleaned_up.wait(timeout=3)
    thread.join(timeout=3)
    assert not thread.is_alive()
