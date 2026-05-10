"""Build the Chroma vector database from local RAG documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import TextSplitter
from app.rag.vector_store import ChromaVectorStore


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Build gaokao-pilot Chroma vector database.")
    parser.add_argument("--docs-dir", type=Path, default=PROJECT_ROOT / "data" / "docs")
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and split documents without generating embeddings.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing Chroma collection before upserting documents.",
    )
    return parser.parse_args()


def main() -> None:
    """Load documents, split chunks, and write them to Chroma."""
    args = parse_args()
    loader = DocumentLoader(args.docs_dir)
    splitter = TextSplitter(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)

    documents = loader.load()
    chunks = splitter.split_documents(documents)

    print(f"Loaded documents: {len(documents)}")
    print(f"Generated chunks: {len(chunks)}")

    if args.dry_run:
        print("Dry run finished. No embeddings were created.")
        return

    vector_store = ChromaVectorStore()
    if args.reset:
        vector_store.reset_collection()
        print("Reset Chroma collection before rebuilding.")

    inserted_count = vector_store.add_documents(chunks)
    print(f"Upserted chunks into Chroma: {inserted_count}")


if __name__ == "__main__":
    main()
