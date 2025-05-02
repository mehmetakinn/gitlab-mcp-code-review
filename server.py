import os
import json
import logging
from typing import Optional, Dict, Any, Union
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
class GerritContext:
    host: str
    user: str
    http_password: Optional[str] = None

def make_gerrit_rest_request(ctx: Context, endpoint: str) -> Dict[str, Any]:
    """Make a REST API request to Gerrit and handle the response"""
    gerrit_ctx = ctx.request_context.lifespan_context
    
    if not gerrit_ctx.http_password:
        logger.error("HTTP password not set in context")
        raise ValueError("HTTP password not set. Please set GERRIT_HTTP_PASSWORD in your environment.")
        
    # Ensure endpoint starts with 'a/' for authenticated requests
    if not endpoint.startswith('a/'):
        endpoint = f'a/{endpoint}'
    
    url = f"https://{gerrit_ctx.host}/{endpoint}"
    auth = requests.auth.HTTPDigestAuth(gerrit_ctx.user, gerrit_ctx.http_password)
    
    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'GerritReviewMCP/1.0'
        }
        response = requests.get(url, auth=auth, headers=headers, verify=True)
        
        if response.status_code == 401:
            logger.error("Authentication failed. Check your credentials.")
            raise Exception("Authentication failed. Please check your Gerrit HTTP password in your account settings.")
            
        response.raise_for_status()
        
        # Remove Gerrit's XSSI prefix if present
        content = response.text
        if content.startswith(")]}'"):
            content = content[4:]
            
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            raise Exception(f"Failed to parse Gerrit response as JSON: {str(e)}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"REST request failed: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response status: {e.response.status_code}")
        raise Exception(f"Failed to make Gerrit REST API request: {str(e)}")

@asynccontextmanager
async def gerrit_lifespan(server: FastMCP) -> AsyncIterator[GerritContext]:
    """Manage Gerrit connection details"""
    host = os.getenv("GERRIT_HOST", "")
    user = os.getenv("GERRIT_USER", "")
    http_password = os.getenv("GERRIT_HTTP_PASSWORD", "")
    
    if not all([host, user]):
        logger.error("Missing required environment variables:")
        if not host: logger.error("- GERRIT_HOST not set")
        if not user: logger.error("- GERRIT_USER not set")
        raise ValueError(
            "Missing required environment variables: GERRIT_HOST, GERRIT_USER. "
            "Please set these in your environment or .env file."
        )

    if not http_password:
        logger.warning("GERRIT_HTTP_PASSWORD not set - REST API calls will fail")
    
    ctx = GerritContext(host=host, user=user, http_password=http_password)
    try:
        yield ctx
    finally:
        pass

# Create MCP server
mcp = FastMCP(
    "Gerrit Review",
    description="MCP server for reviewing Gerrit changes",
    lifespan=gerrit_lifespan,
    dependencies=["python-dotenv", "requests"]
)

@mcp.tool()
def fetch_gerrit_change(ctx: Context, change_id: str, patchset_number: str = None) -> Dict[str, Any]:
    """
    Fetch a Gerrit change and its contents.
    
    Args:
        change_id: The Gerrit change ID to fetch
        patchset_number: Optional patchset number to fetch (defaults to latest)
    Returns:
        Dict containing the raw change information including files and diffs
    """
    # Get change details using REST API with all required information
    change_endpoint = f"a/changes/{change_id}/detail?o=CURRENT_REVISION&o=CURRENT_COMMIT&o=MESSAGES&o=DETAILED_LABELS&o=DETAILED_ACCOUNTS&o=ALL_REVISIONS&o=ALL_COMMITS&o=ALL_FILES&o=COMMIT_FOOTERS"
    change_info = make_gerrit_rest_request(ctx, change_endpoint)
    
    if not change_info:
        raise ValueError(f"Change {change_id} not found")
        
    # Extract project and ref information
    project = change_info.get("project")
    if not project:
        raise ValueError("Project information not found in change")
        
    # Get the target patchset
    current_revision = change_info.get("current_revision")
    revisions = change_info.get("revisions", {})
    
    if patchset_number:
        # Find specific patchset
        target_revision = None
        for rev, rev_info in revisions.items():
            if str(rev_info.get("_number")) == str(patchset_number):
                target_revision = rev
                break
        if not target_revision:
            available_patchsets = sorted([str(info.get("_number")) for info in revisions.values()])
            raise ValueError(f"Patchset {patchset_number} not found. Available patchsets: {', '.join(available_patchsets)}")
    else:
        # Use current revision
        target_revision = current_revision
    
    if not target_revision or target_revision not in revisions:
        raise ValueError("Revision information not found")

    revision_info = revisions[target_revision]
    
    # Process each file
    processed_files = []
    for file_path, file_info in revision_info.get("files", {}).items():
        if file_path == "/COMMIT_MSG":
            continue
            
        # Get the diff for this file
        encoded_path = quote(file_path, safe='')
        diff_endpoint = f"a/changes/{change_id}/revisions/{target_revision}/files/{encoded_path}/diff"
        diff_info = make_gerrit_rest_request(ctx, diff_endpoint)
        
        file_data = {
            "path": file_path,
            "status": file_info.get("status", "MODIFIED"),
            "lines_inserted": file_info.get("lines_inserted", 0),
            "lines_deleted": file_info.get("lines_deleted", 0),
            "size_delta": file_info.get("size_delta", 0),
            "diff": diff_info
        }
        processed_files.append(file_data)
    
    # Return the complete change information
    return {
        "change_info": change_info,
        "project": project,
        "revision": target_revision,
        "patchset": revision_info,
        "files": processed_files
    }

@mcp.tool()
def fetch_patchset_diff(ctx: Context, change_id: str, base_patchset: str, target_patchset: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch differences between two patchsets of a Gerrit change.
    
    Args:
        change_id: The Gerrit change ID
        base_patchset: The base patchset number to compare from
        target_patchset: The target patchset number to compare to
        file_path: Optional specific file path to get diff for. If not provided, returns diffs for all changed files.
    Returns:
        Dict containing the diff information between the patchsets
    """
    # First get the revision info for both patchsets
    change_endpoint = f"a/changes/{change_id}/detail?o=ALL_REVISIONS&o=ALL_FILES"
    change_info = make_gerrit_rest_request(ctx, change_endpoint)
    
    if not change_info:
        raise ValueError(f"Change {change_id} not found")
    
    revisions = change_info.get("revisions", {})
    
    # Find revision hashes for both patchsets
    base_revision = None
    target_revision = None
    for rev, rev_info in revisions.items():
        if str(rev_info.get("_number")) == str(base_patchset):
            base_revision = rev
        if str(rev_info.get("_number")) == str(target_patchset):
            target_revision = rev
            
    if not base_revision or not target_revision:
        available_patchsets = sorted([str(info.get("_number")) for info in revisions.values()])
        raise ValueError(f"Patchset(s) not found. Available patchsets: {', '.join(available_patchsets)}")

    # Get the diff between revisions using Gerrit's comparison endpoint
    diff_endpoint = f"a/changes/{change_id}/revisions/{target_revision}/files"
    if base_revision:
        diff_endpoint += f"?base={base_revision}"
    
    files_diff = make_gerrit_rest_request(ctx, diff_endpoint)
    
    # Process the files that actually changed
    changed_files = {}
    for file_path, file_info in files_diff.items():
        if file_path == "/COMMIT_MSG":
            continue
            
        if file_info.get("status") != "SAME":  # Only include files that actually changed
            # Get detailed diff for this file
            encoded_path = quote(file_path, safe='')
            file_diff_endpoint = f"a/changes/{change_id}/revisions/{target_revision}/files/{encoded_path}/diff"
            if base_revision:
                file_diff_endpoint += f"?base={base_revision}"
            diff_info = make_gerrit_rest_request(ctx, file_diff_endpoint)
            
            changed_files[file_path] = {
                "status": file_info.get("status", "MODIFIED"),
                "lines_inserted": file_info.get("lines_inserted", 0),
                "lines_deleted": file_info.get("lines_deleted", 0),
                "size_delta": file_info.get("size_delta", 0),
                "diff": diff_info
            }
    
    return {
        "base_revision": base_revision,
        "target_revision": target_revision,
        "base_patchset": base_patchset,
        "target_patchset": target_patchset,
        "files": changed_files
    }

if __name__ == "__main__":
    try:
        logger.info("Starting Gerrit Review MCP server")
        # Initialize and run the server
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        raise 