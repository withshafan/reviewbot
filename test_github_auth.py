import asyncio
import os
from dotenv import load_dotenv
from app.github_client import get_installation_access_token

load_dotenv()

async def test():
    installation_id = "142975722"  # Your installation ID
    
    print(f"Testing token exchange for installation ID: {installation_id}")
    
    try:
        token = await get_installation_access_token(installation_id)
        print(f"Success! Got installation access token:")
        print(f"Token (first 20 chars): {token[:20]}...")
        print(f"Token length: {len(token)} characters")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
