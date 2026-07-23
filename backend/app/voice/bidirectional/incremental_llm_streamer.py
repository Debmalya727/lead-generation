"""
IncrementalLLMStreamer — Buffers streaming LLM text tokens into complete sentence/clause chunks for zero-latency TTS synthesis.
"""
import re
from typing import AsyncGenerator, List, Optional
import logging

logger = logging.getLogger("backend.voice.bidirectional.llm_streamer")


class IncrementalLLMStreamer:
    """Aggregates streaming LLM text tokens and yields sentence/clause chunks."""

    def __init__(self):
        self._sentence_delimiters = re.compile(r"([.?!,\n])")

    async def aggregate_tokens(
        self, token_generator: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """Buffer tokens and yield complete sentences as soon as delimiters are encountered."""
        buffer = ""
        async for token in token_generator:
            buffer += token
            # Split buffer by delimiters
            parts = self._sentence_delimiters.split(buffer)

            # If we have completed sentence boundary parts
            if len(parts) > 1:
                # Reassemble delimiter with pre-delimiter text
                for i in range(0, len(parts) - 1, 2):
                    sentence = parts[i] + parts[i + 1]
                    sentence_str = sentence.strip()
                    if sentence_str:
                        logger.debug(f"IncrementalLLMStreamer: Yielding sentence chunk: '{sentence_str}'")
                        yield sentence_str

                # Remaining un-delimited trailing token
                buffer = parts[-1]

        # Flush remaining buffer at end of stream
        remaining = buffer.strip()
        if remaining:
            logger.debug(f"IncrementalLLMStreamer: Flushing final chunk: '{remaining}'")
            yield remaining


incremental_llm_streamer = IncrementalLLMStreamer()
