import requests
from urllib.parse import quote
from django.conf import settings
from rest_framework import status

from apps.core.service.interface import ConnectServiceInterface


class ConnectService(ConnectServiceInterface):
    """Create Kafka Connect connectors and map results to HTTP statuses."""

    def __init__(self):
        """Load the Connect base URL without trailing slashes."""
        self.base_url = settings.KAFKA_CONNECT_URL.rstrip("/")

    def list_connectors(self) -> tuple[list[str] | dict, int]:
        """Fetch all connector names without exposing upstream error details."""
        if not self.base_url:
            return {"error": "not_configured"}, status.HTTP_503_SERVICE_UNAVAILABLE
        try:
            response = requests.get(
                f"{self.base_url}/connectors",
                headers={"Accept": "application/json"},
                timeout=settings.KAFKA_CONNECT_TIMEOUT,
            )
            response.raise_for_status()
            connectors = response.json()
            if not isinstance(connectors, list) or not all(isinstance(name, str) for name in connectors):
                return {"error": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
            return connectors, status.HTTP_200_OK
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return {"error": "unavailable"}, status.HTTP_503_SERVICE_UNAVAILABLE
        except (requests.exceptions.HTTPError, ValueError):
            return {"error": "upstream_error"}, status.HTTP_502_BAD_GATEWAY

    def get_connector(self, source: str) -> tuple[dict, int]:
        """Fetch connector configuration with sensitive properties redacted."""
        if not self.base_url:
            return {"error": "not_configured"}, status.HTTP_503_SERVICE_UNAVAILABLE
        try:
            response = requests.get(
                f"{self.base_url}/connectors/{quote(source, safe='')}/config",
                headers={"Accept": "application/json"},
                timeout=settings.KAFKA_CONNECT_TIMEOUT,
            )
            response.raise_for_status()
            config = response.json()
            if not isinstance(config, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in config.items()
            ):
                return {"error": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
            # Connector properties can include credentials and connection URLs.
            return {
                key: "[redacted]" if any(part in key.lower() for part in (
                    "password", "secret", "token", "credential", "jaas", "connection.url",
                )) else value
                for key, value in config.items()
            }, status.HTTP_200_OK
        except requests.exceptions.HTTPError as error:
            if error.response is not None and error.response.status_code == status.HTTP_404_NOT_FOUND:
                return {"error": "not_found"}, status.HTTP_404_NOT_FOUND
            return {"error": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return {"error": "unavailable"}, status.HTTP_503_SERVICE_UNAVAILABLE
        except ValueError:
            return {"error": "upstream_error"}, status.HTTP_502_BAD_GATEWAY

    def create_connector(self, name: str, db_type: str, config: dict) -> tuple[dict, int]:
        """Return a sanitized response body and HTTP status; db_type is reserved."""
        if not self.base_url:
            return {"message": "not_configured"}, status.HTTP_503_SERVICE_UNAVAILABLE
        try:
            response = requests.post(
                f"{self.base_url}/connectors",
                json={"name": name, "config": config},
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=settings.KAFKA_CONNECT_TIMEOUT,
            )
            response.raise_for_status()
            if response.status_code == status.HTTP_201_CREATED:
                return {"message": "created"}, status.HTTP_201_CREATED
            else:
                return {"error": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
        except requests.exceptions.HTTPError as error:
            code = (
                error.response.status_code
                if error.response is not None
                else status.HTTP_502_BAD_GATEWAY
            )
            message = {
                status.HTTP_400_BAD_REQUEST: error.response.json().get("message", "bad_request") if error.response is not None else "bad_request",
                status.HTTP_404_NOT_FOUND: "not_found",
                status.HTTP_409_CONFLICT: "conflict",
            }.get(code)
            if message is not None:
                return {"error": message}, code
            return {"error": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return {"error": "unavailable"}, status.HTTP_503_SERVICE_UNAVAILABLE
        except (ValueError, UnicodeDecodeError):
            return {"error": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
    
