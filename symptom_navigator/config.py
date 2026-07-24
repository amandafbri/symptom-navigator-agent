import os
from .secrets import get_secret

# ==========================================
# Strategic Model Routing Configuration
# ==========================================

# Fast Model: Low latency & cost for slot checking, symptom matching, quick lookups
FAST_MODEL_NAME = os.getenv("FAST_MODEL_NAME", "gemini-3.1-flash-lite")

# Pro Model: High intelligence for complex clinical triage, safety evaluation & coordinator orchestration
PRO_MODEL_NAME = os.getenv("PRO_MODEL_NAME", "gemini-2.5-pro")

# Cloud environment settings
PROJECT_ID = get_secret("GOOGLE_CLOUD_PROJECT", "amandafurtado-tests")
LOCATION = get_secret("GOOGLE_CLOUD_LOCATION", "us-central1")
GLOBAL_LOCATION = "global"
