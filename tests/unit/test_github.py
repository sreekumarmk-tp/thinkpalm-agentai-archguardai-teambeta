import pytest
from unittest.mock import patch, MagicMock
from src.tools.github import parse_github_repo, github_headers, get_default_branch, fetch_repo_structure, read_github_file

def test_parse_github_repo_valid():
    owner, repo = parse_github_repo("https://github.com/owner/repo")
    assert owner == "owner"
    assert repo == "repo"

def test_parse_github_repo_invalid():
    with pytest.raises(ValueError, match="Invalid GitHub repository URL."):
        parse_github_repo("https://github.com/owner")

@patch("src.tools.github.GITHUB_TOKEN", "fake_token")
def test_github_headers_with_token():
    assert github_headers() == {"Authorization": "token fake_token"}

@patch("src.tools.github.GITHUB_TOKEN", None)
def test_github_headers_without_token():
    assert github_headers() == {}

@patch("src.tools.github.requests.get")
def test_get_default_branch(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"default_branch": "develop"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    branch = get_default_branch("https://github.com/owner/repo")
    assert branch == "develop"

@patch("src.tools.github.requests.get")
@patch("src.tools.github.get_default_branch", return_value="main")
def test_fetch_repo_structure_success(mock_branch, mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tree": [
            {"path": "file1.py", "type": "blob"},
            {"path": "node_modules/file2.js", "type": "blob"},
            {"path": "image.png", "type": "blob"},
            {"path": "dir1", "type": "tree"}
        ]
    }
    mock_get.return_value = mock_response

    structure = fetch_repo_structure("https://github.com/owner/repo")
    assert "file1.py" in structure
    assert "node_modules/file2.js" not in structure
    assert "image.png" not in structure
    assert "dir1" not in structure

@patch("src.tools.github.requests.get")
def test_fetch_repo_structure_error(mock_get):
    mock_get.side_effect = Exception("API error")
    structure = fetch_repo_structure("https://github.com/owner/repo")
    assert "Error fetching structure: API error" in structure

@patch("src.tools.github.requests.get")
def test_read_github_file_success(mock_get):
    mock_response = MagicMock()
    import base64
    content = base64.b64encode(b"file content").decode("utf-8")
    mock_response.json.return_value = {"encoding": "base64", "content": content}
    mock_get.return_value = mock_response

    result = read_github_file("https://github.com/owner/repo", "file.txt")
    assert result.startswith("file content")

@patch("src.tools.github.requests.get")
def test_read_github_file_unsupported_encoding(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"encoding": "utf-8", "content": "file content"}
    mock_get.return_value = mock_response

    result = read_github_file("https://github.com/owner/repo", "file.txt")
    assert "unsupported encoding" in result

@patch("src.tools.github.requests.get")
def test_read_github_file_error(mock_get):
    mock_get.side_effect = Exception("API error")
    result = read_github_file("https://github.com/owner/repo", "file.txt")
    assert "Error reading file: API error" in result
