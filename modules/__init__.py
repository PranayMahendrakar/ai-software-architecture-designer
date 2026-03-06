"""
modules/__init__.py
AI Software Architecture Designer - Module Package

Exposes the four core pipeline modules:
  - requirement_parser   : NLP-based requirements extraction
  - architecture_planner : Architecture pattern selection
  - component_generator  : Detailed component & DB schema generation
  - diagram_builder      : Mermaid diagram generation
"""

from modules.requirement_parser import parse_requirements, ParsedRequirement
from modules.architecture_planner import plan_architecture, ArchitecturePlan
from modules.component_generator import generate_components, GeneratedComponents
from modules.diagram_builder import build_all_diagrams

__version__ = "1.0.0"
__author__ = "PranayMahendrakar"

__all__ = [
    "parse_requirements",
    "ParsedRequirement",
    "plan_architecture",
    "ArchitecturePlan",
    "generate_components",
    "GeneratedComponents",
    "build_all_diagrams",
]


def design_from_description(description: str) -> dict:
    """
    One-shot pipeline: natural language description -> full architecture.
    Returns a dict with requirements, architecture plan, and all 4 Mermaid diagrams.
    """
    req = parse_requirements(description)
    plan = plan_architecture(req)
    components = generate_components(plan)
    diagrams = build_all_diagrams(plan, components)
    return {
        "requirements": req,
        "plan": plan,
        "components": components,
        "diagrams": diagrams,
    }
