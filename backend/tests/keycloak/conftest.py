"""Pytest configuration for keycloak tests.

Sets required environment variables before test module import.
"""

import os

os.environ.setdefault("KEYCLOAK_BASE_URL", "http://localhost:8080")
os.environ.setdefault("KEYCLOAK_REALM", "test-realm")
os.environ.setdefault("KEYCLOAK_CLIENT_ID", "dish-booking-agent-api")
