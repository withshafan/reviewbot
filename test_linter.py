import asyncio
import os
from dotenv import load_dotenv
from app.github_client import get_installation_access_token, fetch_file_content
from app.linter import run_flake8
from app.diff_parser import parse_diff
from app.github_client import fetch_pr_diff

load_dotenv()

async def test():
    installation_id = "142975722"
    owner = "withshafan"
    repo = "test-app"
    pr_number = 1
    
    # 1. Get token and fetch diff
    token = await get_installation_access_token(installation_id)
    diff_text = await fetch_pr_diff(owner, repo, pr_number, token)
    
    # 2. Parse diff to get the changed files
    parsed = parse_diff(diff_text)
    if not parsed:
        print("No files changed or no added lines.")
        return
    
    # 3. For each file, fetch content and run linter
    for file_data in parsed:
        filename = file_data["filename"]
        print(f"\n--- Checking {filename} ---")
        
        try:
            content = await fetch_file_content(owner, repo, filename, "pr-test", token)
            print(f"Fetched content for {filename} ({len(content)} chars)")
            
            # Run flake8
            lint_issues = run_flake8(content)
            if lint_issues:
                print(f"Flake8 found {len(lint_issues)} issues:")
                for issue in lint_issues:
                    print(f"  {issue}")
            else:
                print("No linting issues found.")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
