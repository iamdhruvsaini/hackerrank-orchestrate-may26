import sys
from pathlib import Path

# Add the 'code' directory to python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "code"))

try:
    import retrieval
except ModuleNotFoundError:
    print("Error: Could not import 'retrieval.py' from the code folder.")
    sys.exit(1)

def main():
    print("==================================================")
    print("         TESTING LOCAL RAG RETRIEVAL              ")
    print("==================================================")
    
    # Initialize the retrieval system
    print("\n[Step 1] Initializing retrieval (loading data & cache)...")
    retrieval.init_retrieval()
    print("Success: Data loaded and semantic search is ready!")

    # Test query 1: HackerRank
    print("\n[Step 2] Testing HackerRank specific query:")
    query_1 = "how long tests stay active in the system"
    print(f"Query: '{query_1}'")
    results_1 = retrieval.retrieve(query_1, top_k=2)
    
    for idx, match in enumerate(results_1):
        print(f"  Match {idx+1}:")
        print(f"    Source : {match['source']}")
        print(f"    Company: {match['company']}")
        print(f"    Text   : {match['text'][:120]}...\n")

    # Test query 2: Visa
    print("\n[Step 3] Testing Visa specific query:")
    query_2 = "Citibank travellers cheques stolen Lisbon"
    print(f"Query: '{query_2}'")
    results_2 = retrieval.retrieve(query_2, top_k=1)
    
    for idx, match in enumerate(results_2):
        print(f"  Match {idx+1}:")
        print(f"    Source : {match['source']}")
        print(f"    Company: {match['company']}")
        print(f"    Text   : {match['text'][:120]}...\n")

    # Test query 3: Empty string
    print("\n[Step 4] Testing out-of-scope / empty string:")
    results_3 = retrieval.retrieve("", top_k=2)
    print(f"  Results returned: {len(results_3)} (Expected: 0)")
    
    print("\n==================================================")
    print("                TESTS COMPLETED                   ")
    print("==================================================")

if __name__ == "__main__":
    main()
