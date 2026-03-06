"""
component_generator.py
Generates detailed component specifications and database schemas
from the architecture plan.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from modules.architecture_planner import ArchitecturePlan


@dataclass
class DBColumn:
    name: str
    type: str
    nullable: bool = False
    primary_key: bool = False
    foreign_key: str = ""
    unique: bool = False
    default: str = ""


@dataclass
class DBTable:
    name: str
    columns: List[DBColumn]
    indexes: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class DatabaseSchema:
    tables: List[DBTable]
    relationships: List[Dict]


@dataclass
class ServiceComponent:
    name: str
    language: str
    framework: str
    port: int
    endpoints: List[Dict]
    dependencies: List[str]
    env_vars: List[str]
    dockerfile: str


@dataclass
class GeneratedComponents:
    services: List[ServiceComponent]
    db_schema: DatabaseSchema
    docker_compose_snippet: str
    kubernetes_snippet: str


def generate_user_table() -> DBTable:
    return DBTable(
        name="users",
        description="Stores registered user accounts",
        columns=[
            DBColumn("id", "UUID", primary_key=True),
            DBColumn("email", "VARCHAR(255)", unique=True),
            DBColumn("password_hash", "VARCHAR(255)"),
            DBColumn("full_name", "VARCHAR(100)"),
            DBColumn("role", "VARCHAR(50)", default="'user'"),
            DBColumn("is_active", "BOOLEAN", default="true"),
            DBColumn("created_at", "TIMESTAMP", default="NOW()"),
            DBColumn("updated_at", "TIMESTAMP", default="NOW()"),
        ],
        indexes=["idx_users_email", "idx_users_role"]
    )


def generate_session_table() -> DBTable:
    return DBTable(
        name="sessions",
        description="Manages user authentication sessions",
        columns=[
            DBColumn("id", "UUID", primary_key=True),
            DBColumn("user_id", "UUID", foreign_key="users.id"),
            DBColumn("token_hash", "VARCHAR(512)", unique=True),
            DBColumn("expires_at", "TIMESTAMP"),
            DBColumn("ip_address", "INET"),
            DBColumn("created_at", "TIMESTAMP", default="NOW()"),
        ],
        indexes=["idx_sessions_user_id", "idx_sessions_token"]
    )


def generate_product_table() -> DBTable:
    return DBTable(
        name="products",
        description="Product catalog",
        columns=[
            DBColumn("id", "UUID", primary_key=True),
            DBColumn("name", "VARCHAR(255)"),
            DBColumn("description", "TEXT", nullable=True),
            DBColumn("price", "DECIMAL(10,2)"),
            DBColumn("stock_quantity", "INTEGER", default="0"),
            DBColumn("category_id", "UUID", foreign_key="categories.id", nullable=True),
            DBColumn("is_active", "BOOLEAN", default="true"),
            DBColumn("created_at", "TIMESTAMP", default="NOW()"),
        ],
        indexes=["idx_products_category", "idx_products_active"]
    )


def generate_order_table() -> DBTable:
    return DBTable(
        name="orders",
        description="Customer orders",
        columns=[
            DBColumn("id", "UUID", primary_key=True),
            DBColumn("user_id", "UUID", foreign_key="users.id"),
            DBColumn("status", "VARCHAR(50)", default="'pending'"),
            DBColumn("total_amount", "DECIMAL(10,2)"),
            DBColumn("payment_intent_id", "VARCHAR(255)", nullable=True),
            DBColumn("shipping_address", "JSONB", nullable=True),
            DBColumn("created_at", "TIMESTAMP", default="NOW()"),
            DBColumn("updated_at", "TIMESTAMP", default="NOW()"),
        ],
        indexes=["idx_orders_user_id", "idx_orders_status"]
    )


def generate_audit_log_table() -> DBTable:
    return DBTable(
        name="audit_logs",
        description="Tracks all significant system events",
        columns=[
            DBColumn("id", "BIGSERIAL", primary_key=True),
            DBColumn("entity_type", "VARCHAR(100)"),
            DBColumn("entity_id", "UUID"),
            DBColumn("action", "VARCHAR(50)"),
            DBColumn("actor_id", "UUID", foreign_key="users.id", nullable=True),
            DBColumn("metadata", "JSONB", nullable=True),
            DBColumn("created_at", "TIMESTAMP", default="NOW()"),
        ],
        indexes=["idx_audit_entity", "idx_audit_actor", "idx_audit_created"]
    )


def generate_database_schema(plan: ArchitecturePlan) -> DatabaseSchema:
    """Generate complete database schema from architecture plan."""
    tables = [
        generate_user_table(),
        generate_session_table(),
        generate_audit_log_table(),
    ]

    # Add product/order tables if e-commerce related
    if any("payment" in s["name"] or "core" in s["name"] for s in plan.services):
        tables += [generate_product_table(), generate_order_table()]

    relationships = [
        {"from": "sessions.user_id", "to": "users.id", "type": "many-to-one"},
        {"from": "orders.user_id", "to": "users.id", "type": "many-to-one"},
        {"from": "audit_logs.actor_id", "to": "users.id", "type": "many-to-one"},
    ]

    return DatabaseSchema(tables=tables, relationships=relationships)


def generate_service_component(service: Dict, plan: ArchitecturePlan) -> ServiceComponent:
    """Generate detailed component spec for a single microservice."""
    name = service["name"]
    port = service.get("port", 8000)
    tech = service.get("tech", "FastAPI")

    endpoints = []
    env_vars = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY", "LOG_LEVEL"]

    if "user" in name:
        endpoints = [
            {"method": "POST", "path": "/auth/register", "description": "Register new user"},
            {"method": "POST", "path": "/auth/login", "description": "Login and get JWT"},
            {"method": "POST", "path": "/auth/logout", "description": "Invalidate session"},
            {"method": "GET",  "path": "/users/me", "description": "Get current user profile"},
            {"method": "PATCH","path": "/users/me", "description": "Update user profile"},
        ]
        env_vars += ["JWT_SECRET", "JWT_EXPIRY"]

    elif "payment" in name:
        endpoints = [
            {"method": "POST", "path": "/payments/intent", "description": "Create payment intent"},
            {"method": "POST", "path": "/payments/confirm", "description": "Confirm payment"},
            {"method": "GET",  "path": "/payments/history", "description": "List payment history"},
            {"method": "POST", "path": "/webhooks/stripe", "description": "Stripe webhook handler"},
        ]
        env_vars += ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"]

    elif "notification" in name:
        endpoints = [
            {"method": "POST", "path": "/notify/email", "description": "Send email notification"},
            {"method": "POST", "path": "/notify/sms",   "description": "Send SMS notification"},
            {"method": "GET",  "path": "/notify/status/{id}", "description": "Check notification status"},
        ]
        env_vars += ["SENDGRID_API_KEY", "TWILIO_SID", "TWILIO_AUTH"]

    elif "core" in name:
        endpoints = [
            {"method": "GET",  "path": "/products",    "description": "List all products"},
            {"method": "GET",  "path": "/products/{id}","description": "Get product detail"},
            {"method": "POST", "path": "/orders",      "description": "Create new order"},
            {"method": "GET",  "path": "/orders/{id}", "description": "Get order status"},
            {"method": "PATCH","path": "/orders/{id}", "description": "Update order"},
        ]

    deps = ["postgres-db", "redis-cache"]
    if plan.message_broker != "none":
        deps.append(plan.message_broker)

    dockerfile = f"""FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]"""

    return ServiceComponent(
        name=name,
        language="Python",
        framework="FastAPI" if "react" not in tech.lower() else "React",
        port=port,
        endpoints=endpoints,
        dependencies=deps,
        env_vars=env_vars,
        dockerfile=dockerfile,
    )


def generate_components(plan: ArchitecturePlan) -> GeneratedComponents:
    """Generate all components from the architecture plan."""
    service_components = [generate_service_component(s, plan) for s in plan.services]
    db_schema = generate_database_schema(plan)

    # Docker Compose snippet
    compose = "version: '3.9'\nservices:\n"
    for svc in plan.services[:3]:
        compose += f"  {svc['name']}:\n    build: ./{svc['name']}\n    ports:\n      - \"{svc['port']}:{svc['port']}\"\n"

    # Kubernetes deployment snippet
    k8s = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: core-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: core-service
  template:
    metadata:
      labels:
        app: core-service
    spec:
      containers:
      - name: core-service
        image: core-service:latest
        ports:
        - containerPort: 8002
        envFrom:
        - secretRef:
            name: core-service-secrets"""

    return GeneratedComponents(
        services=service_components,
        db_schema=db_schema,
        docker_compose_snippet=compose,
        kubernetes_snippet=k8s,
    )
