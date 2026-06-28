import asyncio
import os
import json
from dotenv import load_dotenv
from app.github_client import get_installation_access_token, fetch_pr_diff, fetch_file_content
from app.diff_parser import parse_diff
from app.linter import run_flake8
from app.reviewer import review_code_with_gemini

load_dotenv()

async def test():
    installation_id = "142975722"
    owner = "withshafan"
    repo = "reviewbot"
    pr_number = 1
    
    print(f"Testing LLM review for {owner}/{repo} PR #{pr_number}")
    
    # 1. Get token and fetch diff
    token = await get_installation_access_token(installation_id)
    diff_text = await fetch_pr_diff(owner, repo, pr_number, token)
    
    # 2. Parse diff
    parsed = parse_diff(diff_text)
    if not parsed:
        print("No files changed.")
        return
    
    # 3. Process each changed file
    for file_data in parsed:
        filename = file_data["filename"]
        print(f"\n--- Reviewing {filename} ---")
        
        # Fetch full file content
        try:
            content = await fetch_file_content(owner, repo, filename, "add-config-example", token)
            print(f"Fetched content ({len(content)} chars)")
        except Exception as e:
            print(f"Error fetching content: {e}")
            continue
        
        # Run linter
        lint_issues = run_flake8(content)
        print(f"Linter found {len(lint_issues)} issues")
        
        # Build diff for this file (just use the full diff for now)
        # In production, we'd extract per-file diff
        file_diff = diff_text  # Simplified for testing
        
        # Call LLM
        print("Calling Gemini API...")
        result = review_code_with_gemini(content, file_diff, lint_issues)
        
        print("\n=== LLM Review Result ===")
        print(f"Assessment: {result.get('overall_assessment', 'N/A')}")
        print(f"Decision: {result.get('review_decision', 'N/A')}")
        print(f"Issues found: {len(result.get('issues', []))}")
        
        if result.get('issues'):
            print("\nIssues:")
            for issue in result['issues']:
                print(f"  - Line {issue.get('line', '?')}: [{issue.get('severity', 'unknown')}] {issue.get('description', '')}")
        
        # Save the full result to a file for inspection
        with open("review_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\nFull result saved to review_result.json")

if __name__ == "__main__":
    asyncio.run(test())
