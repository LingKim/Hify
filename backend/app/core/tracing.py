"""Tracing helpers for request-level correlation ids."""

from uuid import uuid4


def generate_trace_id() -> str:
    """Generate a request trace id."""
    return uuid4().hex
