import os
import csv
import sys
from pathlib import Path
from tqdm import tqdm

from dotenv import load_dotenv

# Add the repository root to python path so modules inside code/ are resolvable
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

# Load local environment variables from .env
load_dotenv(dotenv_path=repo_root / ".env")

from code.agent import run_agent

def main():
    """
    Main execution script for HackerRank Orchestrate hackathon.
    Reads support tickets from CSV, runs them deterministically through 
    the orchestrated AI agent pipeline, and safely exports the results to CSV.
    """
    
    # 1. Resolve paths
    support_dir = repo_root / "support_tickets"
    input_file = support_dir / "support_tickets.csv"
    output_file = support_dir / "output.csv"
    
    # Check if support_tickets directory and file exists, otherwise try fallback mapping
    if not input_file.exists():
        fallback_dir = repo_root / "support_issues"
        input_file = fallback_dir / "support_issues.csv"
        output_file = fallback_dir / "output.csv"
        
        if not input_file.exists():
            print(f"Error: Could not locate the support dataset at either {support_dir} or {fallback_dir}")
            sys.exit(1)
            
    print("==================================================")
    print("        STARTING SUPPORT AGENT PIPELINE           ")
    print("==================================================")
    print(f"Input file:  {input_file.relative_to(repo_root)}")
    print(f"Output file: {output_file.relative_to(repo_root)}\n")
    
    # The evaluator expects only the five prediction columns in output.csv.
    output_fieldnames = ["status", "product_area", "response", "justification", "request_type"]
    
    results = []
    
    try:
        with open(input_file, mode="r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            
            rows = list(reader)
            total_rows = len(rows)
            
            for row in tqdm(rows, desc="Processing Tickets", unit="ticket", ncols=80):
                # Safely extract with case-insensitive fallback logic
                issue = row.get("Issue", row.get("issue", "")).strip()
                subject = row.get("Subject", row.get("subject", "")).strip()
                company = row.get("Company", row.get("company", "")).strip()
                
                # Pass missing parameters explicitly
                if company.lower() == "none":
                    company = ""
                    
                # 2. Pass to SupportAgent
                try:
                    agent_output = run_agent(issue=issue, subject=subject, company=company)
                except Exception as e:
                    # Deterministic fallback upon total module crash
                    agent_output = {
                        "status": "escalated",
                        "product_area": company if company else "General",
                        "response": "We could not find relevant support information. Your request has been escalated.",
                        "justification": f"Decision: ESCALATED (Level: high)\nError encountered: {e}",
                        "request_type": "general_inquiry"
                    }
                    
                # 3. Collect only the required evaluator outputs.
                results.append({
                    k: str(agent_output.get(k, ""))
                    for k in output_fieldnames
                })
                
    except Exception as e:
        print(f"Failed to read from the input file: {e}")
        sys.exit(1)
        
    # 4. Save to output.csv
    try:
        with open(output_file, mode="w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
        print(f"\nSuccessfully wrote {len(results)} rows to {output_file.name}.")
    except Exception as e:
        print(f"Failed to write results to output file: {e}")
        sys.exit(1)
        
    print("==================================================")
    print("                EXECUTION COMPLETE                ")
    print("==================================================")

if __name__ == "__main__":
    main()
