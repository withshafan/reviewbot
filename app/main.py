from fastapi import FastAPI, Request, Response, Header, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
import json
import os
import fnmatch
from dotenv import load_dotenv

# Database initialization
from app.database import engine, SessionLocal, Base
from app.models import ReviewHistory
Base.metadata.create_all(bind=engine)

from app.auth import validate_signature
from app.github_client import get_installation_access_token, fetch_pr_diff, fetch_file_content
from app.diff_parser import parse_diff
from app.linter import run_flake8
from app.reviewer import review_code_with_gemini
from app.commenter import post_review
from app.config_loader import load_config

# Load environment variables
load_dotenv()

# Create FastAPI app instance — disable default docs to use custom pages
app = FastAPI(
    title="ReviewBot",
    description="AI-Powered Pull Request Reviewer",
    docs_url=None,   # Replaced by custom /docs
    redoc_url=None,   # Replaced by custom /redoc
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include web page routes (landing, dashboard, health, demo, docs, redoc, /api/reviews)
from app.routes.web_routes import router as web_router
app.include_router(web_router)

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

async def process_pr_review(owner: str, repo: str, pr_number: int, installation_id: str, head_sha: str):
    print(f"Starting PR review in background for {owner}/{repo} PR #{pr_number}")
    try:
        # 1. Get installation token
        token = await get_installation_access_token(str(installation_id))
        
        # 2. Load config from repository
        config = await load_config(owner, repo, head_sha, token)
        print(f"Loaded config: {config}")
        
        # 3. Fetch PR diff
        diff_text = await fetch_pr_diff(owner, repo, pr_number, token)
        
        # 4. Parse diff
        parsed = parse_diff(diff_text)
        if not parsed:
            print(f"No changed files found for {owner}/{repo} PR #{pr_number}")
            return
            
        all_issues = []
        
        # 5. Process each file
        for file_data in parsed:
            filename = file_data["filename"]
            
            # Apply ignore_paths filter
            ignored = False
            for pattern in config.get("ignore_paths", []):
                if fnmatch.fnmatch(filename, pattern):
                    ignored = True
                    break
            if ignored:
                print(f"Skipping ignored file: {filename}")
                continue
                
            try:
                content = await fetch_file_content(owner, repo, filename, head_sha, token)
            except Exception as e:
                print(f"Error fetching file content for {filename}: {e}")
                continue
                
            # Run flake8 linter
            lint_issues = run_flake8(content)
            
            # Call Gemini
            result = review_code_with_gemini(content, diff_text, lint_issues)
            
            # Filter issues by min_severity
            severity_order = {"nitpick": 0, "suggestion": 1, "warning": 2, "critical": 3}
            min_sev = config.get("min_severity", "warning")
            min_level = severity_order.get(min_sev, 2)
            
            issues = result.get("issues", [])
            filtered_issues = []
            for issue in issues:
                issue_sev = issue.get("severity", "suggestion")
                issue_level = severity_order.get(issue_sev, 1)
                if issue_level >= min_level:
                    filtered_issues.append(issue)
                    
            all_issues.extend(filtered_issues)
            
        # 6. Post review to GitHub
        decision = "COMMENT"
        if all_issues:
            critical_issues = [i for i in all_issues if i.get('severity') == 'critical']
            if critical_issues:
                decision = "REQUEST_CHANGES"
            else:
                decision = "COMMENT"
            overall_assessment = "Review completed. Please address the listed feedback."
        else:
            overall_assessment = "No issues found matching your configuration filters. Great work!"
            decision = "COMMENT"
            
        await post_review(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            diff_text=diff_text,
            issues=all_issues,
            overall_assessment=overall_assessment,
            decision=decision,
            installation_token=token
        )
        print(f"Successfully posted review for {owner}/{repo} PR #{pr_number}")
        
        # 7. Save review record to Database
        db = SessionLocal()
        try:
            history_record = ReviewHistory(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                head_sha=head_sha,
                total_issues=len(all_issues),
                decision=decision
            )
            db.add(history_record)
            db.commit()
            print("Successfully recorded review to database.")
        except Exception as db_err:
            print(f"Error saving to database: {db_err}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error executing PR review background task: {e}")

@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None)
):
    body = await request.body()
    
    # Validate webhook signature
    if not validate_signature(body, x_hub_signature_256, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Only process pull_request events
    if x_github_event != "pull_request":
        return {"status": "ignored", "event": x_github_event}
    
    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "action": action}
    
    # Extract PR parameters
    repo_full_name = payload["repository"]["full_name"]
    owner, repo = repo_full_name.split("/")
    pr_number = payload["pull_request"]["number"]
    installation_id = payload["installation"]["id"]
    head_sha = payload["pull_request"]["head"]["sha"]
    
    # Process the review in a FastAPI background task
    background_tasks.add_task(
        process_pr_review,
        owner, repo, pr_number, installation_id, head_sha
    )
    
    return {"status": "accepted", "pr": pr_number}