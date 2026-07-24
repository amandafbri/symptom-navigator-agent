variable "project_id" {
  description = "The GCP Project ID to deploy resources"
  type        = string
}

variable "region" {
  description = "GCP Region for Agent Engine deployment"
  type        = string
  default     = "us-central1"
}

variable "agent_name" {
  description = "Display name of the ADK Symptom Navigator Agent"
  type        = string
  default     = "Symptom Navigator Agent"
}
