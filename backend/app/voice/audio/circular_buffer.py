"""
Audio Buffer — CircularBuffer implementing a thread-safe byte ring buffer.
"""
import threading
from typing import Optional
import logging

logger = logging.getLogger("backend.voice.audio.circular_buffer")


class CircularBuffer:
    """Fixed-capacity circular byte ring buffer for real-time PCM audio data."""

    def __init__(self, capacity: int = 65536):
        self.capacity = capacity
        self._buffer = bytearray(capacity)
        self._head = 0  # Write index
        self._tail = 0  # Read index
        self._size = 0
        self._lock = threading.Lock()
        self.overflow_count = 0

    def write(self, data: bytes) -> int:
        """Write bytes to circular buffer. Returns number of bytes written."""
        with self._lock:
            data_len = len(data)
            if data_len == 0:
                return 0

            # Handle overflow if data exceeds available capacity
            available = self.capacity - self._size
            if data_len > available:
                self.overflow_count += 1
                # Drop oldest data to make room
                drop_len = data_len - available
                self._tail = (self._tail + drop_len) % self.capacity
                self._size -= drop_len

            # Perform ring copy
            first_chunk = min(data_len, self.capacity - self._head)
            self._buffer[self._head : self._head + first_chunk] = data[:first_chunk]

            second_chunk = data_len - first_chunk
            if second_chunk > 0:
                self._buffer[0:second_chunk] = data[first_chunk:]

            self._head = (self._head + data_len) % self.capacity
            self._size += data_len
            return data_len

    def read(self, num_bytes: int) -> bytes:
        """Read up to num_bytes from circular buffer."""
        with self._lock:
            read_len = min(num_bytes, self._size)
            if read_len == 0:
                return b""

            first_chunk = min(read_len, self.capacity - self._tail)
            result = bytearray(self._buffer[self._tail : self._tail + first_chunk])

            second_chunk = read_len - first_chunk
            if second_chunk > 0:
                result.extend(self._buffer[0:second_chunk])

            self._tail = (self._tail + read_len) % self.capacity
            self._size -= read_len
            return bytes(result)

    def size(self) -> int:
        """Return current buffered bytes count."""
        with self._lock:
            return self._size

    def clear(self) -> None:
        """Clear buffer contents."""
        with self._lock:
            self._head = 0
            self._tail = 0
            self._size = 0
