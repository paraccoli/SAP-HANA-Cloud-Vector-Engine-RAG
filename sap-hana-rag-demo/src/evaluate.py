"""
evaluate.py - RAG System Benchmark Evaluation Module
Corresponding to Step 5 of the proposal

Comparison methods:
1. Baseline A: Keyword search (BM25)
2. Baseline B: Vector search only (using Top-1 document as the answer)
3. Proposed method: Vector search + RAG (gemini-3.5-flash)

Evaluation metrics:
- Hit Rate @3 (document level / page level)
- MRR @3
- Average latency (ms)
- Cost (converted to Yen per query)
"""
import os
import sys
import json
import time
import re
from typing import List, Dict, Any

import pandas as pd
import matplotlib.pyplot as plt
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from hdbcli import dbapi

# Path settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from vectorstore import get_connection, get_vectorstore
from rag import build_rag_chain, query_with_latency

# Cost calculation constants (assuming Gemini 3.5 Flash pricing: $1 = 150 Yen)
# Input: $0.075 / 1M tokens -> 0.00001125 Yen / token
# Output: $0.30 / 1M tokens -> 0.000045 Yen / token
COST_PER_INPUT_TOKEN = (0.075 / 1000000) * 150
COST_PER_OUTPUT_TOKEN = (0.30 / 1000000) * 150


def tokenize(text: str) -> List[str]:
    """Simple tokenizer for Japanese and English mixed text"""
    tokens = []
    # Alphanumeric words
    en_words = re.findall(r'[a-zA-Z0-9_]+', text)
    tokens.extend([w.lower() for w in en_words])
    # Japanese characters (Hiragana, Katakana, Kanji)
    jp_chars = re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text)
    tokens.extend(jp_chars)
    return tokens if tokens else [""]


class BM25Searcher:
    """Class to perform BM25 search from HANA DB text data"""
    def __init__(self, conn: dbapi.Connection, table_name: str = "SAP_RAG_DOCS"):
        self.conn = conn
        self.table_name = table_name
        self.documents: List[Document] = []
        self.bm25: BM25Okapi = None
        self._initialize_index()

    def _initialize_index(self):
        print("  Loading all text data from HANA DB...")
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT VEC_TEXT, VEC_META FROM {self.table_name}")
        rows = cursor.fetchall()
        
        corpus_tokens = []
        for row in rows:
            text = row[0]
            meta = json.loads(row[1])
            doc = Document(page_content=text, metadata=meta)
            self.documents.append(doc)
            corpus_tokens.append(tokenize(text))
            
        print(f"  Registered {len(self.documents)} chunks in BM25 index.")
        self.bm25 = BM25Okapi(corpus_tokens)

    def search(self, query: str, k: int = 3) -> List[Document]:
        """Execute BM25 similarity search"""
        query_tokens = tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
        # Sort by score in descending order and return Top-k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            # Record score in metadata
            doc.metadata["score"] = float(scores[idx])
            results.append(doc)
        return results


def calculate_metrics(retrieved_docs: List[Document], expected_source: str, expected_page: int) -> Dict[str, Any]:
    """Calculate Hit Rate and MRR"""
    doc_hit = 0
    page_hit = 0
    doc_mrr = 0.0
    page_mrr = 0.0
    
    # Document-level evaluation
    for idx, doc in enumerate(retrieved_docs):
        src = doc.metadata.get("source_file", "")
        if src == expected_source:
            doc_hit = 1
            doc_mrr = 1.0 / (idx + 1)
            break
            
    # Page-level evaluation
    for idx, doc in enumerate(retrieved_docs):
        src = doc.metadata.get("source_file", "")
        page = doc.metadata.get("page", -99)
        # cast page as it might be int or string
        try:
            page_int = int(page)
        except:
            page_int = -99
            
        if src == expected_source and page_int == expected_page:
            page_hit = 1
            page_mrr = 1.0 / (idx + 1)
            break
            
    return {
        "doc_hit": doc_hit,
        "page_hit": page_hit,
        "doc_mrr": doc_mrr,
        "page_mrr": page_mrr
    }


def run_benchmark():
    print("=== SAP HANA Cloud RAG Benchmark Evaluation ===")
    
    # 1. Connection & Data Load
    conn = get_connection()
    vectorstore = get_vectorstore(conn)
    bm25_searcher = BM25Searcher(conn)
    qa_chain = build_rag_chain(vectorstore, k=3, model="gemini-3.5-flash")
    
    # 2. Load QA Test Set
    qa_path = os.path.join(BASE_DIR, "data", "qa_testset.json")
    if not os.path.exists(qa_path):
        print(f"Error: {qa_path} not found.")
        return
        
    with open(qa_path, "r", encoding="utf-8") as f:
        qa_set = json.load(f)
        
    print(f"Loaded QA Test Set: {len(qa_set)} questions.")
    
    results = []
    
    # Sleep between requests to avoid API rate limit
    sleep_time = 4.0
    
    for qa in qa_set:
        qid = qa["id"]
        query = qa["query"]
        expected_src = qa["expected_source"]
        expected_pg = qa["expected_page"]
        
        print(f"\n[Q {qid}/20] {query[:40]}...")
        
        # --- Baseline A: Keyword search (BM25) ---
        t0 = time.time()
        bm25_docs = bm25_searcher.search(query, k=3)
        latency_bm25 = (time.time() - t0) * 1000
        metrics_bm25 = calculate_metrics(bm25_docs, expected_src, expected_pg)
        
        # --- Baseline B: Vector search only ---
        t0 = time.time()
        vec_docs = vectorstore.similarity_search(query, k=3)
        latency_vec = (time.time() - t0) * 1000
        metrics_vec = calculate_metrics(vec_docs, expected_src, expected_pg)
        
        # --- Proposed method: Vector search + RAG ---
        time.sleep(sleep_time)
        
        t0 = time.time()
        try:
            rag_res = query_with_latency(qa_chain, query)
            latency_rag = rag_res["latency_ms"]
            rag_docs = rag_res["source_documents"]
            metrics_rag = calculate_metrics(rag_docs, expected_src, expected_pg)
            
            # Cost calculation
            input_tokens = len(query) + sum(len(d.page_content) for d in rag_docs)
            output_tokens = len(rag_res["answer"])
            cost_rag = (input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN)
        except Exception as e:
            print(f"  RAG error occurred (skipping): {e}")
            latency_rag = 0
            metrics_rag = {"doc_hit": 0, "page_hit": 0, "doc_mrr": 0.0, "page_mrr": 0.0}
            cost_rag = 0.0
            
        # Record results
        results.append({
            "id": qid,
            "query": query,
            "expected_source": expected_src,
            "expected_page": expected_pg,
            # BM25
            "bm25_doc_hit": metrics_bm25["doc_hit"],
            "bm25_page_hit": metrics_bm25["page_hit"],
            "bm25_doc_mrr": metrics_bm25["doc_mrr"],
            "bm25_page_mrr": metrics_bm25["page_mrr"],
            "bm25_latency": round(latency_bm25, 1),
            # Vector Only
            "vec_doc_hit": metrics_vec["doc_hit"],
            "vec_page_hit": metrics_vec["page_hit"],
            "vec_doc_mrr": metrics_vec["doc_mrr"],
            "vec_page_mrr": metrics_vec["page_mrr"],
            "vec_latency": round(latency_vec, 1),
            # RAG
            "rag_doc_hit": metrics_rag["doc_hit"],
            "rag_page_hit": metrics_rag["page_hit"],
            "rag_doc_mrr": metrics_rag["doc_mrr"],
            "rag_page_mrr": metrics_rag["page_mrr"],
            "rag_latency": round(latency_rag, 1),
            "rag_cost_yen": round(cost_rag, 5)
        })
        
        # Display progress
        print(f"  BM25  - DocHit: {metrics_bm25['doc_hit']}, Latency: {latency_bm25:.1f}ms")
        print(f"  Vector- DocHit: {metrics_vec['doc_hit']}, Latency: {latency_vec:.1f}ms")
        print(f"  RAG   - DocHit: {metrics_rag['doc_hit']}, Latency: {latency_rag:.1f}ms, Cost: {cost_rag:.5f} Yen")

    # 3. Aggregate & Save CSV
    df = pd.DataFrame(results)
    csv_path = os.path.join(BASE_DIR, "results", "benchmark_results.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved evaluation results to CSV: {csv_path}")
    
    summary = {
        "BM25 (Doc Hit)": df["bm25_doc_hit"].mean(),
        "BM25 (Page Hit)": df["bm25_page_hit"].mean(),
        "BM25 (Doc MRR)": df["bm25_doc_mrr"].mean(),
        "BM25 Latency (ms)": df["bm25_latency"].mean(),
        "Vector (Doc Hit)": df["vec_doc_hit"].mean(),
        "Vector (Page Hit)": df["vec_page_hit"].mean(),
        "Vector (Doc MRR)": df["vec_doc_mrr"].mean(),
        "Vector Latency (ms)": df["vec_latency"].mean(),
        "RAG (Doc Hit)": df["rag_doc_hit"].mean(),
        "RAG (Page Hit)": df["rag_page_hit"].mean(),
        "RAG (Doc MRR)": df["rag_doc_mrr"].mean(),
        "RAG Latency (ms)": df["rag_latency"].mean(),
        "RAG Cost (Yen)": df["rag_cost_yen"].mean(),
    }
    
    print("\n=== Benchmark Summary ===")
    for k, v in summary.items():
        print(f"  {k:20}: {v:.4f}")
        
    # 4. Visualization (Plotting)
    plot_benchmark_results(summary)
    
    conn.close()


def plot_benchmark_results(summary: Dict[str, float]):
    """Create and save bar charts to compare results"""
    methods = ["Baseline A\n(BM25)", "Baseline B\n(Vector Only)", "Proposed\n(RAG)"]
    
    # 1. Hit Rate & MRR Plot
    doc_hit_rates = [summary["BM25 (Doc Hit)"], summary["Vector (Doc Hit)"], summary["RAG (Doc Hit)"]]
    page_hit_rates = [summary["BM25 (Page Hit)"], summary["Vector (Page Hit)"], summary["RAG (Page Hit)"]]
    mrr_scores = [summary["BM25 (Doc MRR)"], summary["Vector (Doc MRR)"], summary["RAG (Doc MRR)"]]
    
    plt.figure(figsize=(10, 5))
    x = range(len(methods))
    width = 0.25
    
    plt.bar([i - width for i in x], doc_hit_rates, width, label="Hit Rate @3 (Doc)", color="#3498db")
    plt.bar(x, page_hit_rates, width, label="Hit Rate @3 (Page)", color="#2ecc71")
    plt.bar([i + width for i in x], mrr_scores, width, label="MRR @3 (Doc)", color="#e74c3c")
    
    plt.xticks(x, methods)
    plt.ylabel("Score")
    plt.ylim(0, 1.1)
    plt.title("Search Accuracy Comparison (BM25 vs. Vector vs. RAG)")
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    fig_dir = os.path.join(BASE_DIR, "results", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    accuracy_plot_path = os.path.join(fig_dir, "accuracy_comparison.png")
    plt.savefig(accuracy_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    # 2. Latency Plot
    latencies = [summary["BM25 Latency (ms)"], summary["Vector Latency (ms)"], summary["RAG Latency (ms)"]]
    plt.figure(figsize=(8, 4))
    bars = plt.bar(methods, latencies, color=["#95a5a6", "#34495e", "#9b59b6"], width=0.5)
    plt.ylabel("Latency (ms)")
    plt.title("Average Latency Comparison")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Display values on top of the bars
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.1f} ms',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
                    
    latency_plot_path = os.path.join(fig_dir, "latency_comparison.png")
    plt.savefig(latency_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved graph image: {accuracy_plot_path}")
    print(f"Saved graph image: {latency_plot_path}")


if __name__ == "__main__":
    run_benchmark()
