import httpx
import os
from app.auth import generate_app_jwt

async def get_installation_access_token(installation_id: str) -> str:
    """
    Exchanges the App JWT for an installation access token.
    
    Args:
        installation_id: The GitHub App installation ID (from webhook payload)
    
    Returns:
        Installation access token string
    
    Raises:
        Exception: If the token exchange fails
    """
    app_id = os.getenv("GITHUB_APP_ID")
    private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
    
    # Generate the App JWT
    jwt_token = generate_app_jwt(app_id, private_key_path)
    
    # Exchange JWT for installation access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to get installation token: {response.status_code} - {response.text}")
        
        data = response.json()
        return data["token"]

async def fetch_pr_diff(owner: str, repo: str, pr_number: int, installation_token: str) -> str:
    """
    Fetches the unified diff for a pull request using the GitHub API.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        pr_number: Pull request number
        installation_token: Valid installation access token
    
    Returns:
        Unified diff as a string
    
    Raises:
        Exception: If the API call fails
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {installation_token}",
                "Accept": "application/vnd.github.v3.diff"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch PR diff: {response.status_code} - {response.text}")
        
        return response.text

async def fetch_file_content(owner: str, repo: str, file_path: str, ref: str, installation_token: str) -> str:
    """
    Fetches the content of a file from a specific commit/reference.
    
    Args:
        owner: Repository owner
        repo: Repository name
        file_path: Path to the file in the repository
        ref: Git reference (commit SHA, branch name, or tag)
        installation_token: Valid installation access token
    
    Returns:
        File content as a string
    
    Raises:
        Exception: If the API call fails or file is binary/too large
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={ref}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {installation_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch file content: {response.status_code} - {response.text}")
        
        data = response.json()
        if data.get("encoding") != "base64":
            raise Exception(f"Unexpected encoding: {data.get('encoding')}")
        
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content


