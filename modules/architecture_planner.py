"""
architecture_planner.py
Plans the overall software architecture based on parsed requirements.
Determines which architectural patterns, services, and infrastructure to use.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from modules.requirement_parser import ParsedRequirement


@dataclass
class ArchitecturePlan:
    pattern: str                    # monolith | microservices | serverless | event-driven
    services: List[Dict]            # List of microservices with name, responsibility, port
    api_gateway: bool
    message_broker: str             # kafka | rabbitmq | none
    databases: List[Dict]           # name, type, used_by
    cache_layer: bool
    cdn: bool
    load_balancer: bool
    auth_service: bool
    notification_service: bool
    deployment_target: str          # kubernetes | docker-compose | serverless | vm
    monitoring: List[str]           # prometheus | grafana | elk | datadog


SCALE_TO_PATTERN = {
    "small": "monolith",
    "medium": "microservices",
    "large": "event-driven microservices",
}

SCALE_TO_DEPLOYMENT = {
    "small": "docker-compose",
    "medium": "kubernetes",
    "large": "kubernetes",
}


def plan_architecture(req: ParsedRequirement) -> ArchitecturePlan:
    """Generate an architecture plan from parsed requirements."""

    pattern = SCALE_TO_PATTERN.get(req.scale, "microservices")
    deployment = SCALE_TO_DEPLOYMENT.get(req.scale, "kubernetes")

    # Core services
    services = [
        {"name": "api-gateway", "responsibility": "Route requests, rate limiting, auth verification", "port": 8000, "tech": "Nginx / Kong"},
        {"name": "user-service", "responsibility": "User registration, login, profile management", "port": 8001, "tech": "FastAPI"},
        {"name": "core-service", "responsibility": "Main business logic for " + req.project_name, "port": 8002, "tech": "FastAPI"},
    ]

    if req.realtime_required:
        services.append({
            "name": "websocket-service",
            "responsibility": "Real-time event broadcasting and WebSocket management",
            "port": 8003, "tech": "FastAPI + WebSockets"
        })

    if "payment" in req.integrations or "stripe" in [i.lower() for i in req.integrations]:
        services.append({
            "name": "payment-service",
            "responsibility": "Payment processing, invoicing, and transaction management",
            "port": 8004, "tech": "FastAPI + Stripe SDK"
        })

    if "email" in req.integrations or "sendgrid" in [i.lower() for i in req.integrations]:
        services.append({
            "name": "notification-service",
            "responsibility": "Email, SMS, and push notification delivery",
            "port": 8005, "tech": "FastAPI + SendGrid"
        })

    services.append({
        "name": "frontend",
        "responsibility": "User interface and client-side rendering",
        "port": 3000, "tech": "React / Next.js"
    })

    # Databases
    databases = []
    for stype in req.storage_types:
        if stype == "relational":
            databases.append({"name": "postgres-db", "type": "PostgreSQL", "used_by": "user-service, core-service", "port": 5432})
        elif stype == "document":
            databases.append({"name": "mongo-db", "type": "MongoDB", "used_by": "core-service", "port": 27017})
        elif stype == "cache":
            databases.append({"name": "redis-cache", "type": "Redis", "used_by": "api-gateway, session management", "port": 6379})
        elif stype == "search":
            databases.append({"name": "elasticsearch", "type": "Elasticsearch", "used_by": "search-service", "port": 9200})
        elif stype == "object":
            databases.append({"name": "object-store", "type": "S3 / MinIO", "used_by": "file uploads", "port": 9000})

    if not databases:
        databases = [
            {"name": "postgres-db", "type": "PostgreSQL", "used_by": "core services", "port": 5432},
            {"name": "redis-cache", "type": "Redis", "used_by": "caching, sessions", "port": 6379},
        ]

    # Message broker for large/realtime systems
    broker = "none"
    if req.scale == "large" or req.realtime_required:
        broker = "kafka" if req.scale == "large" else "rabbitmq"

    # Monitoring stack
    monitoring = ["prometheus", "grafana"]
    if req.scale == "large":
        monitoring += ["elk-stack", "jaeger-tracing"]

    return ArchitecturePlan(
        pattern=pattern,
        services=services,
        api_gateway=True,
        message_broker=broker,
        databases=databases,
        cache_layer="cache" in req.storage_types,
        cdn=req.scale in ("medium", "large"),
        load_balancer=req.scale in ("medium", "large"),
        auth_service=req.auth_required,
        notification_service=bool(req.integrations),
        deployment_target=deployment,
        monitoring=monitoring,
    )


if __name__ == "__main__":
    from modules.requirement_parser import parse_requirements
    sample = (
        "Build an e-commerce platform where users can browse products, "
        "add them to a cart, and complete payments via Stripe. "
        "It should support real-time order tracking and send email notifications. "
        "The system must scale to handle thousands of concurrent users."
    )
    req = parse_requirements(sample)
    plan = plan_architecture(req)
    print(plan)
