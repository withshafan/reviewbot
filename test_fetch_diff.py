import asyncio
import os
from dotenv import load_dotenv
from app.github_client import get_installation_access_token, fetch_pr_diff

load_dotenv()

async def test():
    installation_id = "142975722"  # Your installation ID
    owner = "withshafan"          # Replace with your GitHub username
    repo = "test-app"             # Replace with your repository name
    pr_number = 1                # Replace with your actual PR number
    
    print(f"Fetching diff for {owner}/{repo} PR #{pr_number}")
    
    try:
        token = await get_installation_access_token(installation_id)
        diff = await fetch_pr_diff(owner, repo, pr_number, token)
        print(f"Successfully fetched diff ({len(diff)} characters)")
        print("\nFirst 500 characters of diff:")
        print(diff[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
