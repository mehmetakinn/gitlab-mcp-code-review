import unittest
from unittest.mock import patch, MagicMock

# This is a basic test skeleton for the server
# You would need to add more comprehensive tests


class TestGitLabMCP(unittest.TestCase):
    """Test cases for GitLab MCP server"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_ctx = MagicMock()
        self.mock_lifespan_context = MagicMock()
        self.mock_ctx.request_context.lifespan_context = self.mock_lifespan_context
        self.mock_lifespan_context.token = "fake_token"
        self.mock_lifespan_context.host = "gitlab.com"

    @patch('requests.get')
    def test_make_gitlab_api_request(self, mock_get):
        """Test the GitLab API request function"""
        # Import here to avoid module-level imports before patching
        from server import make_gitlab_api_request
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "name": "test_project"}
        mock_get.return_value = mock_response
        
        # Test the function
        result = make_gitlab_api_request(self.mock_ctx, "projects/123")
        
        # Assertions
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": 123, "name": "test_project"})


if __name__ == '__main__':
    unittest.main() 