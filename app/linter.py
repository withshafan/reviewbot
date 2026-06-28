import subprocess
import tempfile
import os
import sys

def run_flake8(file_content: str) -> list[str]:
    """
    Runs flake8 on the given file content and returns the output lines.
    
    Args:
        file_content: String content of the Python file
    
    Returns:
        List of flake8 error lines (each line is a string)
    """
    # Write content to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        # Run flake8 with format: line:col: code message
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--format=%(row)d:%(col)d: %(code)s %(text)s", tmp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout.strip()
        if output:
            return output.split("\n")
        else:
            return []
    except subprocess.TimeoutExpired:
        return ["Timeout: flake8 took too long"]
    except Exception as e:
        return [f"Error running flake8: {e}"]
    finally:
        # Clean up the temporary file
        try:
            os.unlink(tmp_path)
        except:
            pass
