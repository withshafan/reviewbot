import httpx
from app.diff_parser import get_line_position_map

async def post_review(
    owner: str,
    repo: str,
    pr_number: int,
    diff_text: str,
    issues: list[dict],
    overall_assessment: str,
    decision: str,
    installation_token: str
) -> dict:
    """
    Posts a pull request review with inline comments and a summary.
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        diff_text: The unified diff for the PR (for position mapping)
        issues: List of issue dicts from the LLM (each has 'file', 'line', 'severity', etc.)
        overall_assessment: Summary text from the LLM
        decision: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'
        installation_token: Valid installation access token
    
    Returns:
        Response from GitHub API
    """
    
    # Group issues by file
    issues_by_file = {}
    for issue in issues:
        file_path = issue.get("file", "unknown")
        if file_path not in issues_by_file:
            issues_by_file[file_path] = []
        issues_by_file[file_path].append(issue)
    
    # Build inline comments
    comments = []
    for file_path, file_issues in issues_by_file.items():
        # Get position map for this file
        pos_map = get_line_position_map(diff_text, file_path)
        
        for issue in file_issues:
            line_num = issue.get("line")
            if not line_num:
                continue
            
            # Map line number to diff position
            position = pos_map.get(line_num)
            if position is None:
                # If we can't map, skip this comment (can't post inline)
                continue
            
            # Build comment body
            severity = issue.get("severity", "suggestion")
            category = issue.get("category", "style")
            description = issue.get("description", "No description")
            suggestion = issue.get("suggestion", "")
            
            body = f"**[{severity.upper()}] {category.upper()}**\n\n{description}"
            if suggestion:
                body += f"\n\n💡 **Suggestion:** {suggestion}"
            
            comments.append({
                "path": file_path,
                "line": line_num,
                "side": "RIGHT",
                "body": body
            })
    
    # Build summary comment
    total_issues = len(issues)
    summary = f"## 🤖 ReviewBot Summary\n\n"
    summary += f"{overall_assessment}\n\n"
    summary += f"**Found {total_issues} issue(s):**\n"
    
    # Count by severity
    severity_counts = {}
    for issue in issues:
        sev = issue.get("severity", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    for sev, count in severity_counts.items():
        summary += f"- {sev}: {count}\n"
    
    summary += f"\n**Decision:** {decision}"
    
    # Create the review request
    review_data = {
        "body": summary,
        "event": decision,
        "comments": comments
    }

    
    # Post the review
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {installation_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json=review_data
        )
        
        if response.status_code not in (200, 201):
            raise Exception(f"Failed to post review: {response.status_code} - {response.text}")
        
        return response.json()
