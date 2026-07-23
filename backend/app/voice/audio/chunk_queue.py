"""
Audio Buffer — ChunkQueue for queuing audio frames.
"""
import asyncio
from typing import Optional, List
import logging

logger = logging.getLogger("backend.voice.audio.chunk_queue")


class ChunkQueue:
    """Async queue storing raw audio byte chunks."""

    def __init__(self, maxsize: int = 500):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)

    async def put(self, chunk: bytes) -> None:
        """Put audio chunk into queue."""
        try:
            self._queue.put_nowait(chunk)
        except asyncio.QueueFull:
            logger.warning("ChunkQueue: Queue full, dropping oldest frame.")
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(chunk)
            except Exception:
                pass

    async def get(self) -> Optional[bytes]:
        """Fetch audio chunk from queue."""

        try:
            return await self._queue.get()
        except Exception:
            return None

    def size(self) -> int:
        """Return queue size."""
        return self._queue.qsize()
