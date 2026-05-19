"""
rag.py - RAG パイプラインモジュール
企画書 Step 4 に対応（03_rag_pipeline.ipynb のバックエンド）
LLM: Google Gemini 1.5 Flash（コスト重視）
"""
import os
import time
from typing import Dict, Any, Optional

from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_hana import HanaDB
from dotenv import load_dotenv

load_dotenv()

# Gemini LLM モデル（無料枠あり / コスト重視）
DEFAULT_LLM_MODEL = "gemini-1.5-flash"


def build_rag_chain(
    vectorstore: HanaDB,
    k: int = 3,
    model: str = DEFAULT_LLM_MODEL,
    temperature: float = 0,
) -> RetrievalQA:
    """RAG チェーンを構築する（企画書 Step 4 準拠）"""
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
    print(f"✅ RAG チェーン構築完了（Top-{k}, model={model}）")
    return qa_chain


def query_with_latency(
    qa_chain: RetrievalQA,
    query: str,
) -> Dict[str, Any]:
    """クエリを実行し、レイテンシも計測する"""
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
    """結果を整形して表示"""
    print(f"\n{'='*60}")
    print(f"Q: {result['query']}")
    print(f"{'='*60}")
    print(f"A: {result['answer']}")
    print(f"\nレイテンシ: {result['latency_ms']} ms")
    print(f"\n--- 参照ソース ---")
    for i, doc in enumerate(result["source_documents"], 1):
        src = doc.metadata.get("source_file", "unknown")
        page = doc.metadata.get("page", "?")
        print(f"  [{i}] {src} p.{page}: {doc.page_content[:100]}...")
