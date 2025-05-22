"""Utilities for OFGA operations."""

import google.auth
import google.auth.transport.requests
from google.oauth2 import id_token
from loguru import logger
from openfga_sdk import (
    ClientConfiguration,
    OpenFgaClient,
)
from openfga_sdk.credentials import CredentialConfiguration, Credentials

from src.configuration.configuration_model import (
    GeneralConfiguration,
)


# --- Helper Function to Get ID Token ---
def get_gcp_id_token(audience_url: str) -> str | None:
    """Fetches a GCP ID token for the given audience."""
    try:
        auth_req = google.auth.transport.requests.Request()
        # fetch_id_token will use Application Default Credentials
        # - For local dev: gcloud auth application-default login
        # - On GCP (Cloud Functions, other Cloud Run, GCE, GKE):
        # Service account credentials
        token = id_token.fetch_id_token(auth_req, audience_url)
        logger.info(f"Successfully fetched ID token for audience: {audience_url}")
    except Exception:
        logger.exception("Error fetching ID token for {}", audience_url)
        raise
    else:
        return token  # type: ignore


def get_client(config: GeneralConfiguration) -> OpenFgaClient:
    """Gets an open-fga client."""
    gcp_id_token = get_gcp_id_token(config.server_configuration.api_url)
    fga_credentials = Credentials(
        method="api_token",  # This tells the SDK to use a bearer token
        configuration=CredentialConfiguration(
            api_token=gcp_id_token  # The fetched ID token
        ),
    )
    client_configuration = ClientConfiguration(
        api_url=config.server_configuration.api_url,
        store_id=config.store_for_documents_configuration.store_id,
        authorization_model_id=config.store_for_documents_configuration.authorization_model_id,
        credentials=fga_credentials,
    )
    return OpenFgaClient(client_configuration)
