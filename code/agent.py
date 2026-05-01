from code.core.retrieval import retrieve
from code.core.decision import make_decision
from code.core.generator import generate

def classify(text: str, company: str):
    """
    Deterministic rule-based classifier that returns the request type, 
    product area, and an estimated confidence score without external APIs.
    """
    text_lower = text.lower()
    
    if "bug" in text_lower or "error" in text_lower or "crash" in text_lower or "fail" in text_lower:
        request_type = "bug"
    elif "feature" in text_lower or "add" in text_lower or "enhance" in text_lower:
        request_type = "feature_request"
    elif "spam" in text_lower or "junk" in text_lower or "nonsense" in text_lower:
        request_type = "invalid"
    else:
        request_type = "product_issue"
        
    product_area = company if company else "General Support"
    confidence_score = 0.85
    return request_type, product_area, confidence_score

def run_agent(issue: str, subject: str, company: str) -> dict:
    """
    Main pipeline entry point that sequentially orchestrates retrieval,
    decision making, and generation modules deterministically.
    """
    # 1. Prepare text
    text = f"{subject} {issue}".strip()
    
    # 2. Classifier output
    request_type, product_area, confidence_score = classify(text, company)
    
    # 3. Retrieval results
    retrieval_res = retrieve(query=text, company=company)
    
    # safely handle the custom list wrapper returning the confidence
    retrieval_results = list(retrieval_res)
    retrieval_confidence = getattr(retrieval_res, "retrieval_confidence", 0.0)
    
    # 4. Decision output
    decision_output = make_decision(
        text=text,
        retrieval_results=retrieval_results,
        retrieval_confidence=retrieval_confidence
    )
    
    # 5. Generator output
    generator_output = generate(
        text=text,
        request_type=request_type,
        product_area=product_area,
        decision_output=decision_output,
        retrieval_results=retrieval_results
    )
    
    # Final Strict Output Format
    final_output = {
        "status": decision_output["status"],
        "product_area": generator_output.get("product_area", product_area),
        "response": generator_output["response"],
        "justification": generator_output["justification"],
        "request_type": request_type
    }
    
    return final_output
