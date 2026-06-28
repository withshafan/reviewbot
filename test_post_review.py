import asyncio
import os
from dotenv import load_dotenv
from app.github_client import get_installation_access_token, fetch_pr_diff, fetch_file_content
from app.diff_parser import parse_diff
from app.linter import run_flake8
from app.reviewer import review_code_with_gemini
from app.commenter import post_review

load_dotenv()

async def main():
    installation_id = "142975722"
    owner = "withshafan"
    repo = "reviewbot"
    pr_number = 1
    branch_ref = "add-config-example"  # The branch name with your changes
    
    print(f"ReviewBot testing PR #{pr_number} on {owner}/{repo}")
    print("=" * 50)
    
    # 1. Get installation token
    print("Getting GitHub token...")
    token = await get_installation_access_token(installation_id)
    print("Token obtained")
    
    # 2. Fetch PR diff
    print(f"Fetching diff for PR #{pr_number}...")
    diff_text = await fetch_pr_diff(owner, repo, pr_number, token)
    print(f"Diff fetched ({len(diff_text)} chars)")
    
    # 3. Parse diff to get changed files
    parsed = parse_diff(diff_text)
    if not parsed:
        print("No changed files found.")
        return
    
    print(f"Changed files: {len(parsed)}")
    
    # 4. Process each file
    all_issues = []
    
    for file_data in parsed:
        filename = file_data["filename"]
        print(f"\n--- Processing {filename} ---")
        
        # Fetch file content
        try:
            content = await fetch_file_content(owner, repo, filename, branch_ref, token)
            print(f"Fetched content ({len(content)} chars)")
        except Exception as e:
            print(f"Error fetching content: {e}")
            continue
        
        # Run linter
        lint_issues = run_flake8(content)
        print(f"Linter found {len(lint_issues)} issues")
        
        # Call Gemini
        print("Calling Gemini API for review...")
        result = review_code_with_gemini(content, diff_text, lint_issues)
        
        issues = result.get("issues", [])
        all_issues.extend(issues)
        print(f"Gemini found {len(issues)} issues")
        
        for issue in issues:
            print(f"  - Line {issue.get('line', '?')}: [{issue.get('severity', 'unknown')}] {issue.get('description', '')[:50]}...")
    
    # 5. Post the review
    if all_issues:
        print(f"\nPosting review with {len(all_issues)} issues...")
        
        # Determine decision based on severity
        critical_issues = [i for i in all_issues if i.get('severity') == 'critical']
        if critical_issues:
            decision = "REQUEST_CHANGES"
        else:
            decision = "COMMENT"
        
        overall_assessment = result.get("overall_assessment", "Code review completed.")
        
        try:
            review_response = await post_review(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                diff_text=diff_text,
                issues=all_issues,
                overall_assessment=overall_assessment,
                decision=decision,
                installation_token=token
            )
            print(f"Review posted successfully!")
            print(f"   Review ID: {review_response.get('id')}")
            print(f"   Decision: {review_response.get('state')}")
            print(f"   Comments: {len(review_response.get('comments', []))}")
            
            # Show the review URL
            print(f"\nView the review at:")
            print(f"https://github.com/{owner}/{repo}/pull/{pr_number}")
            
        except Exception as e:
            print(f"Error posting review: {e}")
    else:
        print("\nNo issues found. Posting a comment review.")
        # Post a comment-only review
        try:
            review_response = await post_review(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                diff_text=diff_text,
                issues=[],
                overall_assessment="No issues found. Great work!",
                decision="COMMENT",
                installation_token=token
            )
            print(f"Comment review posted successfully!")
            print(f"https://github.com/{owner}/{repo}/pull/{pr_number}")
        except Exception as e:
            print(f"Error posting review: {e}")

if __name__ == "__main__":
    asyncio.run(main())
