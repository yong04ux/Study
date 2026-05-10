"""RAG 文档加载模块。

负责从 data/docs 目录读取 txt 和 md 文件，
把原始文本和文件信息封装成 LoadedDocument，供后续文本切分和向量化使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LoadedDocument:
    """从磁盘读取到的一篇原始文档。"""

    content: str
    metadata: dict[str, str] = field(default_factory=dict)


class DocumentLoader:
    """从指定目录递归加载 txt / markdown 文档。"""

    def __init__(self, docs_dir: str | Path = "data/docs") -> None:
        self.docs_dir = Path(docs_dir)
        self.supported_suffixes = {".txt", ".md"}

    def load(self) -> list[LoadedDocument]:
        """读取支持的文档，并跳过空文件。

        返回的 metadata 会保存 source、filename、file_type，
        这些信息会跟随文本块进入 Chroma，最终作为问答引用来源返回给前端。
        """
        if not self.docs_dir.exists():
            raise FileNotFoundError(f"Document directory does not exist: {self.docs_dir}")

        documents: list[LoadedDocument] = []
        for path in sorted(self.docs_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in self.supported_suffixes:
                continue

            content = path.read_text(encoding="utf-8-sig").strip()
            if not content:
                continue

            documents.append(
                LoadedDocument(
                    content=content,
                    metadata={
                        "source": str(path.as_posix()),
                        "filename": path.name,
                        "file_type": path.suffix.lower().lstrip("."),
                    },
                )
            )
        return documents
