# Gerrit Review MCP Server

This MCP server provides integration with Gerrit code review system, allowing AI assistants to review code changes and their details through a simple interface.

## Features

The server provides a streamlined tool for code review:

### Review Change
```python
review_change(change_id: str, patchset_number: Optional[str] = None)
```
- Fetches complete change information including files and patch sets
- Shows detailed diff information for each modified file
- Displays file changes, insertions, and deletions
- Supports reviewing specific patch sets
- Returns comprehensive change details including:
  - Project and branch information
  - Author and reviewer details
  - Comments and review history
  - File modifications with diff content
  - Current patch set information

## Prerequisites

- Python 3.10 or higher
- Gerrit HTTP access credentials
- HTTP password generated from Gerrit settings

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd gerrit-review-mcp
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

## Configuration

1. Set up environment variables:
```bash
export GERRIT_HOST="gerrit.example.com"  # Your Gerrit server hostname
export GERRIT_USER="your-username"       # Your Gerrit username
export GERRIT_HTTP_PASSWORD="your-http-password"  # Your Gerrit HTTP password
```

Or create a `.env` file:
```
GERRIT_HOST=gerrit.example.com
GERRIT_USER=your-username
GERRIT_HTTP_PASSWORD=your-http-password
```

2. Generate HTTP password:
- Log into your Gerrit web interface
- Go to Settings > HTTP Credentials
- Generate new password
- Copy the password to your environment or .env file

## Implementation Details

The server uses Gerrit REST API to interact with Gerrit, providing:
- Fast and reliable change information retrieval
- Secure authentication using HTTP digest auth
- Support for various Gerrit REST endpoints
- Clean and maintainable codebase
- HTTPS encryption for secure communication

## Troubleshooting

If you encounter connection issues:
1. Verify your HTTP password is correctly set
2. Check GERRIT_HOST setting
3. Ensure HTTPS access is enabled on Gerrit server
4. Test connection using curl:
   ```bash
   curl -u "username:http-password" https://your-gerrit-host/a/changes/
   ```
5. Verify Gerrit access permissions for your account

## License

This project is licensed under the MIT License.

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
