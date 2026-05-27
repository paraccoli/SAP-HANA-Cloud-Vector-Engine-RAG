"""
rag.py - RAG Pipeline Module
Corresponding to Step 4 of the proposal (backend for 03_rag_pipeline.ipynb)
LLM: Google Gemini 3.5 Flash
"""
import os
import time
from typing import Dict, Any, Optional

from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_hana import HanaDB
from dotenv import load_dotenv

load_dotenv()

# Gemini LLM model (Free tier available / cost-efficient)
DEFAULT_LLM_MODEL = "gemini-3.5-flash"


def build_rag_chain(
    vectorstore: HanaDB,
    k: int = 3,
    model: str = DEFAULT_LLM_MODEL,
    temperature: float = 0,
) -> RetrievalQA:
    """Build RAG chain (compliant with Step 4 of the proposal)"""
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    llm = ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )
    print(f"RAG Chain construction completed (Top-{k}, model={model})")
    return qa_chain


def query_with_latency(
    qa_chain: RetrievalQA,
    query: str,
) -> Dict[str, Any]:
    """Execute query and measure latency"""
    start = time.time()
    result = qa_chain.invoke({"query": query})
    latency_ms = (time.time() - start) * 1000

    return {
        "query": query,
        "answer": result["result"],
        "source_documents": result.get("source_documents", []),
        "latency_ms": round(latency_ms, 1),
    }


def print_result(result: Dict[str, Any]) -> None:
    """Format and print results"""
    print(f"\n{'='*60}")
    print(f"Q: {result['query']}")
    print(f"{'='*60}")
    print(f"A: {result['answer']}")
    print(f"\nLatency: {result['latency_ms']} ms")
    print(f"\n--- Reference Sources ---")
    for i, doc in enumerate(result["source_documents"], 1):
        src = doc.metadata.get("source_file", "unknown")
        page = doc.metadata.get("page", "?")
        print(f"  [{i}] {src} p.{page}: {doc.page_content[:100]}...")

