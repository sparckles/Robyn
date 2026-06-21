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
