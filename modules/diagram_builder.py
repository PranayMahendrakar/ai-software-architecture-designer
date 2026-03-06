"""
diagram_builder.py
Generates Mermaid syntax diagrams for:
  1. System Architecture
  2. Microservice Layout
  3. Database Schema (ER diagram)
  4. Deployment Strategy
"""

from modules.architecture_planner import ArchitecturePlan
from modules.component_generator import GeneratedComponents


def build_system_architecture_diagram(plan: ArchitecturePlan) -> str:
    """Generate Mermaid flowchart for the overall system architecture."""
    lines = [
        "graph TB",
        "    subgraph Client[\"Client Layer\"]",
        "        Browser[\"🌐 Web Browser\"]",
        "        Mobile[\"📱 Mobile App\"]",
        "    end",
        "",
        "    subgraph Edge[\"Edge Layer\"]",
        "        CDN[\"☁️ CDN / CloudFront\"]",
        "        LB[\"⚖️ Load Balancer\"]",
        "        GW[\"🔀 API Gateway\"]",
        "    end",
        "",
        "    subgraph Services[\"Microservices\"]",
    ]

    for svc in plan.services:
        if svc["name"] not in ("api-gateway", "frontend"):
            safe = svc["name"].replace("-", "_").upper()
            lines.append(f'        {safe}[\"⚙️ {svc["name"]}\"]')

    lines += [
        "    end",
        "",
        "    subgraph Data[\"Data Layer\"]",
    ]

    for db in plan.databases:
        safe = db["name"].replace("-", "_").upper()
        icon = "🗄️" if "postgres" in db["name"] else ("⚡" if "redis" in db["name"] else "📦")
        lines.append(f'        {safe}[\""{icon} {db["name"]} ({db["type"]})\"]')

    if plan.message_broker != "none":
        lines.append(f'        BROKER[\"📨 {plan.message_broker.capitalize()} Message Broker\"]')

    lines += [
        "    end",
        "",
        "    Browser --> CDN",
        "    Mobile --> CDN",
        "    CDN --> LB",
        "    LB --> GW",
    ]

    for svc in plan.services:
        if svc["name"] not in ("api-gateway", "frontend"):
            safe = svc["name"].replace("-", "_").upper()
            lines.append(f"    GW --> {safe}")

    for svc in plan.services:
        if svc["name"] not in ("api-gateway", "frontend"):
            safe = svc["name"].replace("-", "_").upper()
            for db in plan.databases[:2]:
                db_safe = db["name"].replace("-", "_").upper()
                lines.append(f"    {safe} --> {db_safe}")

    if plan.message_broker != "none":
        lines.append("    CORE_SERVICE --> BROKER")
        lines.append("    BROKER --> NOTIFICATION_SERVICE")

    lines += [
        "",
        "    style Client fill:#1a1a2e,stroke:#e94560",
        "    style Edge fill:#16213e,stroke:#0f3460",
        "    style Services fill:#0f3460,stroke:#533483",
        "    style Data fill:#533483,stroke:#e94560",
    ]

    return "\n".join(lines)


def build_microservice_diagram(plan: ArchitecturePlan) -> str:
    """Generate Mermaid diagram for microservice interaction layout."""
    lines = [
        "graph LR",
        "    subgraph External[External Clients]",
        "        WEB[Web App]",
        "        MOB[Mobile App]",
        "    end",
        "",
        "    GW[API Gateway :8000]",
        "",
        "    subgraph Core Services",
    ]

    for svc in plan.services:
        if svc["name"] not in ("api-gateway", "frontend"):
            safe = svc["name"].replace("-", "_").upper()
            lines.append(f'        {safe}["{svc["name"]} :{svc["port"]}\n{svc["tech"]}"]')

    lines += [
        "    end",
        "",
        "    subgraph Storage",
    ]

    for db in plan.databases:
        safe = db["name"].replace("-", "_").upper()
        lines.append(f'        {safe}["{db["name"]}\n{db["type"]}"]')

    lines += ["    end", ""]

    lines.append("    WEB -->|HTTPS| GW")
    lines.append("    MOB -->|HTTPS| GW")

    for svc in plan.services:
        if svc["name"] not in ("api-gateway", "frontend"):
            safe = svc["name"].replace("-", "_").upper()
            lines.append(f"    GW -->|REST/gRPC| {safe}")

    for svc in plan.services:
        if "user" in svc["name"] or "core" in svc["name"] or "payment" in svc["name"]:
            safe = svc["name"].replace("-", "_").upper()
            for db in plan.databases:
                db_safe = db["name"].replace("-", "_").upper()
                lines.append(f"    {safe} --- {db_safe}")

    if plan.message_broker != "none":
        lines.append(f'\n    BROKER["{plan.message_broker.upper()}\nMessage Broker"]')
        lines.append("    CORE_SERVICE -->|publish| BROKER")
        lines.append("    BROKER -->|subscribe| NOTIFICATION_SERVICE")

    return "\n".join(lines)


def build_database_schema_diagram(components: GeneratedComponents) -> str:
    """Generate Mermaid ER diagram for the database schema."""
    lines = ["erDiagram"]

    for table in components.db_schema.tables:
        lines.append(f"    {table.name.upper()} {{")
        for col in table.columns:
            pk_flag = " PK" if col.primary_key else ""
            fk_flag = " FK" if col.foreign_key else ""
            lines.append(f'        {col.type} {col.name}{pk_flag}{fk_flag}')
        lines.append("    }")
        lines.append("")

    for rel in components.db_schema.relationships:
        parts = rel["from"].split(".")
        to_parts = rel["to"].split(".")
        if rel["type"] == "many-to-one":
            lines.append(f"    {parts[0].upper()} }}o--||  {to_parts[0].upper()} : \"belongs to\"")
        elif rel["type"] == "one-to-many":
            lines.append(f"    {parts[0].upper()} ||--o{{ {to_parts[0].upper()} : \"has many\"")

    return "\n".join(lines)


def build_deployment_diagram(plan: ArchitecturePlan) -> str:
    """Generate Mermaid deployment strategy diagram."""
    if plan.deployment_target == "kubernetes":
        return """graph TB
    subgraph Cloud[Cloud Provider - AWS / GCP / Azure]
        subgraph VPC[Virtual Private Cloud]
            subgraph PublicSubnet[Public Subnet]
                IGW[Internet Gateway]
                ALB[Application Load Balancer]
            end

            subgraph K8S[Kubernetes Cluster]
                subgraph ControlPlane[Control Plane]
                    API[API Server]
                    SCHED[Scheduler]
                    ETCD[etcd]
                end

                subgraph NodeGroup1[Node Group - App]
                    POD1[api-gateway Pod x2]
                    POD2[user-service Pod x3]
                    POD3[core-service Pod x3]
                end

                subgraph NodeGroup2[Node Group - Workers]
                    POD4[payment-service Pod x2]
                    POD5[notification-service Pod x2]
                    POD6[websocket-service Pod x2]
                end

                subgraph Ingress[Ingress / Service Mesh]
                    ING[Nginx Ingress]
                    ISTIO[Istio Sidecar]
                end
            end

            subgraph DataSubnet[Private Data Subnet]
                RDS[RDS PostgreSQL Multi-AZ]
                REDIS[ElastiCache Redis Cluster]
                MSK[MSK - Managed Kafka]
            end
        end

        S3[S3 Object Storage]
        CF[CloudFront CDN]
        CW[CloudWatch Monitoring]
        SM[Secrets Manager]
    end

    Internet((Internet)) --> CF
    CF --> ALB
    ALB --> ING
    ING --> POD1
    POD1 --> POD2
    POD1 --> POD3
    POD3 --> RDS
    POD3 --> REDIS
    POD3 --> MSK
    POD2 --> RDS
    MSK --> POD5

    style Cloud fill:#232f3e,stroke:#ff9900
    style K8S fill:#326ce5,stroke:#fff,color:#fff
    style DataSubnet fill:#1a1a2e,stroke:#e94560"""

    else:
        return """graph TB
    subgraph DockerCompose[Docker Compose Stack]
        subgraph App[Application Services]
            GW[api-gateway :8000]
            US[user-service :8001]
            CS[core-service :8002]
            FE[frontend :3000]
        end

        subgraph Data[Data Services]
            PG[PostgreSQL :5432]
            RD[Redis :6379]
        end

        subgraph Monitoring[Observability]
            PROM[Prometheus :9090]
            GRAF[Grafana :3001]
        end
    end

    Browser[Browser] --> FE
    FE --> GW
    GW --> US
    GW --> CS
    US --> PG
    US --> RD
    CS --> PG
    CS --> RD
    PROM --> GW
    PROM --> US
    PROM --> CS
    GRAF --> PROM

    style App fill:#0f3460,stroke:#533483
    style Data fill:#533483,stroke:#e94560
    style Monitoring fill:#1a1a2e,stroke:#ff9900"""


def build_all_diagrams(plan: ArchitecturePlan, components: GeneratedComponents) -> dict:
    """Build all four Mermaid diagrams and return as a dictionary."""
    return {
        "system_architecture": build_system_architecture_diagram(plan),
        "microservice_layout": build_microservice_diagram(plan),
        "database_schema": build_database_schema_diagram(components),
        "deployment_strategy": build_deployment_diagram(plan),
    }


if __name__ == "__main__":
    from modules.requirement_parser import parse_requirements
    from modules.architecture_planner import plan_architecture
    from modules.component_generator import generate_components

    sample = (
        "Build an e-commerce platform where users can browse products, "
        "add them to a cart, and complete payments via Stripe. "
        "It should support real-time order tracking and send email notifications. "
        "The system must scale to handle thousands of concurrent users."
    )
    req = parse_requirements(sample)
    plan = plan_architecture(req)
    components = generate_components(plan)
    diagrams = build_all_diagrams(plan, components)

    for name, diagram in diagrams.items():
        print(f"\n{'='*60}")
        print(f"DIAGRAM: {name}")
        print('='*60)
        print(diagram)
