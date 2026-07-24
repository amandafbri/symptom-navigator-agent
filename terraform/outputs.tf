output "staging_bucket_name" {
  description = "The GCS staging bucket name for ADK deployment"
  value       = google_storage_bucket.adk_staging_bucket.name
}

output "artifact_repository_url" {
  description = "Artifact Registry Docker repository URL"
  value       = google_artifact_registry_repository.agent_repo.name
}

output "service_account_email" {
  description = "Service account email running the Agent Engine"
  value       = google_service_account.agent_sa.email
}
