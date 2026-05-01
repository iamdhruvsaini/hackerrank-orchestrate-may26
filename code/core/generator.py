import re
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables from repo root
dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()

def clean_text(text: str) -> str:
    """
    Strips YAML frontmatter, markdown, and URLs from text.
    """
    # 1. Remove YAML frontmatter if present at the start
    text = re.sub(r'(?s)^\s*---.*?---\s*', '', text)
    
    # Process line by line to remove noisy content
    lines = text.split('\n')
    clean_lines = []
    noisy_keywords = [
        "last_modified", "source_url", "final_url", "download", 
        "last updated", "title:", "title_slug:", "article_slug:", 
        "breadcrumbs:"
    ]
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in noisy_keywords):
            continue
        clean_lines.append(line)
    
    text = " ".join(clean_lines)
    
    # 2. Remove markdown links: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 3. Remove raw URLs completely
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # 4. Remove markdown styling artifacts (bold, italics, headers, blockquotes, etc)
    text = re.sub(r'[*_~`#>]', '', text)
    
    # 5. Remove table formatting artifacts
    text = re.sub(r'\|', ' ', text)
    
    # 6. Collapse multiple spaces and newlines into a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_sentences(text: str, max_sentences: int = 3) -> str:
    """
    Splits text by sentence boundaries and extracts top meaningful sentences.
    """
    # Split using proper sentence boundaries (. ! ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    valid_sentences = []
    seen = set()
    
    for s in sentences:
        s = s.strip()
        # Ensure sentence ends with punctuation
        if s and not re.search(r'[.!?]$', s):
            s += "."
            
        # Filter sentences > 40 chars
        if len(s) > 40 and s not in seen:
            if "colgroup" not in s and "tbody" not in s and "td " not in s and "tr " not in s:
                valid_sentences.append(s)
                seen.add(s)
        
        if len(valid_sentences) >= max_sentences:
            break
            
    if not valid_sentences:
        return ""
        
    return " ".join(valid_sentences)

def generate_justification(request_type: str, product_area: str, decision_output: dict) -> str:
    status = decision_output.get("status", "unknown").lower()
    signals = decision_output.get("signals", {})
    
    risk_val = signals.get('risk', 0)
    urgency_val = signals.get('urgency', 0)
    conf_val = float(signals.get('retrieval_confidence', 0.0))
    
    risk_level = "high" if risk_val >= 2 else "low"
    urgency_level = "high" if urgency_val >= 1 else "low"
    conf_level = "high" if conf_val >= 0.5 else ("medium" if conf_val >= 0.3 else "low")
    
    decision_text = "a direct response was provided" if status == "replied" else "the ticket was escalated for further assistance"
    conf_text = "sufficient confidence" if conf_level in ["high", "medium"] else "low confidence"
    
    justification = (
        f"The request was classified as {request_type} related to {product_area}. "
        f"Relevant support documentation was retrieved with {conf_text}. "
        f"Risk was assessed as {risk_level} and urgency as {urgency_level}, "
        f"so {decision_text}."
    )
    
    return justification

def generate_deterministic(text: str, request_type: str, product_area: str, decision_output: dict, retrieval_results: list) -> dict:
    """
    Deterministic response generator that builds a single-line CSV-safe response 
    and justification.
    """
    status = decision_output.get("status", "unknown").lower()
    
    # 1. Generate user-facing response
    if status == "escalated" or not retrieval_results:
        response = "Your request cannot be fully resolved using the available support documentation. It has been escalated to a support specialist for further assistance."
    else:
        top_chunks = retrieval_results[:2]
        extracted_info = []
        
        for chunk in top_chunks:
            chunk_text = chunk.get("text", "")
            cleaned_text = clean_text(chunk_text)
            summary_sentences = extract_sentences(cleaned_text, max_sentences=2)
            
            if summary_sentences:
                extracted_info.append(summary_sentences)
                
        # Deduplicate
        final_summary_parts = []
        for info in extracted_info:
            if info not in final_summary_parts:
                final_summary_parts.append(info)
                
        summary = " ".join(final_summary_parts)
        
        if not summary.strip():
            response = "Your request cannot be fully resolved using the available support documentation. It has been escalated to a support specialist for further assistance."
        else:
            response = f"Your request relates to {product_area}. According to the support documentation, {summary}"

    # 2. Generate judge-facing justification
    justification = generate_justification(request_type, product_area, decision_output)
    
    # Ensure no newlines are present in the final strings
    response = response.replace('\n', ' ').replace('\r', ' ').strip()
    justification = justification.replace('\n', ' ').replace('\r', ' ').strip()
    
    # Collapse multiple spaces just in case
    response = re.sub(r'\s+', ' ', response)
    justification = re.sub(r'\s+', ' ', justification)
    
    # 3. Output format
    return {
        "response": response,
        "justification": justification,
        "product_area": product_area
    }


def generate(text: str, request_type: str, product_area: str, decision_output: dict, retrieval_results: list) -> dict:
    """
    Uses the Groq LLM API to generate a highly natural, empathetic response grounded strictly 
    in the RAG chunks. Fails back to deterministic string formatting if the API call fails or 
    key is missing.
    """
    status = decision_output.get("status", "unknown").lower()
    
    # Immediately fallback if we are already escalating, as the standard escalation 
    # message is perfectly safe and concise.
    if status == "escalated" or not retrieval_results:
        return generate_deterministic(text, request_type, product_area, decision_output, retrieval_results)
        
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[Generator] GROQ_API_KEY not found. Defaulting to deterministic generation.")
        return generate_deterministic(text, request_type, product_area, decision_output, retrieval_results)
        
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        # Prepare context from retrieved chunks
        context_chunks = []
        for doc in retrieval_results[:2]:
            cleaned_doc = clean_text(doc.get("text", ""))
            context_chunks.append(cleaned_doc)
            
        context_str = "\n\n---\n\n".join(context_chunks)
        
        system_prompt = (
            "You are a helpful, professional customer support agent. Your goal is to reply to the user's inquiry "
            "using ONLY the provided reference documentation.\n\n"
            "RULES:\n"
            "1. Answer the user's question directly, clearly, and concisely (2-4 sentences max).\n"
            "2. Do NOT use markdown formatting like bolding, italics, or lists.\n"
            "3. Do NOT include any URLs or file paths.\n"
            "4. NEVER hallucinate information. If the answer is not in the documentation, state that you cannot help.\n"
            "5. Determine the most specific Product Area (e.g., 'Screening', 'Privacy', 'Billing', 'Card Limits') based on the context.\n"
            "6. Provide a clear, objective internal justification of the support decision in a single paragraph for the judge.\n"
            "7. Output EXACTLY in valid JSON format: {\"response\": \"your response string\", \"product_area\": \"string\", \"justification\": \"your justification string\"}"
        )
        
        user_prompt = f"User Ticket:\n{text}\n\nSupport Documentation:\n{context_str}"
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        content = chat_completion.choices[0].message.content
        result_json = json.loads(content)
        
        llm_response = result_json.get("response", "").replace('\n', ' ').replace('\r', ' ').strip()
        llm_product_area = result_json.get("product_area", product_area).strip()
        llm_justification = result_json.get("justification", "").replace('\n', ' ').replace('\r', ' ').strip()
        
        # If the LLM failed to produce a valid response, fallback
        if not llm_response:
            raise ValueError("Empty response from LLM")
            
        # Compute standard justification as a fallback if LLM omitted it
        if not llm_justification:
            llm_justification = generate_justification(request_type, llm_product_area, decision_output)
            llm_justification = llm_justification.replace('\n', ' ').replace('\r', ' ').strip()
        
        # Collapse multiple spaces
        llm_response = re.sub(r'\s+', ' ', llm_response)
        llm_justification = re.sub(r'\s+', ' ', llm_justification)
        
        return {
            "response": llm_response,
            "justification": llm_justification,
            "product_area": llm_product_area
        }
        
    except Exception as e:
        print(f"[Generator] Groq API failed ({e}). Defaulting to deterministic generation.")
        return generate_deterministic(text, request_type, product_area, decision_output, retrieval_results)
