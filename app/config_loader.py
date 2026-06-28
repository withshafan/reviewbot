import yaml
import base64
import httpx

DEFAULTS = {
    "min_severity": "warning",
    "ignore_paths": ["*.md", "*.txt", "*.lock"],
    "max_files_per_review": 20,
    "focus_areas": [],
}

async def load_config(owner: str, repo: str, ref: str, token: str) -> dict:
    """
    Fetches and parses the .reviewbot.yaml configuration file from the repository.
    Falls back to default settings if the file does not exist or is invalid.
    
    Args:
        owner: Repository owner
        repo: Repository name
        ref: Branch or commit reference
        token: Installation access token
        
    Returns:
        Configuration dictionary
    """
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/.reviewbot.yaml?ref={ref}"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            if response.status_code == 200:
                content = base64.b64decode(response.json()["content"]).decode("utf-8")
                user_config = yaml.safe_load(content)
                if isinstance(user_config, dict):
                    return {**DEFAULTS, **user_config}
    except Exception:
        pass
    return DEFAULTS
