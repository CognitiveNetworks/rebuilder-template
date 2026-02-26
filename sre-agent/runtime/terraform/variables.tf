variable "project_id" {
  description = "GCP project ID or AWS account context"
  type        = string
}

variable "region" {
  description = "Cloud region for deployment"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the SRE agent service"
  type        = string
  default     = "sre-agent"
}

variable "image" {
  description = "Container image URI for the SRE agent"
  type        = string
}

variable "llm_api_key_secret" {
  description = "Secret manager reference for the LLM API key. Not needed for Vertex AI (uses ADC)."
  type        = string
  default     = ""
}

variable "llm_model" {
  description = "LLM model ID. Examples: google/gemini-2.0-flash (Vertex AI), gpt-4o (GitHub Models/OpenAI)"
  type        = string
  default     = "gpt-4o"
}

variable "llm_model_escalation" {
  description = "Stronger LLM model for complex incidents. If set, the agent starts with llm_model and switches to this after llm_escalation_turn turns."
  type        = string
  default     = ""
}

variable "llm_escalation_turn" {
  description = "Turn number at which to switch to the escalation model (default: 5)"
  type        = number
  default     = 5
}

variable "llm_api_base_url" {
  description = "LLM API base URL. For Vertex AI: https://REGION-aiplatform.googleapis.com/v1beta1/projects/PROJECT/locations/REGION/endpoints/openapi"
  type        = string
  default     = "https://models.inference.ai.azure.com"
}

variable "pagerduty_api_token_secret" {
  description = "Secret manager reference for the PagerDuty API token"
  type        = string
}

variable "pagerduty_routing_key_secret" {
  description = "Secret Manager reference for the PagerDuty Events API v2 integration key. Required for GCP Direct mode — the agent uses this to create PagerDuty incidents on escalation."
  type        = string
  default     = ""
}

variable "pagerduty_webhook_secret" {
  description = "Secret manager reference for the PagerDuty webhook signing secret (legacy PD webhook mode only)"
  type        = string
  default     = ""
}

variable "ops_auth_token_secret" {
  description = "Secret manager reference for the /ops/* endpoint auth token"
  type        = string
}

variable "service_registry" {
  description = "Comma-separated service registry: name|url|critical"
  type        = string
}

variable "webhook_invoker_member" {
  description = "IAM principal allowed to invoke the webhook endpoint. Defaults to allUsers because PagerDuty cannot present GCP IAM credentials — security is enforced by HMAC webhook signature verification."
  type        = string
  default     = "allUsers"
}
