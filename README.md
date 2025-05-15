# GitLab MCP for Code Review

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> This project is forked from [cayirtepeomer/gerrit-code-review-mcp](https://github.com/cayirtepeomer/gerrit-code-review-mcp) and adapted for GitLab integration.

An MCP (Model Context Protocol) server for integrating AI assistants like Claude with GitLab's merge requests. This allows AI assistants to review code changes directly through the GitLab API.

## Features

- **Complete Merge Request Analysis**: Fetch full details about merge requests including diffs, commits, and comments
- **File-Specific Diffs**: Analyze changes to specific files within merge requests
- **Version Comparison**: Compare different branches, tags, or commits
- **Review Management**: Add comments, approve, or unapprove merge requests
- **Project Overview**: Get lists of all merge requests in a project

## Installation

### Prerequisites

- Python 3.10+ 
- GitLab personal access token with API scope (read_api, api)
- [Cursor IDE](https://cursor.sh/) or [Claude Desktop App](https://claude.ai/desktop) for MCP integration

### Quick Start

1. Clone this repository:

```bash
git clone https://github.com/mehmetakinn/gitlab-mcp-code-review.git
cd gitlab-mcp-code-review
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your GitLab configuration (see `.env.example` for all options):

```
# Required
GITLAB_TOKEN=your_personal_access_token_here

# Optional settings
GITLAB_HOST=gitlab.com
GITLAB_API_VERSION=v4
LOG_LEVEL=INFO
```

## Configuration Options

The following environment variables can be configured in your `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| GITLAB_TOKEN | Yes | - | Your GitLab personal access token |
| GITLAB_HOST | No | gitlab.com | GitLab instance hostname |
| GITLAB_API_VERSION | No | v4 | GitLab API version to use |
| LOG_LEVEL | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| DEBUG | No | false | Enable debug mode |
| REQUEST_TIMEOUT | No | 30 | API request timeout in seconds |
| MAX_RETRIES | No | 3 | Maximum retry attempts for failed requests |

## Cursor IDE Integration

To use this MCP with Cursor IDE, add this configuration to your `~/.cursor/mcp.json` file:

```json
{
  "mcpServers": {
    "gitlab-mcp-code-review": {
      "command": "/path/to/your/gitlab-mcp-code-review/.venv/bin/python",
      "args": [
        "/path/to/your/gitlab-mcp-code-review/server.py",
        "--transport",
        "stdio"
      ],
      "cwd": "/path/to/your/gitlab-mcp-code-review",
      "env": {
        "PYTHONPATH": "/path/to/your/gitlab-mcp-code-review",
        "VIRTUAL_ENV": "/path/to/your/gitlab-mcp-code-review/.venv",
        "PATH": "/path/to/your/gitlab-mcp-code-review/.venv/bin:/usr/local/bin:/usr/bin:/bin"
      },
      "stdio": true
    }
  }
}
```

Replace `/path/to/your/gitlab-mcp-code-review` with the actual path to your cloned repository.

## Claude Desktop App Integration

To use this MCP with the Claude Desktop App:

1. Open the Claude Desktop App
2. Go to Settings → Advanced → MCP Configuration
3. Add the following configuration:

```json
{
  "mcpServers": {
    "gitlab-mcp-code-review": {
      "command": "/path/to/your/gitlab-mcp-code-review/.venv/bin/python",
      "args": [
        "/path/to/your/gitlab-mcp-code-review/server.py",
        "--transport",
        "stdio"
      ],
      "cwd": "/path/to/your/gitlab-mcp-code-review",
      "env": {
        "PYTHONPATH": "/path/to/your/gitlab-mcp-code-review",
        "VIRTUAL_ENV": "/path/to/your/gitlab-mcp-code-review/.venv",
        "PATH": "/path/to/your/gitlab-mcp-code-review/.venv/bin:/usr/local/bin:/usr/bin:/bin"
      },
      "stdio": true
    }
  }
}
```

Replace `/path/to/your/gitlab-mcp-code-review` with the actual path to your cloned repository.

## Available Tools

The MCP server provides the following tools for interacting with GitLab:

| Tool | Description |
|------|-------------|
| `fetch_merge_request` | Get complete information about a merge request |
| `fetch_merge_request_diff` | Get diffs for a specific merge request |
| `fetch_commit_diff` | Get diff information for a specific commit |
| `compare_versions` | Compare different branches, tags, or commits |
| `add_merge_request_comment` | Add a comment to a merge request |
| `approve_merge_request` | Approve a merge request |
| `unapprove_merge_request` | Unapprove a merge request |
| `get_project_merge_requests` | Get a list of merge requests for a project |

## Usage Examples

### Fetch a Merge Request

```python
# Get details of merge request #5 in project with ID 123
mr = fetch_merge_request("123", "5")
```

### View Specific File Changes

```python
# Get diff for a specific file in a merge request
file_diff = fetch_merge_request_diff("123", "5", "path/to/file.js")
```

### Compare Branches

```python
# Compare develop branch with master branch
diff = compare_versions("123", "develop", "master")
```

### Add a Comment to a Merge Request

```python
# Add a comment to a merge request
comment = add_merge_request_comment("123", "5", "This code looks good!")
```

### Approve a Merge Request

```python
# Approve a merge request and set required approvals to 2
approval = approve_merge_request("123", "5", approvals_required=2)
```

## Troubleshooting

If you encounter issues:

1. Verify your GitLab token has the appropriate permissions (api, read_api)
2. Check your `.env` file settings
3. Ensure your MCP configuration paths are correct
4. Test connection with: `curl -H "Private-Token: your-token" https://gitlab.com/api/v4/projects`
5. Set LOG_LEVEL=DEBUG in your .env file for more detailed logging

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details on the development process.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
