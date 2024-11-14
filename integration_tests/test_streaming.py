import pytest
from robyn import Robyn
import asyncio
import aiohttp
import async_timeout

@pytest.mark.asyncio
async def test_sync_streaming():
    await asyncio.sleep(0.1)  # Wait for server to start
    
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:8080/stream') as response:
            assert response.status == 200
            assert response.headers['Transfer-Encoding'] == 'chunked'
            
            chunks = []
            async with async_timeout.timeout(2):
                async for chunk in response.content.iter_chunks():
                    chunks.append(chunk[0].decode())
            
            assert ''.join(chunks) == "0\n1\n2\n"

@pytest.mark.asyncio
async def test_async_streaming():
    await asyncio.sleep(0.1)
    
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:8080/stream-async') as response:
            assert response.status == 200
            assert response.headers['Transfer-Encoding'] == 'chunked'
            
            start_time = asyncio.get_event_loop().time()
            chunks = []
            async with async_timeout.timeout(2):
                async for chunk in response.content.iter_chunks():
                    chunks.append(chunk[0].decode())
            duration = asyncio.get_event_loop().time() - start_time
            
            assert ''.join(chunks) == "0\n1\n2\n"
            assert duration >= 0.2  # Verify delays between chunks
