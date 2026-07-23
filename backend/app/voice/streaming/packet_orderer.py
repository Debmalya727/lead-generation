"""
Audio Streaming — PacketOrderer for reordering out-of-order UDP/WS audio packets.
"""
from typing import Dict, List, Optional
import heapq
import logging

from app.voice.streaming.schemas import AudioChunkPacket

logger = logging.getLogger("backend.voice.streaming.packet_orderer")


class PacketOrderer:
    """Jitter buffer reordering out-of-sequence audio packets."""

    def __init__(self, buffer_size: int = 10):
        self.buffer_size = buffer_size
        self._buffers: Dict[str, List[tuple]] = {}  # session_id -> heap of (seq_num, packet)
        self._expected_seq: Dict[str, int] = {}

    def push_packet(self, packet: AudioChunkPacket) -> List[AudioChunkPacket]:
        """Push packet into jitter heap and pop sequential ready packets."""
        session_id = packet.header.session_id
        seq = packet.header.sequence_number

        if session_id not in self._buffers:
            self._buffers[session_id] = []
            self._expected_seq[session_id] = 1

        heapq.heappush(self._buffers[session_id], (seq, packet))

        ready = []
        while self._buffers[session_id]:
            min_seq, min_pkt = self._buffers[session_id][0]
            if min_seq <= self._expected_seq[session_id] or len(self._buffers[session_id]) >= self.buffer_size:
                heapq.heappop(self._buffers[session_id])
                ready.append(min_pkt)
                self._expected_seq[session_id] = min_seq + 1
            else:
                break

        return ready


packet_orderer = PacketOrderer()
