import sys
from pathlib import Path

# Add the 'code' directory to python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "code"))

try:
    import decision
except ModuleNotFoundError:
    print("Error: Could not import 'decision.py' from the code folder.")
    sys.exit(1)

def test_decision():
    print("==================================================")
    print("         TESTING DETERMINISTIC DECISION           ")
    print("==================================================")
    
    # Scenario 1: High risk / blocked ticket
    test1 = decision.make_decision("Urgent refund needed for an unauthorized payment", [], 0.5)
    print(f"\nTest 1 (Unauthorized refund request):\n  Result: {test1}")
    assert test1["status"] == "escalated"
    
    # Scenario 2: Safe ticket with good confidence
    test2 = decision.make_decision("How can I change my email address?", [{"text": "Change email procedure..."}], 0.85)
    print(f"\nTest 2 (Routine question with high confidence):\n  Result: {test2}")
    assert test2["status"] == "replied"
    
    # Scenario 3: Ticket with low confidence retrieval
    test3 = decision.make_decision("How can I download usage history?", [], 0.31)
    print(f"\nTest 3 (Low confidence query):\n  Result: {test3}")
    assert test3["status"] == "escalated"

    print("\n==================================================")
    print("                TESTS COMPLETED                   ")
    print("==================================================")

if __name__ == "__main__":
    test_decision()
