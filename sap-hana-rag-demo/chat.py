import sys
import os

# Set path based on script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from vectorstore import get_connection, get_vectorstore
from rag import build_rag_chain, query_with_latency, print_result

def main():
    print("=== SAP HANA Cloud RAG: Interactive Chat ===")
    print("Connecting to HANA DB...")
    
    try:
        conn = get_connection()
        vectorstore = get_vectorstore(conn)
        qa_chain = build_rag_chain(vectorstore, k=3)
    except Exception as e:
        print(f"Initialization error: {e}")
        print("Please run `python setup_db.py` first to set up the database.")
        return

    print("\nReady! Please ask questions to the RAG system.")
    print("(Type 'exit' or 'quit' to exit)")
    
    while True:
        try:
            query = input("\nYou: ")
            if query.lower() in ['exit', 'quit']:
                print("Exiting chat. Goodbye!")
                break
            if not query.strip():
                continue
                
            print("AI is generating response...")
            result = query_with_latency(qa_chain, query)
            print_result(result)
            
        except KeyboardInterrupt:
            print("\nExiting chat.")
            break
        except Exception as e:
            print(f"\nError occurred: {e}")

if __name__ == '__main__':
    main()
