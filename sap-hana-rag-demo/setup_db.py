import sys
import os

# Set path based on script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from ingest import load_pdfs, split_documents
from vectorstore import get_connection, ingest_documents

def main():
    print("=== SAP HANA Cloud RAG: Vector DB Initialization Script ===")
    
    data_dir = os.path.join(BASE_DIR, 'data', 'raw')
    if not os.path.exists(data_dir):
        print(f"Error: {data_dir} directory not found.")
        return

    # 1. Load PDFs
    print("\n[Step 1] Loading PDFs...")
    try:
        docs = load_pdfs(data_dir)
    except Exception as e:
        print(f"PDF loading error: {e}")
        return

    # 2. Split documents into chunks
    print("\n[Step 2] Splitting documents into chunks...")
    chunks = split_documents(docs)

    # 3. Store vectors in HANA DB
    print("\n[Step 3] Storing vectors in HANA DB...")
    try:
        conn = get_connection()
        ingest_documents(chunks, conn)
        print("\nVector DB initialization completed!")
        print("You can now run `python chat.py` to try the RAG system.")
    except Exception as e:
        print(f"\nError occurred: {e}")

if __name__ == '__main__':
    main()
