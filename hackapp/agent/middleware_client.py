"""
Middleware Client
HTTP client for communicating with middleware API
"""

import requests
from typing import Optional


class MiddlewareClient:
    """Client for HackApp Middleware API"""

    def __init__(self, base_url: str, token: str, timeout: int = 30):
        """
        Initialize middleware client

        Args:
            base_url: Middleware base URL
            token: Authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        })

    def trigger_workflow(self, hotkey: str, context: dict) -> dict:
        """
        Trigger a workflow

        Args:
            hotkey: Hotkey that was pressed
            context: Context dictionary

        Returns:
            Workflow response dictionary

        Raises:
            MiddlewareError: If request fails
        """
        url = f"{self.base_url}/api/trigger"

        payload = {
            "hotkey": hotkey,
            "context": context
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )

            # Check for HTTP errors
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            raise MiddlewareError(
                "Request timeout - middleware not responding",
                error_code="TIMEOUT"
            )
        except requests.exceptions.ConnectionError:
            raise MiddlewareError(
                f"Cannot connect to middleware at {self.base_url}",
                error_code="CONNECTION_ERROR"
            )
        except requests.exceptions.HTTPError as e:
            error_msg = e.response.text if hasattr(e.response, 'text') else str(e)
            raise MiddlewareError(
                f"Middleware error: {error_msg}",
                error_code=f"HTTP_{e.response.status_code}"
            )
        except Exception as e:
            raise MiddlewareError(
                f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )

    def health_check(self) -> bool:
        """
        Check if middleware is healthy

        Returns:
            True if healthy, False otherwise
        """
        url = f"{self.base_url}/api/health"

        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            return data.get('status') == 'healthy'

        except Exception:
            return False

    def list_workflows(self) -> Optional[list]:
        """
        List available workflows

        Returns:
            List of workflows or None if error
        """
        url = f"{self.base_url}/api/workflows"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return data.get('workflows', [])

        except Exception as e:
            print(f"⚠️  Could not list workflows: {e}")
            return None

    def list_visual_workflows(self) -> Optional[list]:
        """
        List available visual workflows with their hotkeys

        Returns:
            List of visual workflows or None if error
        """
        url = f"{self.base_url}/api/visual-workflows"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return data.get('workflows', [])

        except Exception as e:
            print(f"⚠️  Could not list visual workflows: {e}")
            return None

    def execute_visual_workflow(self, workflow_id: str, initial_variables: dict = None) -> dict:
        """
        Execute a visual workflow

        Args:
            workflow_id: Workflow ID to execute
            initial_variables: Optional dict of variables to pass to workflow (e.g., transcription)

        Returns:
            Execution result dictionary

        Raises:
            MiddlewareError: If request fails
        """
        url = f"{self.base_url}/api/visual-workflows/{workflow_id}/execute"

        payload = {}
        if initial_variables:
            payload['initial_variables'] = initial_variables

        try:
            response = self.session.post(
                url,
                json=payload if payload else None,
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise MiddlewareError(
                "Request timeout - middleware not responding",
                error_code="TIMEOUT"
            )
        except requests.exceptions.HTTPError as e:
            error_msg = e.response.text if hasattr(e.response, 'text') else str(e)
            raise MiddlewareError(
                f"Middleware error: {error_msg}",
                error_code=f"HTTP_{e.response.status_code}"
            )
        except Exception as e:
            raise MiddlewareError(
                f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )

    def report_picked_coordinates(self, field_name: str, x: int, y: int) -> bool:
        """
        Report picked coordinates to middleware

        Args:
            field_name: Name of the field being picked
            x: X coordinate
            y: Y coordinate

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/picker/coordinates"

        try:
            response = self.session.post(
                url,
                json={
                    "field_name": field_name,
                    "x": x,
                    "y": y
                },
                timeout=5
            )

            response.raise_for_status()
            return True

        except Exception as e:
            print(f"⚠️  Could not report coordinates: {e}")
            return False


class MiddlewareError(Exception):
    """Exception for middleware client errors"""

    def __init__(self, message: str, error_code: str = "ERROR"):
        super().__init__(message)
        self.error_code = error_code


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing middleware client...")
    print("=" * 60)

    # Test with default config
    client = MiddlewareClient(
        base_url="http://localhost:5000",
        token="hackathon_demo_token"
    )

    print("\n1. Health Check:")
    try:
        healthy = client.health_check()
        if healthy:
            print("   ✅ Middleware is healthy")
        else:
            print("   ❌ Middleware is not healthy")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n2. List Workflows:")
    try:
        workflows = client.list_workflows()
        if workflows:
            print(f"   ✅ Found {len(workflows)} workflows:")
            for wf in workflows:
                print(f"      • {wf.get('workflow_id')}: {wf.get('hotkey')}")
        else:
            print("   ⚠️  No workflows found")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n✅ Middleware client tests complete!")
    print("   Note: Start middleware server for full functionality")
