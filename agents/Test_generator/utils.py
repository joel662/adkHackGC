import os
import requests

EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "c#",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".rs": "rust",
    ".swift": "swift",
    ".kt": "kotlin",
    ".sh": "bash",
    ".sql": "sql",
    ".html": "html",
    ".jsx": "react-jsx",
    ".tsx": "react-tsx",
    # Add more as needed
}

def read_local_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def read_remote_file(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")

def detect_language_from_extension(filepath: str) -> str:
    _, ext = os.path.splitext(filepath)
    return EXTENSION_LANGUAGE_MAP.get(ext.lower(), "unknown")