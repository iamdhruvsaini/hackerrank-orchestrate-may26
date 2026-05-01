# Support Triage Agent

This directory contains the core implementation of the HackerRank Orchestrate AI support triage agent. The agent uses Retrieval-Augmented Generation (RAG) and deterministic routing to accurately classify, route, and resolve customer support tickets across three corporate ecosystems (Visa, HackerRank, and Claude).

---

## 🏗️ System Architecture

The project is structured as a scalable pipeline, orchestrated via a clear set of decoupled modules in the `core` package:

1. **Pipeline Orchestrator (`agent.py`)**  
   The known entry point. Parses inputs and orchestrates the flow of data through classification, retrieval, decision making, and generation.

2. **Semantic Retrieval Engine (`core/retrieval.py`)**  
   Responsible for data ingestion and chunking. Uses `sentence-transformers` (`all-MiniLM-L6-v2`) locally to embed and cache the 100+ Markdown documents from the `data/` directory. Applies company-specific filters and relevance thresholding (confidence `< 0.4` filters out bad context).

3. **Deterministic Triage & Decision (`core/decision.py`)**  
   Scores inbound tickets for `urgency`, `risk`, and `sentiment` through strict linguistic pattern matching. Combines linguistic risk with retrieval confidence to assign a final `status` ("replied" vs. "escalated") and computes robust metric explanations for the judge. Implements **High-Risk Overrides** (e.g. fraud, access removed, overrides) that bypass RAG completely to escalate instantly.

4. **Response & Justification Generator (`core/generator.py`)**  
   - **Text Grounding:** Extracts only factually complete sentences from RAG chunks, heavily filtering noisy document artifacts (YAML frontmatter, links, URLs).
   - **Groq LLM Synthesis:** Leverages `llama-3.1-8b-instant` through Groq to generate highly empathetic user responses and professional internal justifications exactly bounded by the provided RAG context.
   - **Deterministic Fallback:** Robust fallback mode drops seamlessly into pure deterministic string matching if API keys fail.

5. **Batch Executor (`main.py`)**  
   Reads batch requests from `support_issues.csv`, passes variables through the `.env` configuration layer, and outputs results precisely formatted to `output.csv`.

---

## ⚙️ Setup Instructions

1. Create and activate a virtual environment using [uv](https://github.com/astral-sh/uv):
   ```sh
   uv venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

2. Install the necessary dependencies (listed in `requirements.txt`):
   ```sh
   uv pip install -r ../requirements.txt
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env` in the root repository. To enable LLM natural language generation, provide your Groq key:
   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```

---

## 🚀 Run Commands

To execute the support agent batch processor against the `support_issues.csv` input set:

```sh
# Ensure you are at the repo root or inside code/
python code/main.py
```

This will run a `tqdm` progress bar in the terminal and write all 29 generated ticket resolutions side-by-side with original inputs directly into `support_tickets/output.csv`.
