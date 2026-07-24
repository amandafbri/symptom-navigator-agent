import os
from typing import Optional
from .telemetry import logger

def get_secret(secret_id: str, default_value: Optional[str] = None) -> Optional[str]:
    """Retrieves secret securely from Google Cloud Secret Manager with environment variable fallback.
    
    Args:
        secret_id: The identifier of the secret (e.g., 'GOOGLE_API_KEY').
        default_value: Optional fallback value.
        
    Returns:
        Secret string value or fallback.
    """
    # 1. First check environment variables
    env_val = os.getenv(secret_id)
    if env_val:
        return env_val
        
    # 2. Check GCP Secret Manager if running in GCP environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            logger.info(f"[SECRET_MANAGER] Successfully injected secret '{secret_id}' from Secret Manager.")
            return payload
        except Exception as e:
            logger.debug(f"[SECRET_MANAGER] Secret Manager lookup for '{secret_id}' skipped: {str(e)}")
            
    return default_value
