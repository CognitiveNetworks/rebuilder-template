output "service_url" {
  description = "URL of the deployed SRE agent service"
  value       = google_cloud_run_v2_service.sre_agent.uri
}

output "webhook_url" {
  description = "Full webhook URL to configure in PagerDuty"
  value       = "${google_cloud_run_v2_service.sre_agent.uri}/webhook"
}

output "gcp_webhook_url" {
  description = "GCP Direct webhook URL (recommended) — use with GCP notification channel"
  value       = "${google_cloud_run_v2_service.sre_agent.uri}/webhook/gcp"
}

output "service_name" {
  description = "Name of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.sre_agent.name
}
