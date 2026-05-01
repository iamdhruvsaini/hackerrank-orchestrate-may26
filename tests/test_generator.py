import sys
from pathlib import Path

# Add the 'code' directory to python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "code"))

try:
    import generator
except ModuleNotFoundError:
    print("Error: Could not import 'generator.py' from the code folder.")
    sys.exit(1)

def test_generator():
    print("==================================================")
    print("         TESTING DETERMINISTIC GENERATOR          ")
    print("==================================================")
    
    # Mock data for test 1 (empty results)
    decision1 = {
        "status": "escalated",
        "escalation_level": "medium",
        "decision_confidence": 0.8,
        "signals": {
            "urgency": 0, "risk": 0, "sentiment": 0, "retrieval_confidence": 0.0
        }
    }
    
    res1 = generator.generate(
        text="I need help with X", 
        request_type="general_inquiry", 
        product_area="Unknown Product", 
        decision_output=decision1, 
        retrieval_results=[]
    )
    
    print("\n[Test 1] Empty Retrieval")
    print("Response:\n", res1["response"])
    print("\nJustification:\n", res1["justification"])
    
    # Mock data for test 2 (valid results)
    decision2 = {
        "status": "replied",
        "escalation_level": "low",
        "decision_confidence": 0.95,
        "signals": {
            "urgency": 0, "risk": 0, "sentiment": 0, "retrieval_confidence": 0.92
        }
    }
    
    results2 = [
        {"text": "This is the first sentence about tests. Tests are active for 6 months.\nThis is a third sentence.", "source": "docs/tests.md"},
        {"text": "Candidates can view their scores after completion. The platform supports multiple languages.", "source": "docs/candidates.md"}
    ]
    
    res2 = generator.generate(
        text="How long do tests stay active?", 
        request_type="feature_query", 
        product_area="Assessments", 
        decision_output=decision2, 
        retrieval_results=results2
    )
    
    print("\n--------------------------------------------------\n")
    print("[Test 2] Valid Retrieval")
    print("Response:\n", res2["response"])
    print("\nJustification:\n", res2["justification"])
    
    print("\n==================================================")
    print("                TESTS COMPLETED                   ")
    print("==================================================")

if __name__ == "__main__":
    test_generator()
