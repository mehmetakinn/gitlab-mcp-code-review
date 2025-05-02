import os
import json
import logging
from typing import Optional, Dict, Any, Union, List
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from urllib.parse import quote
import requests

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class GitLabContext:
    host: str
    token: str
    api_version: str = "v4"

def make_gitlab_api_request(ctx: Context, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Any:
    """Make a REST API request to GitLab and handle the response"""
    gitlab_ctx = ctx.request_context.lifespan_context
    
    if not gitlab_ctx.token:
        logger.error("GitLab token not set in context")
        raise ValueError("GitLab token not set. Please set GITLAB_TOKEN in your environment.")
    
    url = f"https://{gitlab_ctx.host}/api/{gitlab_ctx.api_version}/{endpoint}"
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'GitLabMCPCodeReview/1.0',
        'Private-Token': gitlab_ctx.token
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, verify=True)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, verify=True)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code == 401:
            logger.error("Authentication failed. Check your GitLab token.")
            raise Exception("Authentication failed. Please check your GitLab token.")
            
        response.raise_for_status()
        
        if not response.content:
            return {}
            
        try:
            return response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            raise Exception(f"Failed to parse GitLab response as JSON: {str(e)}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"REST request failed: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response status: {e.response.status_code}")
        raise Exception(f"Failed to make GitLab API request: {str(e)}")

@asynccontextmanager
async def gitlab_lifespan(server: FastMCP) -> AsyncIterator[GitLabContext]:
    """Manage GitLab connection details"""
    host = os.getenv("GITLAB_HOST", "gitlab.com")
    token = os.getenv("GITLAB_TOKEN", "")
    
    if not token:
        logger.error("Missing required environment variable: GITLAB_TOKEN")
        raise ValueError(
            "Missing required environment variable: GITLAB_TOKEN. "
            "Please set this in your environment or .env file."
        )
    
    ctx = GitLabContext(host=host, token=token)
    try:
        yield ctx
    finally:
        pass

# Create MCP server
mcp = FastMCP(
    "GitLab MCP for Code Review",
    description="MCP server for reviewing GitLab code changes",
    lifespan=gitlab_lifespan,
    dependencies=["python-dotenv", "requests"]
)

@mcp.tool()
def fetch_merge_request(ctx: Context, project_id: str, merge_request_iid: str) -> Dict[str, Any]:
    """
    Fetch a GitLab merge request and its contents.
    
    Args:
        project_id: The GitLab project ID or URL-encoded path
        merge_request_iid: The merge request IID (project-specific ID)
    Returns:
        Dict containing the merge request information
    """
    # Get merge request details
    mr_endpoint = f"projects/{quote(project_id, safe='')}/merge_requests/{merge_request_iid}"
    mr_info = make_gitlab_api_request(ctx, mr_endpoint)
    
    if not mr_info:
        raise ValueError(f"Merge request {merge_request_iid} not found in project {project_id}")
    
    # Get the changes (diffs) for this merge request
    changes_endpoint = f"{mr_endpoint}/changes"
    changes_info = make_gitlab_api_request(ctx, changes_endpoint)
    
    # Get the commit information
    commits_endpoint = f"{mr_endpoint}/commits"
    commits_info = make_gitlab_api_request(ctx, commits_endpoint)
    
    # Get the notes (comments) for this merge request
    notes_endpoint = f"{mr_endpoint}/notes"
    notes_info = make_gitlab_api_request(ctx, notes_endpoint)
    
    return {
        "merge_request": mr_info,
        "changes": changes_info,
        "commits": commits_info,
        "notes": notes_info
    }

@mcp.tool()
def fetch_merge_request_diff(ctx: Context, project_id: str, merge_request_iid: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch the diff for a specific file in a merge request, or all files if none specified.
    
    Args:
        project_id: The GitLab project ID or URL-encoded path
        merge_request_iid: The merge request IID (project-specific ID)
        file_path: Optional specific file path to get diff for
    Returns:
        Dict containing the diff information
    """
    # Get the changes for this merge request
    changes_endpoint = f"projects/{quote(project_id, safe='')}/merge_requests/{merge_request_iid}/changes"
    changes_info = make_gitlab_api_request(ctx, changes_endpoint)
    
    if not changes_info:
        raise ValueError(f"Changes not found for merge request {merge_request_iid}")
    
    # Extract all changes
    files = changes_info.get("changes", [])
    
    # Filter by file path if specified
    if file_path:
        files = [f for f in files if f.get("new_path") == file_path or f.get("old_path") == file_path]
        if not files:
            raise ValueError(f"File '{file_path}' not found in the merge request changes")
    
    return {
        "merge_request_iid": merge_request_iid,
        "files": files
    }

@mcp.tool()
def fetch_commit_diff(ctx: Context, project_id: str, commit_sha: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch the diff for a specific commit, or for a specific file in that commit.
    
    Args:
        project_id: The GitLab project ID or URL-encoded path
        commit_sha: The commit SHA
        file_path: Optional specific file path to get diff for
    Returns:
        Dict containing the diff information
    """
    # Get the diff for this commit
    diff_endpoint = f"projects/{quote(project_id, safe='')}/repository/commits/{commit_sha}/diff"
    diff_info = make_gitlab_api_request(ctx, diff_endpoint)
    
    if not diff_info:
        raise ValueError(f"Diff not found for commit {commit_sha}")
    
    # Filter by file path if specified
    if file_path:
        diff_info = [d for d in diff_info if d.get("new_path") == file_path or d.get("old_path") == file_path]
        if not diff_info:
            raise ValueError(f"File '{file_path}' not found in the commit diff")
    
    # Get the commit details
    commit_endpoint = f"projects/{quote(project_id, safe='')}/repository/commits/{commit_sha}"
    commit_info = make_gitlab_api_request(ctx, commit_endpoint)
    
    return {
        "commit": commit_info,
        "diffs": diff_info
    }

@mcp.tool()
def compare_versions(ctx: Context, project_id: str, from_sha: str, to_sha: str) -> Dict[str, Any]:
    """
    Compare two commits/branches/tags to see the differences between them.
    
    Args:
        project_id: The GitLab project ID or URL-encoded path
        from_sha: The source commit/branch/tag
        to_sha: The target commit/branch/tag
    Returns:
        Dict containing the comparison information
    """
    # Compare the versions
    compare_endpoint = f"projects/{quote(project_id, safe='')}/repository/compare?from={quote(from_sha, safe='')}&to={quote(to_sha, safe='')}"
    compare_info = make_gitlab_api_request(ctx, compare_endpoint)
    
    if not compare_info:
        raise ValueError(f"Comparison failed between {from_sha} and {to_sha}")
    
    return compare_info

@mcp.tool()
def add_merge_request_comment(ctx: Context, project_id: str, merge_request_iid: str, body: str, position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add a comment to a merge request, optionally at a specific position in a file.
    
    Args:
        project_id: The GitLab project ID or URL-encoded path
        merge_request_iid: The merge request IID (project-specific ID)
        body: The comment text
        position: Optional position data for line comments
    Returns:
        Dict containing the created comment information
    """
    # Create the comment data
    data = {
        "body": body
    }
    
    # Add position data if provided
    if position:
        data["position"] = position
    
    # Add the comment
    comment_endpoint = f"projects/{quote(project_id, safe='')}/merge_requests/{merge_request_iid}/notes"
    comment_info = make_gitlab_api_request(ctx, comment_endpoint, method="POST", data=data)
    
    if not comment_info:
        raise ValueError("Failed to add comment to merge request")
    
    return comment_info

@mcp.tool()
def approve_merge_request(ctx: Context, project_id: str, merge_request_iid: str, approvals_required: Optional[int] = None) -> Dict[str, Any]:
    """
    Approve a merge request.
    
    Args:
        project_id: The GitLab project ID or URL-encoded path
        merge_request_iid: The merge request IID (project-specific ID)
        approvals_required: Optional number of required approvals to set
    Returns:
        Dict containing the approval information
    """
    # Approve the merge request
    approve_endpoint = f"projects/{quote(project_id, safe='')}/merge_requests/{merge_request_iid}/approve"
    approve_info = make_gitlab_api_request(ctx, approve_endpoint, method="POST")
    
    # Set required approvals if specified
    if approvals_required is not None:
        approvals_endpoint = f"projects/{quote(project_id, safe='')}/merge_requests/{merge_request_iid}/approvals"
        data = {
            "approvals_required": approvals_required
        }
        make_gitlab_api_request(ctx, approvals_endpoint, method="POST", data=data)
    
    return approve_info

@mcp.tool()
def unapprove_merge_request(ctx: Context, project_id: str, merge_request_iid: str) -> Dict[str, Any]:
    """
    Unapprove a merge request.
    
    Args:
        project_id: The GitLab project ID or URL-encoded path
        merge_request_iid: The merge request IID (project-specific ID)
    Returns:
        Dict containing the unapproval information
    """
    # Unapprove the merge request
    unapprove_endpoint = f"projects/{quote(project_id, safe='')}/merge_requests/{merge_request_iid}/unapprove"
    unapprove_info = make_gitlab_api_request(ctx, unapprove_endpoint, method="POST")
    
    return unapprove_info

@mcp.tool()
def get_project_merge_requests(ctx: Context, project_id: str, state: str = "all", limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get all merge requests for a project.
    
    Args:
        project_id: The GitLab project ID or URL-encoded path
        state: Filter merge requests by state (all, opened, closed, merged, or locked)
        limit: Maximum number of merge requests to return
    Returns:
        List of merge request objects
    """
    # Get the merge requests
    mrs_endpoint = f"projects/{quote(project_id, safe='')}/merge_requests?state={state}&per_page={limit}"
    mrs_info = make_gitlab_api_request(ctx, mrs_endpoint)
    
    return mrs_info

if __name__ == "__main__":
    try:
        logger.info("Starting GitLab Review MCP server")
        # Initialize and run the server
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        raise 