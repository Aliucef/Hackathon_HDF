"""
Connector Abstraction
Handles external service API calls
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from middleware.models import ConnectorConfig


class Connector(ABC):
    """Abstract base class for connectors"""

    def __init__(self, config: ConnectorConfig):
        """
        Initialize connector

        Args:
            config: Connector configuration
        """
        self.config = config

    @abstractmethod
    def execute(self, endpoint: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an API call

        Args:
            endpoint: Endpoint name (from config)
            request_data: Request payload

        Returns:
            Response data dictionary

        Raises:
            ConnectorError: If API call fails
        """
        pass


class ConnectorError(Exception):
    """Exception raised for connector errors"""

    def __init__(self, message: str, error_code: str = "CONNECTOR_ERROR", details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class RestApiConnector(Connector):
    """REST API connector implementation"""

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.session = requests.Session()

        # Set default headers
        if config.headers:
            self.session.headers.update(config.headers)

        # Setup authentication
        if config.auth:
            self._setup_auth()

    def _setup_auth(self):
        """Setup authentication for requests"""
        auth = self.config.auth

        if auth.type == "bearer_token":
            token = auth.token or self._get_token_from_env(auth.token_env)
            self.session.headers['Authorization'] = f'Bearer {token}'

        elif auth.type == "api_key":
            token = auth.token or self._get_token_from_env(auth.token_env)
            header = auth.header or 'X-API-Key'
            self.session.headers[header] = token

        elif auth.type == "basic":
            if auth.username and auth.password:
                self.session.auth = (auth.username, auth.password)

    def _get_token_from_env(self, env_var: Optional[str]) -> str:
        """Get token from environment variable"""
        import os
        if not env_var:
            raise ConnectorError("No token or token_env specified", "AUTH_ERROR")

        token = os.getenv(env_var)
        if not token:
            raise ConnectorError(
                f"Token environment variable '{env_var}' not set",
                "AUTH_ERROR"
            )

        return token

    def _get_endpoint_url(self, endpoint_name: str) -> str:
        """Get full URL for endpoint"""
        if endpoint_name not in self.config.endpoints:
            raise ConnectorError(
                f"Unknown endpoint: {endpoint_name}",
                "INVALID_ENDPOINT",
                {"available_endpoints": list(self.config.endpoints.keys())}
            )

        endpoint_path = self.config.endpoints[endpoint_name]
        return f"{self.config.base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"

    def _make_request(
        self,
        url: str,
        method: str,
        data: Dict[str, Any]
    ) -> requests.Response:
        """
        Make HTTP request with retries

        Args:
            url: Full URL
            method: HTTP method
            data: Request data

        Returns:
            Response object

        Raises:
            ConnectorError: If all retries fail
        """
        retry_policy = self.config.retry_policy
        max_retries = retry_policy.max_retries if retry_policy else 0
        backoff = retry_policy.backoff if retry_policy else "fixed"
        initial_delay = retry_policy.initial_delay if retry_policy else 1.0

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Make request
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=self.config.timeout
                )

                # Check for HTTP errors
                response.raise_for_status()

                return response

            except requests.exceptions.Timeout as e:
                last_error = ConnectorError(
                    f"Request timeout after {self.config.timeout}s",
                    "TIMEOUT",
                    {"attempt": attempt + 1, "max_retries": max_retries}
                )

            except requests.exceptions.ConnectionError as e:
                last_error = ConnectorError(
                    f"Connection error: {str(e)}",
                    "CONNECTION_ERROR",
                    {"attempt": attempt + 1}
                )

            except requests.exceptions.HTTPError as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise ConnectorError(
                        f"HTTP {e.response.status_code}: {e.response.text}",
                        f"HTTP_{e.response.status_code}",
                        {"status_code": e.response.status_code}
                    )

                # Retry on server errors (5xx)
                last_error = ConnectorError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    "SERVER_ERROR",
                    {"attempt": attempt + 1, "status_code": e.response.status_code}
                )

            except Exception as e:
                last_error = ConnectorError(
                    f"Unexpected error: {str(e)}",
                    "UNKNOWN_ERROR",
                    {"attempt": attempt + 1}
                )

            # If not last attempt, wait before retry
            if attempt < max_retries:
                if backoff == "exponential":
                    delay = initial_delay * (2 ** attempt)
                else:
                    delay = initial_delay

                time.sleep(delay)

        # All retries exhausted
        raise last_error

    def execute(
        self,
        endpoint: str,
        request_data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Execute API call to external service

        Args:
            endpoint: Endpoint name from config
            request_data: Request payload
            method: HTTP method (default: POST)

        Returns:
            Response data dictionary

        Raises:
            ConnectorError: If API call fails
        """
        url = self._get_endpoint_url(endpoint)

        try:
            response = self._make_request(url, method, request_data)

            # Parse JSON response
            try:
                return response.json()
            except ValueError:
                raise ConnectorError(
                    "Response is not valid JSON",
                    "INVALID_RESPONSE",
                    {"content": response.text[:200]}
                )

        except ConnectorError:
            raise
        except Exception as e:
            raise ConnectorError(
                f"Unexpected error: {str(e)}",
                "UNKNOWN_ERROR"
            )


class ConnectorRegistry:
    """Registry for managing connectors"""

    def __init__(self):
        self._connectors: Dict[str, Connector] = {}

    def register(self, name: str, connector: Connector):
        """
        Register a connector

        Args:
            name: Connector name
            connector: Connector instance
        """
        self._connectors[name] = connector
        print(f"✅ Registered connector: {name}")

    def get(self, name: str) -> Connector:
        """
        Get a connector by name

        Args:
            name: Connector name

        Returns:
            Connector instance

        Raises:
            KeyError: If connector not found
        """
        if name not in self._connectors:
            raise KeyError(f"Connector not found: {name}. Available: {list(self._connectors.keys())}")

        return self._connectors[name]

    def list(self) -> list:
        """List all registered connector names"""
        return list(self._connectors.keys())


# ============================================================================
# Connector factory
# ============================================================================

def create_connector(config: ConnectorConfig) -> Connector:
    """
    Create a connector from configuration

    Args:
        config: Connector configuration

    Returns:
        Connector instance

    Raises:
        ValueError: If connector type is unknown
    """
    if config.type == "rest_api":
        return RestApiConnector(config)
    elif config.type == "soap":
        raise NotImplementedError("SOAP connectors not yet implemented")
    elif config.type == "custom":
        raise NotImplementedError("Custom connectors not yet implemented")
    else:
        raise ValueError(f"Unknown connector type: {config.type}")


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing connectors...")
    print("=" * 60)

    # Create mock connector config
    from middleware.models import ConnectorConfig, AuthConfig, RetryPolicy

    config = ConnectorConfig(
        type="rest_api",
        base_url="http://httpbin.org",
        auth=AuthConfig(type="none"),
        endpoints={
            "post": "/post",
            "delay": "/delay/2"
        },
        timeout=30,
        retry_policy=RetryPolicy(max_retries=2, backoff="exponential"),
        headers={"User-Agent": "HackApp-Test/1.0"}
    )

    connector = RestApiConnector(config)

    # Test 1: Successful API call
    print("\n1. Test successful API call:")
    try:
        response = connector.execute("post", {"test": "data"})
        print(f"  ✅ Success! Response keys: {list(response.keys())[:5]}")
    except ConnectorError as e:
        print(f"  ❌ Error: {e}")

    # Test 2: Unknown endpoint
    print("\n2. Test unknown endpoint:")
    try:
        response = connector.execute("unknown_endpoint", {})
        print(f"  ❌ Should have failed!")
    except ConnectorError as e:
        print(f"  ✅ Expected error: {e.error_code}")

    # Test connector registry
    print("\n3. Test connector registry:")
    registry = ConnectorRegistry()
    registry.register("test_connector", connector)

    retrieved = registry.get("test_connector")
    print(f"  ✅ Retrieved connector: {type(retrieved).__name__}")

    print("\n✅ Connector tests complete!")
