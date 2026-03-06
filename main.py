"""
main.py
AI Software Architecture Designer
Entry point: converts a natural language project description into
a full software architecture with Mermaid diagrams.

Usage:
    python main.py --description "Build an e-commerce platform..."
    python main.py --interactive
    python main.py --example ecommerce|chat|iot|saas
"""

import argparse
import json
import os
import sys
from pathlib import Path

from modules.requirement_parser import parse_requirements
from modules.architecture_planner import plan_architecture
from modules.component_generator import generate_components
from modules.diagram_builder import build_all_diagrams

EXAMPLES = {
    "ecommerce": (
        "Build an e-commerce platform where users can browse products, "
        "add them to a cart, and complete payments via Stripe. "
        "Support real-time order tracking, email notifications, and product search. "
        "The system must scale to handle thousands of concurrent users."
    ),
    "chat": (
        "Create a real-time chat application where users can join rooms, "
        "send messages, and share files. Support OAuth login with Google. "
        "Messages should persist and be searchable. Scale for thousands of users."
    ),
    "iot": (
        "Design an IoT platform that ingests sensor data from thousands of devices, "
        "stores time-series metrics, triggers alerts, and provides a dashboard. "
        "The system must handle distributed, large-scale streaming data."
    ),
    "saas": (
        "Build a SaaS project management tool with teams, tasks, milestones, "
        "and Slack integrations. Support SSO login, role-based access, "
        "webhooks, and an API. The system targets enterprise scale."
    ),
}


def design_architecture(description: str) -> dict:
    """Full pipeline: description -> architecture + diagrams."""
    print("\n🔍 Parsing requirements...")
    req = parse_requirements(description)
    print(f"   Project: {req.project_name}")
    print(f"   Scale:   {req.scale}")
    print(f"   Features: {', '.join(req.features[:3])}...")

    print("\n🏗️  Planning architecture...")
    plan = plan_architecture(req)
    print(f"   Pattern:    {plan.pattern}")
    print(f"   Services:   {len(plan.services)}")
    print(f"   Databases:  {len(plan.databases)}")
    print(f"   Deployment: {plan.deployment_target}")

    print("\n⚙️  Generating components...")
    components = generate_components(plan)
    print(f"   DB Tables:  {len(components.db_schema.tables)}")
    print(f"   Services:   {len(components.services)}")

    print("\n📊 Building Mermaid diagrams...")
    diagrams = build_all_diagrams(plan, components)
    print(f"   Generated:  {', '.join(diagrams.keys())}")

    return {
        "project_name": req.project_name,
        "description": description,
        "requirements": {
            "scale": req.scale,
            "features": req.features,
            "entities": req.entities,
            "integrations": req.integrations,
            "auth_required": req.auth_required,
            "realtime_required": req.realtime_required,
            "storage_types": req.storage_types,
        },
        "architecture": {
            "pattern": plan.pattern,
            "services": plan.services,
            "databases": plan.databases,
            "message_broker": plan.message_broker,
            "deployment": plan.deployment_target,
            "monitoring": plan.monitoring,
        },
        "diagrams": diagrams,
        "components": {
            "service_count": len(components.services),
            "db_tables": [t.name for t in components.db_schema.tables],
            "docker_compose_snippet": components.docker_compose_snippet,
            "kubernetes_snippet": components.kubernetes_snippet,
        }
    }


def save_output(result: dict, output_dir: str = "output"):
    """Save architecture output to files."""
    Path(output_dir).mkdir(exist_ok=True)
    project_slug = result["project_name"].lower().replace(" ", "-")

    # Save JSON report
    json_path = Path(output_dir) / f"{project_slug}-architecture.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 JSON report saved:  {json_path}")

    # Save individual Mermaid diagram files
    diagrams_dir = Path(output_dir) / "diagrams"
    diagrams_dir.mkdir(exist_ok=True)
    for name, diagram in result["diagrams"].items():
        mmd_path = diagrams_dir / f"{project_slug}-{name.replace('_', '-')}.mmd"
        with open(mmd_path, "w") as f:
            f.write(diagram)
        print(f"   📐 Diagram saved:    {mmd_path}")

    # Save Markdown summary
    md_path = Path(output_dir) / f"{project_slug}-summary.md"
    with open(md_path, "w") as f:
        f.write(f"# {result['project_name']} - Architecture Summary\n\n")
        f.write(f"> {result['description']}\n\n")
        f.write(f"## Pattern\n**{result['architecture']['pattern']}**\n\n")
        f.write(f"## Services ({len(result['architecture']['services'])})\n")
        for svc in result['architecture']['services']:
            f.write(f"- **{svc['name']}** :{svc['port']} — {svc['responsibility']}\n")
        f.write(f"\n## Databases\n")
        for db in result['architecture']['databases']:
            f.write(f"- **{db['name']}** ({db['type']}) — Used by: {db['used_by']}\n")
        f.write(f"\n## Diagrams\n")
        for name, diagram in result["diagrams"].items():
            f.write(f"\n### {name.replace('_', ' ').title()}\n")
            f.write(f"```mermaid\n{diagram}\n```\n")
    print(f"   📝 Markdown summary: {md_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Software Architecture Designer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --example ecommerce
  python main.py --description "Build a ride-sharing app like Uber"
  python main.py --interactive
        """
    )
    parser.add_argument("--description", "-d", type=str, help="Natural language project description")
    parser.add_argument("--example", "-e", choices=list(EXAMPLES.keys()), help="Use a built-in example")
    parser.add_argument("--interactive", "-i", action="store_true", help="Enter description interactively")
    parser.add_argument("--output", "-o", default="output", help="Output directory (default: output)")
    parser.add_argument("--json-only", action="store_true", help="Only output JSON to stdout")

    args = parser.parse_args()

    if args.example:
        description = EXAMPLES[args.example]
        print(f"\n📌 Using example: {args.example}")
    elif args.description:
        description = args.description
    elif args.interactive:
        print("\n🤖 AI Software Architecture Designer")
        print("=" * 50)
        description = input("Describe your project: ").strip()
        if not description:
            print("Error: Description cannot be empty.")
            sys.exit(1)
    else:
        # Default to ecommerce example
        print("\nNo description provided. Using ecommerce example.\nUse --help for options.\n")
        description = EXAMPLES["ecommerce"]

    result = design_architecture(description)

    if args.json_only:
        print(json.dumps(result, indent=2))
    else:
        save_output(result, args.output)
        print("\n✅ Architecture design complete!")
        print(f"   Open output/{result['project_name'].lower().replace(' ', '-')}-summary.md to view")


if __name__ == "__main__":
    main()
