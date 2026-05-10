"""RAG 文本切分模块。

长文档不能直接整体做 embedding，因为会超过模型上下文或影响召回精度。
这里把文档切成带 overlap 的小块，让检索时更容易命中相关片段。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rag.document_loader import LoadedDocument


@dataclass
class TextChunk:
    """准备送去 embedding 的文本块。"""

    content: str
    metadata: dict[str, str | int] = field(default_factory=dict)


class TextSplitter:
    """把长文本切分成互相有重叠的 chunk。"""

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 100) -> None:
        if chunk_size < 100:
            raise ValueError("chunk_size must be at least 100.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: list[LoadedDocument]) -> list[TextChunk]:
        """批量切分文档，并保留原始文件 metadata。"""
        chunks: list[TextChunk] = []
        for document in documents:
            for index, content in enumerate(self.split_text(document.content)):
                metadata = dict(document.metadata)
                metadata["chunk_index"] = index
                chunks.append(TextChunk(content=content, metadata=metadata))
        return chunks

    def split_text(self, text: str) -> list[str]:
        """切分单篇文本，优先在段落、换行或句号等自然边界处断开。"""
        normalized = self._normalize_text(text)
        if len(normalized) <= self.chunk_size:
            return [normalized] if normalized else []

        chunks: list[str] = []
        start = 0
        text_length = len(normalized)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            boundary = self._find_boundary(normalized, start, end)
            chunk = normalized[start:boundary].strip()
            if chunk:
                chunks.append(chunk)

            if boundary >= text_length:
                break

            next_start = boundary - self.chunk_overlap
            if next_start <= start:
                next_start = boundary
            start = max(0, next_start)

        return chunks

    @staticmethod
    def _normalize_text(text: str) -> str:
        """统一换行符，并压缩连续空行，减少无意义 token。"""
        lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
        compact_lines: list[str] = []
        previous_blank = False

        for line in lines:
            is_blank = not line
            if is_blank and previous_blank:
                continue
            compact_lines.append(line)
            previous_blank = is_blank

        return "\n".join(compact_lines).strip()

    def _find_boundary(self, text: str, start: int, end: int) -> int:
        """在目标长度附近寻找更适合阅读的切分边界。"""
        if end >= len(text):
            return len(text)

        min_boundary = start + int(self.chunk_size * 0.7)
        boundary_chars = ["\n\n", "\n", "。", "！", "？", ".", "!", "?"]

        for marker in boundary_chars:
            candidate = text.rfind(marker, min_boundary, end)
            if candidate != -1:
                return candidate + len(marker)

        return end
