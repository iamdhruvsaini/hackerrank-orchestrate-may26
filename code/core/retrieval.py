import os
import pickle
from pathlib import Path
import numpy as np

# Global variables for caching in memory
_chunks = None
_embeddings = None
_model = None

CACHE_FILE = Path(__file__).parent / "retrieval_cache.pkl"
CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "data"

class RetrievalResults(list):
    """
    A custom list class that stores retrieval_confidence as an attribute,
    while behaving exactly like a list to maintain backwards compatibility.
    """
    def __init__(self, *args, **kwargs):
        self.retrieval_confidence = kwargs.pop("retrieval_confidence", 0.0)
        super().__init__(*args, **kwargs)

def load_documents():
    """
    Scans the data folders and yields document chunks with source and company.
    """
    domains = {
        "hackerrank": "HackerRank",
        "claude": "Claude",
        "visa": "Visa"
    }
    
    docs = []
    
    for dir_name, company in domains.items():
        dir_path = CORPUS_DIR / dir_name
        if not dir_path.exists():
            continue
        
        # Use rglob to recursively find all .md files
        for md_file in dir_path.rglob("*.md"):
            try:
                # Prepend extended path prefix on Windows to bypass 260-char path limit
                file_str = str(md_file.resolve())
                if os.name == "nt" and not file_str.startswith("\\\\?\\"):
                    file_str = "\\\\?\\" + file_str
                    
                with open(file_str, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Derive relative path for clean source identification
                relative_source = str(md_file.relative_to(CORPUS_DIR.parent))
                
                # Chunk document: size 300-500 words (400 chosen), overlap 50 words
                words = content.split()
                chunk_size = 400
                overlap = 50
                
                i = 0
                while i < len(words):
                    chunk_words = words[i:i+chunk_size]
                    chunk_text = " ".join(chunk_words)
                    
                    if chunk_text.strip():
                        docs.append({
                            "text": chunk_text,
                            "source": relative_source,
                            "company": company
                        })
                    
                    if i + chunk_size >= len(words):
                        break
                    i += chunk_size - overlap
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
                
    return docs

def init_retrieval():
    """
    Initializes the retrieval chunks and embeddings. Loads from cache if available.
    """
    global _chunks, _embeddings, _model
    
    # If already loaded in memory
    if _chunks is not None and _embeddings is not None:
        return
        
    # Check if a serialized cache exists
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "rb") as f:
                data = pickle.load(f)
                _chunks = data["chunks"]
                _embeddings = data["embeddings"]
            return
        except Exception as e:
            pass

    # If no cache exists, we compute it from files
    _chunks = load_documents()
    
    if not _chunks:
        _embeddings = np.array([])
        return
        
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    
    texts = [c["text"] for c in _chunks]
    
    # Encode with unit normalisation so similarity is just a dot product
    _embeddings = _model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    
    # Save to file cache
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump({"chunks": _chunks, "embeddings": _embeddings}, f)
    except Exception as e:
        pass

def retrieve(query: str = "", top_k: int = 3, company: str = None, subject: str = None, issue: str = None):
    """
    Retrieves the most relevant chunks matching the query with options for 
    filtering by company, fusing subject + issue, and a similarity threshold.
    """
    global _chunks, _embeddings, _model
    
    # Combine user inputs into a single improved query
    full_query = query or ""
    if subject:
        full_query = f"{subject} {full_query}" if full_query else subject
    if issue:
        full_query = f"{full_query} {issue}" if full_query else issue

    if not full_query or not isinstance(full_query, str) or not full_query.strip():
        return RetrievalResults([], retrieval_confidence=0.0)

    init_retrieval()
    
    if _chunks is None or len(_chunks) == 0:
        return RetrievalResults([], retrieval_confidence=0.0)
        
    if _embeddings is None or len(_embeddings) == 0:
        return RetrievalResults([], retrieval_confidence=0.0)
        
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        
    # Filter documents by company if provided
    if company:
        valid_indices = [i for i, c in enumerate(_chunks) if c["company"].lower() == company.lower()]
    else:
        valid_indices = list(range(len(_chunks)))
        
    if not valid_indices:
        return RetrievalResults([], retrieval_confidence=0.0)

    valid_chunks = [_chunks[i] for i in valid_indices]
    valid_embeddings = _embeddings[valid_indices]

    # Encode query with normalisation
    query_emb = _model.encode([full_query], normalize_embeddings=True, show_progress_bar=False)[0]
    
    # Compute cosine similarities via dot product
    similarities = np.dot(valid_embeddings, query_emb)
    
    max_score = float(np.max(similarities)) if len(similarities) > 0 else 0.0

    # Similarity Threshold filtering: if top similarity < 0.4, return empty list
    if max_score < 0.4:
        return RetrievalResults([], retrieval_confidence=max_score)
    
    # Sort top matches
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        # Avoid including any chunks that might fall below the threshold
        if similarities[idx] >= 0.4:
            results.append({
                "text": valid_chunks[idx]["text"],
                "source": valid_chunks[idx]["source"],
                "company": valid_chunks[idx]["company"],
                "score": float(similarities[idx])
            })
        
    return RetrievalResults(results, retrieval_confidence=max_score)
