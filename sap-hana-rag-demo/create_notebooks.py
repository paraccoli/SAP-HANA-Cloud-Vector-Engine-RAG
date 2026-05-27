import json
import os

def create_notebook(filename, cells):
    nb = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.11"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    for cell_type, source in cells:
        cell = {
            "cell_type": cell_type,
            "metadata": {},
            "source": [line + "\n" for line in source.split("\n")]
        }
        if cell_type == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        cell["source"] = [line if i < len(cell["source"])-1 else line.rstrip('\n') for i, line in enumerate(cell["source"])]
        if not cell["source"] or cell["source"] == [""]:
            cell["source"] = []
        nb["cells"].append(cell)
        
    with open(filename, "w") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)

os.makedirs("notebooks", exist_ok=True)

# 01_ingest.ipynb
cells_01 = [
    ("markdown", "# Step 1: Document Ingest and Text Splitting\nHere we load PDF data and split it into chunks of appropriate sizes."),
    ("code", "import sys\nimport os\nsys.path.append(os.path.abspath('../src'))\nfrom ingest import load_pdfs, split_documents, preview_chunks"),
    ("code", "# Load PDFs from data/raw directory\ndocs = load_pdfs('../data/raw')"),
    ("code", "# Split into chunks\nchunks = split_documents(docs)\npreview_chunks(chunks)")
]
create_notebook("notebooks/01_ingest.ipynb", cells_01)

# 02_vectorstore.ipynb
cells_02 = [
    ("markdown", "# Step 2: Vector Storage in SAP HANA Cloud\nStore the chunked data into SAP HANA Cloud Vector Store."),
    ("code", "import sys\nimport os\nsys.path.append(os.path.abspath('../src'))\nfrom ingest import load_pdfs, split_documents\nfrom vectorstore import get_connection, ingest_documents\n\n# Re-run preprocessing (keep in memory)\ndocs = load_pdfs('../data/raw')\nchunks = split_documents(docs)"),
    ("code", "# Connect to HANA DB\nconn = get_connection()"),
    ("code", "# Store into Vector Store\nvectorstore = ingest_documents(chunks, conn)\nprint('Vector DB setup completed!')")
]
create_notebook("notebooks/02_vectorstore.ipynb", cells_02)

# 03_rag_pipeline.ipynb
cells_03 = [
    ("markdown", "# Step 3: RAG Chain Build and Demo\nBuild the RAG pipeline to search relevant documents from HANA DB for a query and generate responses using LLM."),
    ("code", "import sys\nimport os\nsys.path.append(os.path.abspath('../src'))\nfrom vectorstore import get_connection, get_vectorstore\nfrom rag import build_rag_chain, query_with_latency, print_result\n\nconn = get_connection()\nvectorstore = get_vectorstore(conn)"),
    ("code", "# Build RAG chain\nqa_chain = build_rag_chain(vectorstore, k=3)"),
    ("code", "# Test query\nquery = 'What are the main features of SAP HANA Cloud?'\nresult = query_with_latency(qa_chain, query)\nprint_result(result)")
]
create_notebook("notebooks/03_rag_pipeline.ipynb", cells_03)

# 04_benchmark.ipynb
cells_04 = [
    ("markdown", "# Step 4: Benchmark Evaluation Experiment\\nHere we evaluate the performance of the RAG system built so far.\\nWe compare the following:\\n1. Baseline A: Keyword search (BM25)\\n2. Baseline B: Vector search only\\n3. Proposed method: Vector search + RAG (gemini-3.5-flash)"),
    ("code", "import sys\\nimport os\\nsys.path.append(os.path.abspath('../src'))\\nfrom evaluate import run_benchmark"),
    ("code", "# Run benchmark experiment\\nrun_benchmark()"),
    ("markdown", "## Review Evaluation Results\\nThe experiment results are saved in `results/benchmark_results.csv` and comparison charts are generated under `results/figures/`."),
    ("code", "import pandas as pd\\nimport matplotlib.pyplot as plt\\n\\ndf = pd.read_csv('../results/benchmark_results.csv')\\ndisplay(df.head())")
]
create_notebook("notebooks/04_benchmark.ipynb", cells_04)

