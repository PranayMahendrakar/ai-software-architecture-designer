"""
requirement_parser.py
Parses natural language project descriptions and extracts structured requirements.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ParsedRequirement:
    project_name: str
    description: str
    features: List[str]
    entities: List[str]
    integrations: List[str]
    scale: str  # small | medium | large
    tech_hints: List[str]
    auth_required: bool
    realtime_required: bool
    storage_types: List[str]


SCALE_KEYWORDS = {
    "large": ["enterprise", "million", "billion", "global", "scale", "distributed"],
    "medium": ["startup", "team", "hundred", "thousand", "moderate"],
    "small": ["simple", "basic", "small", "personal", "prototype", "mvp"],
}

STORAGE_KEYWORDS = {
    "relational": ["sql", "relational", "table", "mysql", "postgres"],
    "document": ["mongo", "document", "nosql", "json", "flexible"],
    "cache": ["redis", "cache", "session", "fast", "memory"],
    "search": ["elasticsearch", "search", "full-text", "index"],
    "object": ["s3", "blob", "file", "image", "video", "storage"],
}

TECH_HINTS_KEYWORDS = [
    "python", "node", "react", "vue", "django", "fastapi",
    "kafka", "rabbitmq", "grpc", "graphql", "rest", "websocket"
]

AUTH_KEYWORDS = ["auth", "login", "user", "oauth", "jwt", "password", "signup", "register"]
REALTIME_KEYWORDS = ["real-time", "realtime", "websocket", "live", "streaming", "push", "notification"]


def parse_requirements(description: str) -> ParsedRequirement:
    """Parse a natural language project description into structured requirements."""
    text = description.lower()
    words = re.findall(r'\b\w+\b', text)

    name_match = re.search(
        r'(?:build|create|design|develop)?\s*(?:an?\s+)?([A-Za-z][A-Za-z\s]+?)'
        r'(?:\s+that|\s+which|\s+system|\s+platform|\s+app|\s+application|$)',
        description, re.IGNORECASE
    )
    project_name = name_match.group(1).strip() if name_match else "Software System"

    scale = "medium"
    for level, keywords in SCALE_KEYWORDS.items():
        if any(k in text for k in keywords):
            scale = level
            break

    features = []
    feature_patterns = [
        r'(?:support|handle|provide|enable|allow|include)\s+([^.,;]+)',
        r'(?:users? (?:can|should|must|will))\s+([^.,;]+)',
    ]
    for pattern in feature_patterns:
        for match in re.finditer(pattern, text):
            feat = match.group(1).strip()
            if len(feat.split()) <= 8:
                features.append(feat.capitalize())

    if not features:
        features = ["User management", "Core business logic", "API endpoints", "Data persistence"]

    entities = list(set(re.findall(r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b', description)))
    if not entities:
        entities = ["User", "Product", "Order", "Session"]

    integrations = []
    integration_patterns = [
        "payment", "stripe", "email", "sendgrid", "sms", "twilio",
        "maps", "google", "aws", "azure", "slack", "webhook"
    ]
    for pattern in integration_patterns:
        if pattern in text:
            integrations.append(pattern.capitalize())

    storage_types = []
    for stype, keywords in STORAGE_KEYWORDS.items():
        if any(k in text for k in keywords):
            storage_types.append(stype)
    if not storage_types:
        storage_types = ["relational", "cache"]

    tech_hints = [t for t in TECH_HINTS_KEYWORDS if t in words]
    auth_required = any(k in text for k in AUTH_KEYWORDS)
    realtime_required = any(k in text for k in REALTIME_KEYWORDS)

    return ParsedRequirement(
        project_name=project_name,
        description=description,
        features=features[:6],
        entities=entities[:8],
        integrations=integrations,
        scale=scale,
        tech_hints=tech_hints,
        auth_required=auth_required,
        realtime_required=realtime_required,
        storage_types=storage_types,
    )


if __name__ == "__main__":
    sample = (
        "Build an e-commerce platform where users can browse products, "
        "add them to a cart, and complete payments via Stripe. "
        "It should support real-time order tracking and send email notifications. "
        "The system must scale to handle thousands of concurrent users."
    )
    result = parse_requirements(sample)
    print(result)
