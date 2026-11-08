"""
VEDANTA — Text Chunker
Splits document text into retrieval-ready chunks with sentence awareness.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChunkData:
    text: str
    text_hash: str
    chunk_index: int
    char_start: int
    char_end: int
    token_count: int
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    page_id: Optional[str] = None
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    metadata: dict = field(default_factory=dict)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 0.75 words ≈ 4 chars."""
    return max(1, len(text) // 4)


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex patterns."""
    # Split on sentence endings followed by whitespace
    sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
    sentences = sentence_endings.split(text)
    # Also split on newlines that look like paragraph breaks
    result = []
    for sent in sentences:
        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', sent)
        result.extend(p.strip() for p in paragraphs if p.strip())
    return result


class TextChunker:
    """
    Sentence-aware text chunker for retrieval indexing.

    Produces overlapping chunks to prevent answer loss at boundaries.
    Default: 512 tokens max, 64 token overlap.
    """

    def __init__(
        self,
        max_tokens: int = 512,
        overlap_tokens: int = 64,
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        # Approximate max chars (4 chars/token)
        self.max_chars = max_tokens * 4
        self.overlap_chars = overlap_tokens * 4

    def chunk(
        self,
        text: str,
        source_url: Optional[str] = None,
        source_title: Optional[str] = None,
        page_id: Optional[str] = None,
        document_id: Optional[str] = None,
        page_number: Optional[int] = None,
    ) -> List[ChunkData]:
        """
        Split text into overlapping chunks and return ChunkData list.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        sentences = _split_into_sentences(text)

        if not sentences:
            sentences = [text]

        chunks: List[ChunkData] = []
        current_chunk_sentences: List[str] = []
        current_chars = 0
        char_pos = 0
        chunk_index = 0

        # Track position in original text
        sentence_positions: List[tuple[str, int, int]] = []
        pos = 0
        for sent in sentences:
            start = text.find(sent, pos)
            if start == -1:
                start = pos
            end = start + len(sent)
            sentence_positions.append((sent, start, end))
            pos = end

        sent_idx = 0
        while sent_idx < len(sentence_positions):
            sent, sent_start, sent_end = sentence_positions[sent_idx]

            if current_chars + len(sent) > self.max_chars and current_chunk_sentences:
                # Emit current chunk
                chunk_text = " ".join(current_chunk_sentences)
                chunk_start = text.find(current_chunk_sentences[0])
                chunk_end = chunk_start + len(chunk_text)

                chunks.append(ChunkData(
                    text=chunk_text,
                    text_hash=_sha256(chunk_text),
                    chunk_index=chunk_index,
                    char_start=chunk_start,
                    char_end=chunk_end,
                    token_count=_estimate_tokens(chunk_text),
                    source_url=source_url,
                    source_title=source_title,
                    page_id=page_id,
                    document_id=document_id,
                    page_number=page_number,
                ))
                chunk_index += 1

                # Overlap: keep last N chars worth of sentences
                overlap_sents: List[str] = []
                overlap_total = 0
                for prev_sent in reversed(current_chunk_sentences):
                    if overlap_total + len(prev_sent) > self.overlap_chars:
                        break
                    overlap_sents.insert(0, prev_sent)
                    overlap_total += len(prev_sent) + 1

                current_chunk_sentences = overlap_sents
                current_chars = sum(len(s) for s in current_chunk_sentences)

            current_chunk_sentences.append(sent)
            current_chars += len(sent) + 1
            sent_idx += 1

        # Emit final chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            if chunk_text.strip():
                chunk_start = text.find(current_chunk_sentences[0])
                chunk_end = chunk_start + len(chunk_text)
                chunks.append(ChunkData(
                    text=chunk_text,
                    text_hash=_sha256(chunk_text),
                    chunk_index=chunk_index,
                    char_start=max(0, chunk_start),
                    char_end=min(len(text), chunk_end),
                    token_count=_estimate_tokens(chunk_text),
                    source_url=source_url,
                    source_title=source_title,
                    page_id=page_id,
                    document_id=document_id,
                    page_number=page_number,
                ))

        return chunks
