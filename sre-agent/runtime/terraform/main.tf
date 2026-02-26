# SRE Agent deployment — Cloud Run (GCP)
#
# For AWS (ECS/Fargate), replace this file with the equivalent
# aws_ecs_service, aws_ecs_task_definition, and ALB resources.
# The container image, env vars, and secrets pattern are the same.

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- Cloud Run Service ---

resource "google_cloud_run_v2_service" "sre_agent" {
  name                = var.service_name
  location            = var.region
  deletion_protection = false

  template {
    containers {
      image = var.image

      ports {
        container_port = 8080
      }

      # LLM_API_KEY — only needed for non-Vertex AI providers.
      # For Vertex AI, the Cloud Run service account uses ADC automatically.
      dynamic "env" {
        for_each = var.llm_api_key_secret != "" ? [1] : []
        content {
          name = "LLM_API_KEY"
          value_source {
            secret_key_ref {
              secret  = var.llm_api_key_secret
              version = "latest"
            }
          }
        }
      }

      env {
        name = "PAGERDUTY_API_TOKEN"
        value_source {
          secret_key_ref {
            secret  = var.pagerduty_api_token_secret
            version = "latest"
          }
        }
      }

      env {
        name = "OPS_AUTH_TOKEN"
        value_source {
          secret_key_ref {
            secret  = var.ops_auth_token_secret
            version = "latest"
          }
        }
      }

      env {
        name  = "SERVICE_REGISTRY"
        value = var.service_registry
      }

      env {
        name  = "LLM_MODEL"
        value = var.llm_model
      }

      env {
        name  = "LLM_API_BASE_URL"
        value = var.llm_api_base_url
      }

      dynamic "env" {
        for_each = var.llm_model_escalation != "" ? [1] : []
        content {
          name  = "LLM_MODEL_ESCALATION"
          value = var.llm_model_escalation
        }
      }

      dynamic "env" {
        for_each = var.llm_model_escalation != "" ? [1] : []
        content {
          name  = "LLM_ESCALATION_TURN"
          value = tostring(var.llm_escalation_turn)
        }
      }

      env {
        name  = "SRE_PROMPT_PATH"
        value = "/app/WINDSURF_SRE.md"
      }

      env {
        name  = "INCIDENTS_DIR"
        value = "/app/incidents"
      }

      dynamic "env" {
        for_each = var.pagerduty_routing_key_secret != "" ? [1] : []
        content {
          name = "PAGERDUTY_ROUTING_KEY"
          value_source {
            secret_key_ref {
              secret  = var.pagerduty_routing_key_secret
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.pagerduty_webhook_secret != "" ? [1] : []
        content {
          name = "PAGERDUTY_WEBHOOK_SECRET"
          value_source {
            secret_key_ref {
              secret  = var.pagerduty_webhook_secret
              version = "latest"
            }
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 5
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        period_seconds = 30
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 3
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# --- IAM: Allow webhook callers to invoke the service ---
#
# Defaults to "allUsers" because both GCP Cloud Monitoring (GCP Direct mode)
# and PagerDuty (legacy mode) send webhooks from their infrastructure and
# cannot present GCP IAM credentials. Security is enforced by:
#   - GCP Direct mode: auth_token query parameter on /webhook/gcp
#   - Legacy PD mode:  HMAC signature verification on /webhook
#
# To restrict further, place an API gateway with OIDC in front of
# Cloud Run and set webhook_invoker_member to the gateway's service account.

# --- IAM: Grant Vertex AI access to Cloud Run service account (Vertex AI mode only) ---
#
# When using Vertex AI as the LLM provider, the Cloud Run service account
# needs the aiplatform.user role to call the chat completions endpoint.
# This is only created when llm_api_key_secret is empty (Vertex AI / ADC mode).

resource "google_project_iam_member" "vertex_ai_user" {
  count   = var.llm_api_key_secret == "" ? 1 : 0
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_cloud_run_v2_service.sre_agent.template[0].service_account}"
}

resource "google_cloud_run_v2_service_iam_member" "webhook_invoker" {
  name     = google_cloud_run_v2_service.sre_agent.name
  location = var.region
  role     = "roles/run.invoker"
  member   = var.webhook_invoker_member
}
