"""
vectorstore.py - SAP HANA Cloud Vector Store 操作モジュール
企画書 Step 3 に対応（02_vectorstore.ipynb のバックエンド）
Embedding: Google Gemini text-embedding-004
"""
import os
from typing import List, Optional

from hdbcli import dbapi
from langchain_hana import HanaDB
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

TABLE_NAME = "SAP_RAG_DOCS"

# Gemini Embedding モデル（768次元 / 無料枠あり）
EMBEDDING_MODEL = "models/gemini-embedding-001"


def get_connection() -> dbapi.Connection:
    """SAP HANA Cloud への接続を確立する"""
    conn = dbapi.connect(
        address=os.getenv("HANA_DB_ADDRESS"),
        port=int(os.getenv("HANA_DB_PORT", "443")),
        user=os.getenv("HANA_DB_USER", "DBADMIN"),
        password=os.getenv("HANA_DB_PASSWORD"),
        encrypt=True,
        sslValidateCertificate=False,
    )
    print("✅ SAP HANA Cloud 接続成功")
    return conn


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Gemini Embedding モデルを返す"""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def get_vectorstore(conn: dbapi.Connection, table_name: str = TABLE_NAME) -> HanaDB:
    """HanaDB VectorStore インスタンスを返す"""
    vectorstore = HanaDB(
        connection=conn,
        embedding=get_embeddings(),
        table_name=table_name,
    )
    return vectorstore


def ingest_documents(
    chunks: List[Document],
    conn: Optional[dbapi.Connection] = None,
    table_name: str = TABLE_NAME,
    batch_size: int = 20,
) -> HanaDB:
    """
    チャンクを SAP HANA Cloud に格納する
    Gemini Free Tier: 100 req/min → batch_size=20 で 3秒待機しながら安全に投入
    """
    import time

    if conn is None:
        conn = get_connection()

    vectorstore = get_vectorstore(conn, table_name)
    total = len(chunks)
    print(f"ベクトル格納開始: {total} チャンク → {table_name}")
    print(f"（バッチサイズ={batch_size}, レート制限対応モード）")

    t0 = time.time()
    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        retries = 0
        while retries < 5:
            try:
                vectorstore.add_documents(batch)
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait = 30 * (retries + 1)
                    print(f"  ⚠️  レート制限 → {wait}秒待機してリトライ...")
                    time.sleep(wait)
                    retries += 1
                else:
                    raise

        done = min(i + batch_size, total)
        elapsed = time.time() - t0
        print(f"  進捗: {done}/{total} ({elapsed:.0f}秒経過)")

        # 60秒あたり100リクエスト制限 → batch_size=20なら3秒待機で安全
        if done < total:
            time.sleep(3)

    print(f"✅ 全 {total} チャンク格納完了（合計 {time.time()-t0:.0f}秒）")
    return vectorstore


def similarity_search(
    query: str,
    conn: Optional[dbapi.Connection] = None,
    k: int = 3,
    table_name: str = TABLE_NAME,
) -> List[Document]:
    """類似度検索（COSINE_SIMILARITY）を実行する"""
    if conn is None:
        conn = get_connection()

    vectorstore = get_vectorstore(conn, table_name)
    results = vectorstore.similarity_search(query, k=k)
    return results
