from unidiff import PatchSet

def parse_diff(diff_text: str) -> list[dict]:
    """
    Parses a unified diff into a structured list of files with their hunks and added lines.
    
    Args:
        diff_text: Unified diff string from GitHub
    
    Returns:
        List of file objects, each containing filename and list of hunks
        Each hunk contains added lines with their line numbers and content
    """
    if not diff_text or diff_text.strip() == "":
        return []
    
    patch = PatchSet(diff_text)
    files = []
    
    for patched_file in patch:
        # Skip binary files
        if patched_file.is_binary_file:
            continue
        
        file_data = {
            "filename": patched_file.path,
            "hunks": []
        }
        
        for hunk in patched_file:
            added_lines = []
            for line in hunk:
                if line.is_added:
                    # Line numbers in the target file (after the patch)
                    # target_line_no is the line number in the new file
                    added_lines.append({
                        "line_number": line.target_line_no,
                        "content": line.value.strip("\n")
                    })
            if added_lines:
                file_data["hunks"].append(added_lines)
        
        # Only include files that have added lines (we only comment on additions)
        if file_data["hunks"]:
            files.append(file_data)
    
    return files

def get_line_position_map(diff_text: str, file_path: str) -> dict[int, int]:
    """
    Given a unified diff and a file path, returns a dict mapping each added line's
    target line number to its diff position (used by GitHub PR Review API).
    The position is the line number in the file's diff, starting from 1.
    """
    from unidiff import PatchSet
    patch = PatchSet(diff_text)
    
    # Find the correct file in the patch
    for patched_file in patch:
        if patched_file.path == file_path:
            # We need to compute the position within this file's diff
            # First, find the line number where this file's diff starts in the global diff
            global_lines = diff_text.splitlines()
            start_line = None
            for i, line in enumerate(global_lines, start=1):
                if line.startswith(f"+++ b/{file_path}") or line.startswith(f"+++ {file_path}"):
                    start_line = i - 1
                    break
            
            if start_line is None:
                # Fallback: if we can't find the start, just use the target line number (not ideal)
                return {}
            
            # Now compute position = diff_line_no - start_line + 1
            pos_map = {}
            for hunk in patched_file:
                for line in hunk:
                    if line.is_added:
                        # `diff_line_no` is the line number in the *global* diff
                        position = line.diff_line_no - start_line + 1
                        pos_map[line.target_line_no] = position
            return pos_map
    
    return {}
