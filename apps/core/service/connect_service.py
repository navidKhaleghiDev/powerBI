import requests
from django.conf import settings
from rest_framework import status

from apps.core.service.interface import ConnectServiceInterface


class ConnectService(ConnectServiceInterface):
    """Create Kafka Connect connectors and map results to HTTP statuses."""

    def __init__(self):
        """Load the Connect base URL without trailing slashes."""
        self.base_url = settings.KAFKA_CONNECT_URL.rstrip("/")

    def create_connector(self, name: str, db_type: str, config: dict) -> tuple[dict, int]:
        """Return a sanitized response body and HTTP status; db_type is reserved."""
        if not self.base_url:
            return {"message": "not_configured"}, status.HTTP_503_SERVICE_UNAVAILABLE
        try:
            # Bound network waits using the configured Connect timeout.
            response = requests.post(
                f"{self.base_url}/connectors",
                json={"name": name, "config": config},
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=settings.KAFKA_CONNECT_TIMEOUT,
            )
            response.raise_for_status()
            # Only HTTP 201 confirms creation; other successful codes are unexpected.
            if response.status_code == status.HTTP_201_CREATED:
                return {"message": "created"}, status.HTTP_201_CREATED
            else:
                return {"message": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
        except requests.exceptions.HTTPError as error:
            # Do not expose upstream messages, which may contain credentials.
            code = (
                error.response.status_code
                if error.response is not None
                else status.HTTP_502_BAD_GATEWAY
            )
            message = {
                status.HTTP_400_BAD_REQUEST: "rejected",
                status.HTTP_404_NOT_FOUND: "not_found",
                status.HTTP_409_CONFLICT: "conflict",
            }.get(code)
            if message is not None:
                return {"message": message}, code
            return {"message": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return {"message": "unavailable"}, status.HTTP_503_SERVICE_UNAVAILABLE
        except (ValueError, UnicodeDecodeError):
            return {"message": "upstream_error"}, status.HTTP_502_BAD_GATEWAY
    
