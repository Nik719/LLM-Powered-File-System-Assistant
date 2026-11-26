import os
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pypdf import PdfReader
from docx import Document

def read_file(filepath: str) -> Dict[str, Any]:
    """Read PDF, TXT, DOCX files, extract text, and return structured metadata."""
    path = Path(filepath)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {filepath}"}

    try:
        ext = path.suffix.lower()
        extracted_text = ""

        if ext == ".txt":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()
        elif ext == ".pdf":
            reader = PdfReader(path)
            text_runs = [page.extract_text() or "" for page in reader.pages]
            extracted_text = "\n".join(text_runs)
        elif ext == ".docx":
            doc = Document(path)
            extracted_text = "\n".join([p.text for p in doc.paragraphs])
        else:
            return {"status": "error", "message": f"Unsupported extension: {ext}"}

        stats = path.stat()
        return {
            "status": "success",
            "content": extracted_text.strip(),
            "metadata": {
                "filename": path.name,
                "filepath": str(path.resolve()),
                "size_bytes": stats.st_size,
                "extension": ext
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to read file: {str(e)}"}

def list_files(directory: str, extension: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all files in a directory with optional extension filtering."""
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        return []

    results = []
    if extension and not extension.startswith('.'):
        extension = f".{extension}"

    for entry in dir_path.iterdir():
        if entry.is_file():
            if extension and entry.suffix.lower() != extension.lower():
                continue
            stats = entry.stat()
            mod_time = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
            results.append({
                "name": entry.name,
                "filepath": str(entry.resolve()),
                "size_bytes": stats.st_size,
                "modified_date": mod_time
            })
    return results

def write_file(filepath: str, content: str) -> Dict[str, Any]:
    """Write text content to a destination path, creating folders if missing."""
    try:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "status": "success",
            "message": f"File written successfully to {filepath}",
            "bytes_written": len(content)
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to write file: {str(e)}"}

def search_in_file(filepath: str, keyword: str) -> Dict[str, Any]:
    """Perform case-insensitive keyword search in file returning context lines."""
    res = read_file(filepath)
    if res.get("status") == "error":
        return res

    lines = res["content"].splitlines()
    matches = []
    keyword_lower = keyword.lower()

    for idx, line in enumerate(lines):
        if keyword_lower in line.lower():
            start_idx = max(0, idx - 1)
            end_idx = min(len(lines), idx + 2)
            context = "\n".join(lines[start_idx:end_idx])
            matches.append({
                "line_number": idx + 1,
                "matched_text": line.strip(),
                "context": context.strip()
            })

    return {
        "status": "success",
        "filepath": filepath,
        "keyword": keyword,
        "match_count": len(matches),
        "matches": matches
    }

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and extract raw text content from a PDF, TXT, or DOCX resume file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "The path to the file to read."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in a directory with optional extension filtering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path to list files from."},
                    "extension": {"type": "string", "description": "Optional extension filter (e.g. '.pdf', '.txt')."}
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a destination file path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Target output file path."},
                    "content": {"type": "string", "description": "Text content to save."}
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Perform a case-insensitive search for a keyword inside a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "File path to search inside."},
                    "keyword": {"type": "string", "description": "Keyword or skill to search for."}
                },
                "required": ["filepath", "keyword"]
            }
        }
    }
]
