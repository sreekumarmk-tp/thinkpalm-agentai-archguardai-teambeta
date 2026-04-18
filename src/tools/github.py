import base64
import requests
from typing import Dict, Tuple
from urllib.parse import urlparse
from src.config.settings import GITHUB_TOKEN, GITHUB_TIMEOUT, MAX_FILE_LIST, MAX_FILE_CONTENT_CHARS

def parse_github_repo(repo_url: str) -> Tuple[str, str]:
    cleaned = repo_url.strip().rstrip("/")
    parsed = urlparse(cleaned)
    path_parts = [p for p in parsed.path.split("/") if p]
    if len(path_parts) < 2:
        raise ValueError("Invalid GitHub repository URL.")
    return path_parts[0], path_parts[1]

def github_headers() -> Dict[str, str]:
    if GITHUB_TOKEN:
        return {"Authorization": f"token {GITHUB_TOKEN}"}
    return {}

def get_default_branch(repo_url: str) -> str:
    owner, repo = parse_github_repo(repo_url)
    url = f"https://api.github.com/repos/{owner}/{repo}"
    res = requests.get(url, headers=github_headers(), timeout=GITHUB_TIMEOUT)
    res.raise_for_status()
    return res.json().get("default_branch", "main")

def fetch_repo_structure(repo_url: str) -> str:
    try:
        owner, repo = parse_github_repo(repo_url)
        branch = get_default_branch(repo_url)
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        res = requests.get(url, headers=github_headers(), timeout=GITHUB_TIMEOUT)
        res.raise_for_status()
        tree = res.json().get("tree", [])
        files = []
        excluded = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
        for node in tree:
            node_path = node.get("path", "")
            if node.get("type") != "blob":
                continue
            if "node_modules" in node_path or ".git/" in node_path:
                continue
            if node_path.lower().endswith(excluded):
                continue
            files.append(node_path)
        return "\n".join(files[:MAX_FILE_LIST])
    except Exception as e:
        return f"Error fetching structure: {str(e)}"

def read_github_file(repo_url: str, path: str) -> str:
    try:
        owner, repo = parse_github_repo(repo_url)
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        res = requests.get(url, headers=github_headers(), timeout=GITHUB_TIMEOUT)
        res.raise_for_status()
        payload = res.json()
        if payload.get("encoding") != "base64":
            return "Error reading file: unsupported encoding."
        decoded = base64.b64decode(payload["content"])
        try:
            content = decoded.decode("utf-8")
        except UnicodeDecodeError:
            content = decoded.decode("latin-1", errors="ignore")
        return content[:MAX_FILE_CONTENT_CHARS]
    except Exception as e:
        return f"Error reading file: {str(e)}"
