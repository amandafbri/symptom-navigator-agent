terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Google Cloud Storage Bucket for ADK Staging
resource "google_storage_bucket" "adk_staging_bucket" {
  name                     = "${var.project_id}-adk-staging"
  location                 = var.region
  force_destroy            = true
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30
    }
  }
}

# 2. Secret Manager for Secure Key Storage
resource "google_secret_manager_secret" "api_key_secret" {
  secret_id = "symptom_navigator_api_key"
  replication {
    auto {}
  }
}

# 3. Artifact Registry Repository for Docker container images
resource "google_artifact_registry_repository" "agent_repo" {
  location      = var.region
  repository_id = "symptom-navigator-repo"
  description   = "Docker repository for Symptom Navigator Agent"
  format        = "DOCKER"
}

# 4. Service Account for Agent Engine Execution
resource "google_service_account" "agent_sa" {
  account_id   = "symptom-navigator-sa"
  display_name = "Symptom Navigator Agent Service Account"
}

# IAM Role bindings for Vertex AI and Telemetry Logging
resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}
