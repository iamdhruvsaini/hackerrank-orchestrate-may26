import sys
from pathlib import Path

# Add the repository root to the python path so absolute imports like `from code.retrieval` work natively
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

try:
    from code.agent import run_agent
except ModuleNotFoundError as e:
    print(f"Error: Could not import 'agent.py'. Reason: {e}")
    sys.exit(1)

def test_full_pipeline():
    print("==================================================")
    print("           TESTING FULL AGENT PIPELINE            ")
    print("==================================================")
    
    # Mocking a realistic scenario: HackerRank issue
    issue_text = "I made changes to Test content. When does it take effect for the Candidates?"
    subject = "Updates to test content"
    company = "HackerRank"
    
    print("\n[Running Agent on Valid Query]")
    output = run_agent(issue=issue_text, subject=subject, company=company)
    
    print("\n--- Final Structured Output ---")
    import json
    print(json.dumps(output, indent=2))
    
    # Ensure keys exist
    assert "status" in output
    assert "product_area" in output
    assert "response" in output
    assert "justification" in output
    assert "request_type" in output
    
    print("\n[Running Agent on Out-Of-Scope Query]")
    output2 = run_agent(issue="How do I boil an egg?", subject="Cooking", company="Visa")
    print("\n--- Final Structured Output ---")
    print(json.dumps(output2, indent=2))
    
    assert output2["status"] == "escalated"
    
    print("\n==================================================")
    print("                TESTS COMPLETED                   ")
    print("==================================================")

if __name__ == "__main__":
    test_full_pipeline()
