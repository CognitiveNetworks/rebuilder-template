#!/usr/bin/env python3
"""PagerDuty API helper for deploy.sh.

Handles service and webhook subscription management via the PagerDuty REST API.
All operations are idempotent — safe to run multiple times.

Usage:
    export PAGERDUTY_API_TOKEN=your-token

    # Find or create a PagerDuty service
    python pagerduty_setup.py find-or-create-service --name orderflow-api --escalation-policy-id PABCDEF

    # Create a webhook subscription (returns subscription_id and signing secret)
    python pagerduty_setup.py create-webhook --service-id PABC123 --url https://sre-agent.run.app/webhook

    # List existing webhook subscriptions for a service
    python pagerduty_setup.py list-webhooks --service-id PABC123
"""

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = "https://api.pagerduty.com"


def _get_token():
    token = os.environ.get("PAGERDUTY_API_TOKEN")
    if not token:
        print("Error: PAGERDUTY_API_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)
    return token


def _request(method, path, body=None):
    token = _get_token()
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": f"Token token={token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"Error: PagerDuty API returned {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)


def find_or_create_service(name, escalation_policy_id):
    """Find a PagerDuty service by name, or create one if it doesn't exist."""
    resp = _request("GET", f"/services?query={name}&limit=100")
    for svc in resp.get("services", []):
        if svc["name"].lower() == name.lower():
            result = {"service_id": svc["id"], "created": False}
            print(json.dumps(result))
            return

    if not escalation_policy_id:
        print("Error: --escalation-policy-id is required when creating a new service", file=sys.stderr)
        sys.exit(1)

    body = {
        "service": {
            "name": name,
            "description": f"Monitored by SRE agent — {name}",
            "escalation_policy": {
                "id": escalation_policy_id,
                "type": "escalation_policy_reference",
            },
            "alert_creation": "create_alerts_and_incidents",
        }
    }
    resp = _request("POST", "/services", body)
    result = {"service_id": resp["service"]["id"], "created": True}
    print(json.dumps(result))


def create_webhook(service_id, url, description=None):
    """Create a webhook subscription. Skips if one with the same URL already exists."""
    existing = _list_webhooks_for_service(service_id)
    for sub in existing:
        dm = sub.get("delivery_method", {})
        if dm.get("url") == url:
            result = {
                "subscription_id": sub["id"],
                "secret": None,
                "created": False,
                "message": "Webhook subscription already exists for this URL",
            }
            print(json.dumps(result))
            return

    desc = description or f"SRE agent webhook for service {service_id}"
    body = {
        "webhook_subscription": {
            "type": "webhook_subscription",
            "delivery_method": {
                "type": "http_delivery_method",
                "url": url,
            },
            "events": [
                "incident.triggered",
                "incident.escalated",
            ],
            "filter": {
                "type": "service_reference",
                "id": service_id,
            },
            "description": desc,
        }
    }
    resp = _request("POST", "/webhook_subscriptions", body)
    sub = resp["webhook_subscription"]
    secret = sub.get("delivery_method", {}).get("secret")
    result = {
        "subscription_id": sub["id"],
        "secret": secret,
        "created": True,
    }
    print(json.dumps(result))


def _list_webhooks_for_service(service_id):
    """List all webhook subscriptions filtered to a specific service."""
    resp = _request("GET", f"/webhook_subscriptions?filter[type]=service_reference&filter[id]={service_id}")
    return resp.get("webhook_subscriptions", [])


def list_webhooks(service_id):
    """List webhook subscriptions for a service and print as JSON."""
    subs = _list_webhooks_for_service(service_id)
    result = []
    for sub in subs:
        result.append({
            "subscription_id": sub["id"],
            "url": sub.get("delivery_method", {}).get("url"),
            "description": sub.get("description"),
            "events": [e["type"] for e in sub.get("events", [])],
        })
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description="PagerDuty setup helper for deploy.sh")
    subparsers = parser.add_subparsers(dest="command", required=True)

    svc_parser = subparsers.add_parser("find-or-create-service", help="Find or create a PagerDuty service")
    svc_parser.add_argument("--name", required=True, help="Service name")
    svc_parser.add_argument("--escalation-policy-id", default="", help="Escalation policy ID (required for creation)")

    wh_parser = subparsers.add_parser("create-webhook", help="Create a webhook subscription")
    wh_parser.add_argument("--service-id", required=True, help="PagerDuty service ID")
    wh_parser.add_argument("--url", required=True, help="Webhook delivery URL")
    wh_parser.add_argument("--description", default="", help="Webhook description")

    list_parser = subparsers.add_parser("list-webhooks", help="List webhook subscriptions for a service")
    list_parser.add_argument("--service-id", required=True, help="PagerDuty service ID")

    args = parser.parse_args()

    if args.command == "find-or-create-service":
        find_or_create_service(args.name, args.escalation_policy_id)
    elif args.command == "create-webhook":
        create_webhook(args.service_id, args.url, args.description or None)
    elif args.command == "list-webhooks":
        list_webhooks(args.service_id)


if __name__ == "__main__":
    main()
