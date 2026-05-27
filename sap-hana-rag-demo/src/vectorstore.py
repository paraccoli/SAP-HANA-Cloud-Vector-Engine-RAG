"""
vectorstore.py - SAP HANA Cloud Vector Store Operation Module
Corresponding to Step 3 of the proposal (backend for 02_vectorstore.ipynb)
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

# Gemini Embedding Model (768 dimensions / free tier available)
EMBEDDING_MODEL = "models/gemini-embedding-001"


def get_connection() -> dbapi.Connection:
    """Establish a connection to SAP HANA Cloud"""
    conn = dbapi.connect(
        address=os.getenv("HANA_DB_ADDRESS"),
        port=int(os.getenv("HANA_DB_PORT", "443")),
        user=os.getenv("HANA_DB_USER", "DBADMIN"),
        password=os.getenv("HANA_DB_PASSWORD"),
        encrypt=True,
        sslValidateCertificate=False,
    )
    print("SAP HANA Cloud connection successful")
    return conn


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Return Gemini Embedding model"""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def get_vectorstore(conn: dbapi.Connection, table_name: str = TABLE_NAME) -> HanaDB:
    """Return HanaDB VectorStore instance"""
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
    Store chunks into SAP HANA Cloud
    Gemini Free Tier: 100 req/min -> Batch safe ingestion with batch_size=20 and 3 seconds wait
    """
    import time

    if conn is None:
        conn = get_connection()

    vectorstore = get_vectorstore(conn, table_name)
    total = len(chunks)
    print(f"Starting vector ingestion: {total} chunks -> {table_name}")
    print(f"(batch_size={batch_size}, rate limit handling mode)")

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
                    print(f"  Rate limit reached -> waiting {wait} seconds to retry...")
                    time.sleep(wait)
                    retries += 1
                else:
                    raise

        done = min(i + batch_size, total)
        elapsed = time.time() - t0
        print(f"  Progress: {done}/{total} ({elapsed:.0f} seconds elapsed)")

        # Limit of 100 requests per 60 seconds -> waiting 3 seconds for batch_size=20 is safe
        if done < total:
            time.sleep(3)

    print(f"Ingestion completed for all {total} chunks (total {time.time()-t0:.0f} seconds)")
    return vectorstore


def similarity_search(
    query: str,
    conn: Optional[dbapi.Connection] = None,
    k: int = 3,
    table_name: str = TABLE_NAME,
) -> List[Document]:
    """Execute similarity search (COSINE_SIMILARITY)"""
    if conn is None:
        conn = get_connection()

    vectorstore = get_vectorstore(conn, table_name)
    results = vectorstore.similarity_search(query, k=k)
    return results

