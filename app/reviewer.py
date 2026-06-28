import os
import json
import google.generativeai as genai
from typing import List, Dict, Any

# Configure Gemini lazily
_model = None

def get_gemini_model():
    global _model
    if _model is None:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        _model = genai.GenerativeModel("gemini-2.5-flash")  # Working stable model
    return _model

def review_code_with_gemini(file_content: str, diff_text: str, lint_issues: List[str]) -> Dict[str, Any]:
    """
    Sends code review request to Google Gemini and returns structured feedback.
    
    Args:
        file_content: Full content of the file being reviewed
        diff_text: The unified diff for this file
        lint_issues: List of linter issues found (strings)
    
    Returns:
        Dictionary with 'issues' list, 'overall_assessment', and 'review_decision'
    """
    
    # Build the prompt
    lint_text = "\n".join(lint_issues) if lint_issues else "No linting issues found."
    
    prompt = f"""You are a senior software engineer conducting a code review.

FILE CONTENT (full file):
```
{file_content}
```

CHANGED LINES (diff):
```
{diff_text}
```

STATIC ANALYSIS RESULTS (from flake8):
```
{lint_text}
```

Review the changes above. Identify bugs, security issues, logic errors, performance problems, and style violations.

Return ONLY valid JSON matching this exact schema, with no other text:
{{
  "issues": [
    {{
      "file": "filename.py",
      "line": 42,
      "severity": "critical",  // one of: critical, warning, suggestion, nitpick
      "category": "bug",       // one of: bug, security, performance, style, logic
      "description": "Description of the issue",
      "suggestion": "Suggested fix"
    }}
  ],
  "overall_assessment": "Brief summary of the PR quality",
  "review_decision": "APPROVE" // one of: APPROVE, REQUEST_CHANGES, COMMENT
}}

Severity levels:
- critical: Will break something, must fix
- warning: Likely to cause problems
- suggestion: Worth changing but not urgent
- nitpick: Minor style preference

Focus only on the changed lines (the diff). Do not comment on code that hasn't been changed.
"""

    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract JSON from the response (remove any markdown code blocks)
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
        
        result = json.loads(result_text)
        
        # Ensure required fields exist
        if "issues" not in result:
            result["issues"] = []
        if "overall_assessment" not in result:
            result["overall_assessment"] = "No assessment provided."
        if "review_decision" not in result:
            result["review_decision"] = "COMMENT"
            
        return result
        
    except json.JSONDecodeError as e:
        return {
            "issues": [],
            "overall_assessment": f"Error parsing LLM response: {e}",
            "review_decision": "COMMENT",
            "error": result_text if 'result_text' in locals() else "Unknown error"
        }
    except Exception as e:
        return {
            "issues": [],
            "overall_assessment": f"Error calling Gemini: {e}",
            "review_decision": "COMMENT",
            "error": str(e)
        }
