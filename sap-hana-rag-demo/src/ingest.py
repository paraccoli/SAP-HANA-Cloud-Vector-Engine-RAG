"""
ingest.py - Document Ingest and Text Splitting Module
Corresponding to Step 2 of the proposal (backend for 01_ingest.ipynb)
"""
import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# Proposal specification: chunk_size=512, overlap=64
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 64


def load_pdfs(data_dir: str = "data/raw") -> List[Document]:
    """Load all PDFs from the specified directory"""
    docs = []
    raw_path = Path(data_dir)
    pdf_files = list(raw_path.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"PDF files not found: {raw_path.resolve()}")

    for pdf_path in pdf_files:
        print(f"  Loading: {pdf_path.name}")
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        # Attach source information
        for page in pages:
            page.metadata["source_file"] = pdf_path.name
        docs.extend(pages)
        print(f"    -> {len(pages)} pages loaded successfully")

    print(f"\nTotal: {len(docs)} pages ({len(pdf_files)} files)")
    return docs


def split_documents(
    docs: List[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Document]:
    """Split documents into chunks"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"Number of chunks: {len(chunks)} (expected: 200-500)")
    return chunks


def preview_chunks(chunks: List[Document], n: int = 3) -> None:
    """Display previews of the chunks"""
    print(f"\n=== Chunk Preview (First {n} items) ===")
    for i, chunk in enumerate(chunks[:n]):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Source: {chunk.metadata.get('source_file', 'unknown')} p.{chunk.metadata.get('page', '?')}")
        print(f"Character count: {len(chunk.page_content)}")
        print(f"Content: {chunk.page_content[:200]}...")


if __name__ == "__main__":
    # Unit test
    docs = load_pdfs("data/raw")
    chunks = split_documents(docs)
    preview_chunks(chunks)

