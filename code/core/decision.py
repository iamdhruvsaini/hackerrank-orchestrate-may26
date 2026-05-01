def make_decision(text: str, retrieval_results: list, retrieval_confidence: float):
    """
    Refined deterministic scoring-based decision system that classifies an 
    incoming support ticket, extracts linguistic signals, and makes explainable
    triage decisions.
    """
    text_lower = (text or "").lower()
    
    # STEP 1: Compute scores via keyword matching
    urgency_words = ["urgent", "asap", "immediately", "now", "blocked"]
    urgency_score = sum(1 for w in urgency_words if w in text_lower)
    
    risk_words = ["refund", "fraud", "payment", "billing", "unauthorized", "ban"]
    risk_score = sum(1 for w in risk_words if w in text_lower)
    
    sentiment_words = ["angry", "frustrated", "issue", "problem"]
    sentiment_score = sum(1 for w in sentiment_words if w in text_lower)
    
    # CRITICAL ESCALATION OVERRIDES (BEFORE NORMAL SCORING)
    access_words = ["access removed", "admin", "permission", "restore access"]
    system_words = ["increase score", "change result", "override system"]
    finance_words = ["refund", "fraud", "unauthorized", "ban"]
    
    if any(w in text_lower for w in access_words + system_words + finance_words):
        return {
            "status": "escalated",
            "escalation_level": "high",
            "decision_confidence": 1.0, # High confidence due to explicit override match
            "signals": {
                "urgency": urgency_score,
                "risk": risk_score,
                "sentiment": sentiment_score,
                "retrieval_confidence": retrieval_confidence
            }
        }
    
    # STEP 2: Combine scores with a weighted sum
    urgency_weight = 0.4
    risk_weight = 0.4
    sentiment_weight = 0.2
    
    escalation_score = (urgency_score * urgency_weight) + \
                       (risk_score * risk_weight) + \
                       (sentiment_score * sentiment_weight)
                       
    # Combine with retrieval_confidence when in the 0.3–0.5 zone
    if 0.3 <= retrieval_confidence <= 0.5:
        # Lower confidence increases escalation score penalty
        escalation_score += float(0.5 - retrieval_confidence)

    # STEP 3 & 4: Decision logic and Escalation level determination
    status = "replied"
    escalation_level = "low"
    
    is_very_low_confidence = retrieval_confidence < 0.3
    is_strong_risk = risk_score >= 2
    is_out_of_scope = not retrieval_results
    is_high_combined = escalation_score >= 0.8
    is_strong_risk_override = risk_score >= 1
    
    # Status determination rules
    if is_very_low_confidence or is_strong_risk or is_out_of_scope or is_high_combined or is_strong_risk_override:
        status = "escalated"

    # Escalation level determination
    # high: strong risk or very low confidence
    if is_strong_risk or is_very_low_confidence:
        escalation_level = "high"
    # medium: combined score > threshold or moderate risk or out of scope
    elif is_high_combined or is_out_of_scope or is_strong_risk_override:
        escalation_level = "medium"
    else:
        escalation_level = "low"
        
    # Compute decision confidence score
    if status == "replied":
        decision_confidence = float(max(0.0, min(1.0, retrieval_confidence)))
    else:
        normalized_escalation = float(min(1.0, escalation_score / 3.0))
        decision_confidence = float(max(retrieval_confidence, normalized_escalation))
        
    return {
        "status": status,
        "escalation_level": escalation_level,
        "decision_confidence": round(decision_confidence, 4),
        "signals": {
            "urgency": urgency_score,
            "risk": risk_score,
            "sentiment": sentiment_score,
            "retrieval_confidence": retrieval_confidence
        }
    }
