"""
ingest.py - 文書取込・チャンク分割モジュール
企画書 Step 2 に対応（01_ingest.ipynb のバックエンド）
"""
import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# 企画書仕様: chunk_size=512, overlap=64
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 64


def load_pdfs(data_dir: str = "data/raw") -> List[Document]:
    """指定ディレクトリ内の全PDFを読み込む"""
    docs = []
    raw_path = Path(data_dir)
    pdf_files = list(raw_path.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"PDFが見つかりません: {raw_path.resolve()}")

    for pdf_path in pdf_files:
        print(f"  読み込み中: {pdf_path.name}")
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        # ソース情報を付与
        for page in pages:
            page.metadata["source_file"] = pdf_path.name
        docs.extend(pages)
        print(f"    → {len(pages)} ページ読み込み完了")

    print(f"\n合計: {len(docs)} ページ（{len(pdf_files)} ファイル）")
    return docs


def split_documents(
    docs: List[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Document]:
    """ドキュメントをチャンクに分割する"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"チャンク数: {len(chunks)}（期待値: 200〜500）")
    return chunks


def preview_chunks(chunks: List[Document], n: int = 3) -> None:
    """チャンクのプレビュー表示"""
    print(f"\n=== チャンクプレビュー（先頭{n}件） ===")
    for i, chunk in enumerate(chunks[:n]):
        print(f"\n--- Chunk {i+1} ---")
        print(f"ソース: {chunk.metadata.get('source_file', 'unknown')} p.{chunk.metadata.get('page', '?')}")
        print(f"文字数: {len(chunk.page_content)}")
        print(f"内容: {chunk.page_content[:200]}...")


if __name__ == "__main__":
    # 単体テスト
    docs = load_pdfs("data/raw")
    chunks = split_documents(docs)
    preview_chunks(chunks)
