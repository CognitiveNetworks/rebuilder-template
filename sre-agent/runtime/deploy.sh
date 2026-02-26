#!/usr/bin/env bash
#
# deploy.sh — Automated SRE agent deployment with PagerDuty integration
#
# Deploys the SRE agent to Cloud Run, creates PagerDuty webhook, and
# wires everything together. Credentials needed:
#   - GCP auth via gcloud ADC
#   - LLM_API_KEY env var (GitHub PAT or OpenAI key) — NOT needed with --vertex-ai
#   - PAGERDUTY_API_TOKEN env var
#
# Usage:
#   ./deploy.sh <project-dir> --gcp-project <id> --service-url <url> [options]
#
# Example:
#   ./deploy.sh ../../rebuild-inputs/orderflow \
#     --gcp-project my-gcp-project \
#     --service-url https://orderflow-abc123.run.app

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/terraform"

# --- Defaults ---
REGION="us-central1"
SERVICE_NAME=""
PD_SERVICE_ID=""
ESCALATION_POLICY_ID=""
IMAGE=""
SKIP_BUILD=false
SKIP_PAGERDUTY=false
GCP_DIRECT=false
PD_ROUTING_KEY=""
DRY_RUN=false
VERTEX_AI=false
LLM_MODEL=""
LLM_API_BASE_URL=""

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${BLUE}[deploy]${NC} $*"; }
ok()    { echo -e "${GREEN}[  ok  ]${NC} $*"; }
warn()  { echo -e "${YELLOW}[ warn ]${NC} $*"; }
err()   { echo -e "${RED}[error ]${NC} $*" >&2; }
step()  { echo -e "\n${BLUE}━━━ $* ━━━${NC}"; }

usage() {
    cat <<'EOF'
Usage: ./deploy.sh <project-dir> --gcp-project <id> --service-url <url> [options]

Required:
  <project-dir>                 Path to rebuild-inputs/<project>/ (must contain scope.md)
  --gcp-project <id>            GCP project ID
  --service-url <url>           URL of the monitored service

Optional:
  --region <region>             GCP region (default: us-central1)
  --service-name <name>         Override service name (default: from scope.md)
  --pagerduty-service-id <id>   Reuse existing PagerDuty service
  --escalation-policy-id <id>   PagerDuty escalation policy for new service
  --image <uri>                 Container image URI (default: build and push)
  --skip-build                  Skip Docker build and push
  --skip-pagerduty              Skip PagerDuty setup
  --gcp-direct                  GCP Direct mode (recommended): creates a GCP webhook
                                notification channel instead of PagerDuty webhook.
                                Alerts go directly to the SRE agent; PagerDuty incidents
                                are only created when the agent escalates.
  --pagerduty-routing-key <key> PagerDuty Events API v2 integration key (required for
                                --gcp-direct mode — used to create incidents on escalation)
  --vertex-ai                   Use Vertex AI (Gemini) as LLM provider. Uses ADC for auth
                                instead of LLM_API_KEY. Recommended for GCP projects.
  --llm-model <model>           Override LLM model (default: google/gemini-2.0-flash for
                                Vertex AI, gpt-4o for other providers)
  --dry-run                     Show plan without executing

Environment variables:
  LLM_API_KEY                   LLM API key (not needed with --vertex-ai)
  PAGERDUTY_API_TOKEN           PagerDuty API token (unless --skip-pagerduty)

GCP auth: gcloud auth application-default login
EOF
    exit 1
}

# --- Argument parsing ---

PROJECT_DIR=""
GCP_PROJECT=""
SERVICE_URL=""

parse_args() {
    if [[ $# -lt 1 ]]; then
        usage
    fi

    PROJECT_DIR="$1"
    shift

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --gcp-project)        GCP_PROJECT="$2"; shift 2 ;;
            --service-url)        SERVICE_URL="$2"; shift 2 ;;
            --region)             REGION="$2"; shift 2 ;;
            --service-name)       SERVICE_NAME="$2"; shift 2 ;;
            --pagerduty-service-id) PD_SERVICE_ID="$2"; shift 2 ;;
            --escalation-policy-id) ESCALATION_POLICY_ID="$2"; shift 2 ;;
            --image)              IMAGE="$2"; shift 2 ;;
            --skip-build)         SKIP_BUILD=true; shift ;;
            --skip-pagerduty)     SKIP_PAGERDUTY=true; shift ;;
            --gcp-direct)         GCP_DIRECT=true; shift ;;
            --pagerduty-routing-key) PD_ROUTING_KEY="$2"; shift 2 ;;
            --vertex-ai)          VERTEX_AI=true; shift ;;
            --llm-model)          LLM_MODEL="$2"; shift 2 ;;
            --dry-run)            DRY_RUN=true; shift ;;
            -h|--help)            usage ;;
            *)                    err "Unknown option: $1"; usage ;;
        esac
    done
}

# --- Validation ---

validate_prerequisites() {
    step "Validating prerequisites"

    local failed=false

    # Project directory
    if [[ ! -d "$PROJECT_DIR" ]]; then
        err "Project directory does not exist: $PROJECT_DIR"
        failed=true
    elif [[ ! -f "$PROJECT_DIR/scope.md" ]]; then
        err "scope.md not found in $PROJECT_DIR"
        failed=true
    fi

    # Required flags
    if [[ -z "$GCP_PROJECT" ]]; then
        err "Missing required flag: --gcp-project"
        failed=true
    fi
    if [[ -z "$SERVICE_URL" ]]; then
        err "Missing required flag: --service-url"
        failed=true
    fi

    # Environment variables
    if [[ "$VERTEX_AI" == "false" && -z "${LLM_API_KEY:-}" ]]; then
        err "LLM_API_KEY environment variable is required (or use --vertex-ai)"
        failed=true
    fi
    if [[ "$SKIP_PAGERDUTY" == "false" && -z "${PAGERDUTY_API_TOKEN:-}" ]]; then
        err "PAGERDUTY_API_TOKEN environment variable is required (or use --skip-pagerduty)"
        failed=true
    fi

    # CLI tools
    if ! command -v gcloud &>/dev/null; then
        err "gcloud CLI not found. Install: brew install --cask gcloud-cli"
        failed=true
    fi
    if ! command -v terraform &>/dev/null; then
        err "terraform CLI not found. Install: brew install terraform"
        failed=true
    fi
    if [[ "$SKIP_BUILD" == "false" ]] && ! command -v docker &>/dev/null; then
        err "docker not found (required for build). Install Docker or use --skip-build"
        failed=true
    fi

    # GCP auth check
    if ! gcloud auth application-default print-access-token &>/dev/null 2>&1; then
        err "GCP not authenticated. Run: gcloud auth application-default login"
        failed=true
    fi

    if [[ "$failed" == "true" ]]; then
        exit 1
    fi

    ok "All prerequisites met"
}

# --- Service name extraction ---

extract_service_name() {
    step "Extracting service name"

    if [[ -n "$SERVICE_NAME" ]]; then
        ok "Using provided service name: $SERVICE_NAME"
        return
    fi

    local scope_file="$PROJECT_DIR/scope.md"
    local found=false
    local next_non_empty=false

    while IFS= read -r line; do
        if [[ "$next_non_empty" == "true" ]]; then
            line="$(echo "$line" | sed 's/^[> *]*//; s/[* ]*$//; s/^\[//; s/\]$//')"
            if [[ -n "$line" && "$line" != *"new repository"* ]]; then
                SERVICE_NAME="$line"
                found=true
                break
            fi
        fi
        if [[ "$line" == *"Target Repository"* ]]; then
            next_non_empty=true
        fi
    done < "$scope_file"

    if [[ "$found" == "false" || -z "$SERVICE_NAME" ]]; then
        err "Could not extract service name from scope.md Target Repository field"
        err "Use --service-name to provide it manually"
        exit 1
    fi

    # Sanitize: lowercase, replace spaces/underscores with hyphens
    SERVICE_NAME="$(echo "$SERVICE_NAME" | tr '[:upper:]' '[:lower:]' | tr ' _' '-' | tr -cd 'a-z0-9-')"

    ok "Service name: $SERVICE_NAME"
}

# --- GCP Secret Manager ---

store_secret() {
    local name="$1"
    local value="$2"

    if gcloud secrets describe "$name" --project="$GCP_PROJECT" &>/dev/null 2>&1; then
        echo -n "$value" | gcloud secrets versions add "$name" \
            --project="$GCP_PROJECT" \
            --data-file=- \
            --quiet
        log "Updated secret: $name"
    else
        echo -n "$value" | gcloud secrets create "$name" \
            --project="$GCP_PROJECT" \
            --data-file=- \
            --replication-policy=automatic \
            --quiet
        log "Created secret: $name"
    fi
}

setup_secrets() {
    step "Storing secrets in GCP Secret Manager"

    # Enable Secret Manager API
    gcloud services enable secretmanager.googleapis.com --project="$GCP_PROJECT" --quiet

    if [[ "$VERTEX_AI" == "false" ]]; then
        store_secret "llm-api-key" "$LLM_API_KEY"
    else
        log "Vertex AI mode: skipping llm-api-key (using ADC)"
    fi
    store_secret "pagerduty-api-token" "${PAGERDUTY_API_TOKEN:-placeholder}"

    # Auto-generate ops-auth-token if it doesn't already exist
    if gcloud secrets describe "ops-auth-token" --project="$GCP_PROJECT" &>/dev/null 2>&1; then
        log "ops-auth-token already exists, keeping current value"
    else
        local ops_token
        ops_token="$(openssl rand -base64 32)"
        store_secret "ops-auth-token" "$ops_token"
    fi

    # Store PagerDuty routing key if provided (GCP Direct mode)
    if [[ -n "$PD_ROUTING_KEY" ]]; then
        store_secret "pagerduty-routing-key" "$PD_ROUTING_KEY"
    fi

    ok "Secrets configured"
}

# --- Container image ---

build_and_push_image() {
    step "Building and pushing container image"

    if [[ "$SKIP_BUILD" == "true" ]]; then
        if [[ -z "$IMAGE" ]]; then
            err "When using --skip-build, you must provide --image <uri>"
            exit 1
        fi
        ok "Skipping build, using image: $IMAGE"
        return
    fi

    # Enable Artifact Registry API
    gcloud services enable artifactregistry.googleapis.com --project="$GCP_PROJECT" --quiet

    # Create repository if needed
    if ! gcloud artifacts repositories describe sre-agent \
        --location="$REGION" \
        --project="$GCP_PROJECT" &>/dev/null 2>&1; then
        gcloud artifacts repositories create sre-agent \
            --repository-format=docker \
            --location="$REGION" \
            --project="$GCP_PROJECT" \
            --quiet
        log "Created Artifact Registry repository: sre-agent"
    fi

    IMAGE="${REGION}-docker.pkg.dev/${GCP_PROJECT}/sre-agent/sre-agent:latest"

    # Copy project-specific WINDSURF_SRE.md into the build context if it exists.
    # The Dockerfile COPYs sre-agent/WINDSURF_SRE.md into the container.
    # The template version has placeholders — we need the populated version.
    local sre_prompt_src="$PROJECT_DIR/sre-agent/WINDSURF_SRE.md"
    local sre_prompt_dest="$SCRIPT_DIR/../WINDSURF_SRE.md"
    local prompt_swapped=false
    if [[ -f "$sre_prompt_src" ]]; then
        log "Copying project-specific WINDSURF_SRE.md into build context"
        cp "$sre_prompt_dest" "$sre_prompt_dest.template.bak"
        cp "$sre_prompt_src" "$sre_prompt_dest"
        prompt_swapped=true
    else
        warn "No project-specific WINDSURF_SRE.md found at $sre_prompt_src"
        warn "The container will use the generic template — populate it before deploying"
    fi

    log "Building image: $IMAGE"
    docker build --platform linux/amd64 -f "$SCRIPT_DIR/Dockerfile" -t "$IMAGE" "$SCRIPT_DIR/.."

    # Restore the template after building
    if [[ "$prompt_swapped" == "true" ]]; then
        mv "$sre_prompt_dest.template.bak" "$sre_prompt_dest"
        log "Restored generic WINDSURF_SRE.md template"
    fi

    log "Pushing image..."
    docker push "$IMAGE"

    ok "Image pushed: $IMAGE"
}

# --- Terraform ---

terraform_apply() {
    local phase="$1"
    local webhook_secret_name="${2:-}"

    step "Terraform apply (Phase $phase)"

    local service_registry="${SERVICE_NAME}|${SERVICE_URL}|true"

    # Resolve LLM settings
    local llm_model_resolved="${LLM_MODEL}"
    local llm_base_url_resolved="${LLM_API_BASE_URL}"
    local llm_key_secret="llm-api-key"

    local llm_escalation_model=""
    local llm_escalation_turn="5"

    if [[ "$VERTEX_AI" == "true" ]]; then
        llm_key_secret=""  # Vertex AI uses ADC, no secret needed
        if [[ -z "$llm_model_resolved" ]]; then
            llm_model_resolved="google/gemini-2.0-flash"
        fi
        if [[ -z "$llm_base_url_resolved" ]]; then
            llm_base_url_resolved="https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${GCP_PROJECT}/locations/${REGION}/endpoints/openapi"
        fi
        # Default escalation model for Vertex AI: upgrade to Pro after 5 turns
        llm_escalation_model="google/gemini-2.5-pro"
        log "Vertex AI mode: model=$llm_model_resolved escalation=$llm_escalation_model@turn$llm_escalation_turn"
    else
        if [[ -z "$llm_model_resolved" ]]; then
            llm_model_resolved="gpt-4o"
        fi
        if [[ -z "$llm_base_url_resolved" ]]; then
            llm_base_url_resolved="https://models.inference.ai.azure.com"
        fi
    fi

    # Generate tfvars
    cat > "$TERRAFORM_DIR/deploy.auto.tfvars" <<EOF
project_id                 = "${GCP_PROJECT}"
region                     = "${REGION}"
service_name               = "sre-agent"
image                      = "${IMAGE}"
llm_api_key_secret         = "${llm_key_secret}"
llm_model                  = "${llm_model_resolved}"
llm_model_escalation       = "${llm_escalation_model}"
llm_escalation_turn        = ${llm_escalation_turn}
llm_api_base_url           = "${llm_base_url_resolved}"
pagerduty_api_token_secret = "pagerduty-api-token"
ops_auth_token_secret      = "ops-auth-token"
pagerduty_webhook_secret       = "${webhook_secret_name}"
pagerduty_routing_key_secret   = "${PD_ROUTING_KEY:+pagerduty-routing-key}"
service_registry           = "${service_registry}"
EOF

    # Enable required APIs
    gcloud services enable run.googleapis.com --project="$GCP_PROJECT" --quiet
    if [[ "$VERTEX_AI" == "true" ]]; then
        gcloud services enable aiplatform.googleapis.com --project="$GCP_PROJECT" --quiet
    fi

    (
        cd "$TERRAFORM_DIR"
        terraform init -input=false -no-color
        terraform apply -auto-approve -input=false -no-color
    )

    ok "Terraform Phase $phase complete"
}

get_terraform_output() {
    local key="$1"
    (cd "$TERRAFORM_DIR" && terraform output -raw "$key" 2>/dev/null)
}

# --- PagerDuty setup ---

setup_pagerduty() {
    local webhook_url="$1"

    step "Setting up PagerDuty"

    local pd_helper="$SCRIPT_DIR/pagerduty_setup.py"

    # Find or create PagerDuty service
    local pd_result
    local pd_args="--name $SERVICE_NAME"
    if [[ -n "$ESCALATION_POLICY_ID" ]]; then
        pd_args="$pd_args --escalation-policy-id $ESCALATION_POLICY_ID"
    fi

    if [[ -n "$PD_SERVICE_ID" ]]; then
        log "Using provided PagerDuty service ID: $PD_SERVICE_ID"
    else
        pd_result="$(python3 "$pd_helper" find-or-create-service $pd_args 2>&1)" || {
            err "PagerDuty service setup failed: $pd_result"
            exit 1
        }
        # Extract last line of JSON (skip any debug/warning output)
        pd_result="$(echo "$pd_result" | grep '^{' | tail -1)"
        if ! echo "$pd_result" | python3 -c "import sys,json; json.load(sys.stdin)" &>/dev/null; then
            err "PagerDuty setup returned invalid JSON: $pd_result"
            exit 1
        fi
        PD_SERVICE_ID="$(echo "$pd_result" | python3 -c "import sys,json; print(json.load(sys.stdin)['service_id'])")"
        local pd_created="$(echo "$pd_result" | python3 -c "import sys,json; print(json.load(sys.stdin)['created'])")"
        if [[ "$pd_created" == "True" ]]; then
            log "Created PagerDuty service: $PD_SERVICE_ID"
        else
            log "Found existing PagerDuty service: $PD_SERVICE_ID"
        fi
    fi

    # Create webhook subscription
    local wh_result
    wh_result="$(python3 "$pd_helper" create-webhook \
        --service-id "$PD_SERVICE_ID" \
        --url "$webhook_url" \
        --description "SRE agent webhook for $SERVICE_NAME" 2>&1)" || {
        err "PagerDuty webhook setup failed: $wh_result"
        exit 1
    }
    # Extract last line of JSON (skip any debug/warning output)
    wh_result="$(echo "$wh_result" | grep '^{' | tail -1)"
    if ! echo "$wh_result" | python3 -c "import sys,json; json.load(sys.stdin)" &>/dev/null; then
        err "PagerDuty webhook returned invalid JSON: $wh_result"
        exit 1
    fi

    local wh_created="$(echo "$wh_result" | python3 -c "import sys,json; print(json.load(sys.stdin)['created'])")"
    local wh_secret="$(echo "$wh_result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('secret') or '')")"
    local wh_id="$(echo "$wh_result" | python3 -c "import sys,json; print(json.load(sys.stdin)['subscription_id'])")"

    if [[ "$wh_created" == "True" ]]; then
        log "Created webhook subscription: $wh_id"
    else
        log "Webhook subscription already exists: $wh_id"
    fi

    # Store the signing secret in GCP Secret Manager
    if [[ -n "$wh_secret" ]]; then
        store_secret "pagerduty-webhook-signing-secret" "$wh_secret"
        ok "Webhook signing secret stored in GCP Secret Manager"
        echo "pagerduty-webhook-signing-secret"
    else
        warn "No new signing secret returned (webhook may already exist)"
        # Check if the secret already exists in GCP SM
        if gcloud secrets describe "pagerduty-webhook-signing-secret" --project="$GCP_PROJECT" &>/dev/null 2>&1; then
            echo "pagerduty-webhook-signing-secret"
        else
            echo ""
        fi
    fi
}

# --- GCP Direct mode ---

setup_gcp_direct() {
    local sre_agent_url="$1"

    step "Setting up GCP Direct alert routing"

    if [[ -z "$PD_ROUTING_KEY" ]]; then
        err "--pagerduty-routing-key is required for --gcp-direct mode"
        err "Get it from PagerDuty > Service > Integrations > Events API v2 > Integration Key"
        exit 1
    fi

    # Get the ops-auth-token for the webhook URL
    local ops_token
    ops_token="$(gcloud secrets versions access latest --secret=ops-auth-token --project="$GCP_PROJECT")"

    local webhook_target="${sre_agent_url}/webhook/gcp?auth_token=${ops_token}"

    # Create GCP webhook notification channel
    log "Creating GCP webhook notification channel..."
    local channel_name
    channel_name="$(gcloud beta monitoring channels create \
        --type=webhook_tokenauth \
        --display-name="SRE Agent (GCP Direct)" \
        --channel-labels="url=${webhook_target}" \
        --project="$GCP_PROJECT" \
        --format="value(name)" 2>&1)" || {
        err "Failed to create notification channel: $channel_name"
        exit 1
    }

    ok "Notification channel created: $channel_name"
    log "GCP alerts will be sent directly to: ${sre_agent_url}/webhook/gcp"
    log "PagerDuty incidents will only be created when the agent escalates (routing key configured)"
}

# --- Verification ---

verify_deployment() {
    local service_url="$1"
    local webhook_url="$2"

    step "Verifying deployment"

    local health_status
    if health_status="$(curl -sf "${service_url}/health" 2>/dev/null)"; then
        ok "Health check passed"
    else
        warn "Health check failed — the service may still be starting"
    fi

    echo ""
    echo -e "${GREEN}━━━ Deployment Summary ━━━${NC}"
    echo ""
    echo "  Service URL:    $service_url"
    if [[ "$GCP_DIRECT" == "true" ]]; then
        echo "  GCP Webhook:    ${service_url}/webhook/gcp"
    fi
    echo "  PD Webhook:     $webhook_url"
    echo "  GCP Project:    $GCP_PROJECT"
    echo "  Region:         $REGION"
    echo "  Service Name:   $SERVICE_NAME"
    echo "  Monitored:      $SERVICE_URL"
    if [[ -n "$PD_SERVICE_ID" ]]; then
        echo "  PagerDuty SVC:  $PD_SERVICE_ID"
    fi
    echo ""
    echo "  Secrets in GCP Secret Manager:"
    echo "    llm-api-key              LLM API key"
    echo "    pagerduty-api-token      PagerDuty API token"
    echo "    ops-auth-token           Auto-generated auth token for /ops/* endpoints"
    if [[ -n "$PD_ROUTING_KEY" ]]; then
        echo "    pagerduty-routing-key    PagerDuty Events API v2 integration key"
    fi
    if [[ "$SKIP_PAGERDUTY" == "false" && "$GCP_DIRECT" == "false" ]]; then
        echo "    pagerduty-webhook-signing-secret  PD webhook HMAC signing secret"
    fi
    echo ""
}

# --- Dry run ---

print_dry_run() {
    step "Dry run — no changes will be made"

    echo ""
    echo "  Project directory: $PROJECT_DIR"
    echo "  GCP project:       $GCP_PROJECT"
    echo "  Region:            $REGION"
    echo "  Service name:      $SERVICE_NAME"
    echo "  Monitored URL:     $SERVICE_URL"
    echo "  Image:             ${IMAGE:-<will be built>}"
    echo "  Skip build:        $SKIP_BUILD"
    echo "  Skip PagerDuty:    $SKIP_PAGERDUTY"
    echo ""
    echo "  Steps that would execute:"
    echo "    1. Store LLM_API_KEY in GCP Secret Manager"
    echo "    2. Store PAGERDUTY_API_TOKEN in GCP Secret Manager"
    echo "    3. Generate and store ops-auth-token in GCP Secret Manager"
    if [[ "$SKIP_BUILD" == "false" ]]; then
        echo "    4. Build and push container image to Artifact Registry"
    fi
    echo "    5. Terraform apply Phase 1 — deploy Cloud Run"
    if [[ "$SKIP_PAGERDUTY" == "false" ]]; then
        echo "    6. Find or create PagerDuty service: $SERVICE_NAME"
        echo "    7. Create webhook subscription pointing to Cloud Run"
        echo "    8. Store webhook signing secret in GCP Secret Manager"
        echo "    9. Terraform apply Phase 2 — inject webhook secret"
    fi
    echo "   10. Verify health check"
    echo ""
}

# --- Main ---

main() {
    parse_args "$@"
    validate_prerequisites
    extract_service_name

    if [[ "$DRY_RUN" == "true" ]]; then
        print_dry_run
        exit 0
    fi

    # Step 1: Secrets
    setup_secrets

    # Step 2: Build
    build_and_push_image

    # Step 3: Phase 1 Terraform (no webhook secret yet)
    terraform_apply 1 ""

    local service_url
    local webhook_url
    service_url="$(get_terraform_output service_url)"
    webhook_url="$(get_terraform_output webhook_url)"

    # Step 4: Alert routing setup
    local webhook_secret_name=""
    if [[ "$GCP_DIRECT" == "true" ]]; then
        setup_gcp_direct "$service_url"
    elif [[ "$SKIP_PAGERDUTY" == "false" ]]; then
        webhook_secret_name="$(setup_pagerduty "$webhook_url")"
    fi

    # Step 5: Phase 2 Terraform (with webhook secret if PD mode)
    if [[ -n "$webhook_secret_name" ]]; then
        terraform_apply 2 "$webhook_secret_name"
    else
        log "No webhook secret to inject, skipping Phase 2"
    fi

    # Step 6: Verify
    verify_deployment "$service_url" "$webhook_url"
}

main "$@"
