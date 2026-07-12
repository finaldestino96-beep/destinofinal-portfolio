#!/usr/bin/env python3
"""Small HTTP service that drafts truthful gig proposals with Claude.

No framework or third-party runtime dependency is required. Secrets are read
only from environment variables and are never returned by the API.
"""

from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-4-5"
MAX_BODY_BYTES = 64 * 1024


class ServiceError(RuntimeError):
    pass


def require_text(value: Any, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ServiceError(f"{name} must be a non-empty string")
    value = value.strip()
    if len(value) > maximum:
        raise ServiceError(f"{name} exceeds {maximum} characters")
    return value


def normalize_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ServiceError("Request body must be a JSON object")
    skills = payload.get("skills", [])
    if not isinstance(skills, list) or len(skills) > 20:
        raise ServiceError("skills must be a list with at most 20 items")
    normalized_skills = [require_text(item, "skill", 80) for item in skills]
    return {
        "title": require_text(payload.get("title"), "title", 200),
        "description": require_text(payload.get("description"), "description", 12_000),
        "platform": require_text(payload.get("platform", "unspecified"), "platform", 100),
        "budget": require_text(payload.get("budget", "not stated"), "budget", 100),
        "language": require_text(payload.get("language", "Spanish"), "language", 40),
        "skills": normalized_skills,
    }


def proposal_prompt(job: dict[str, Any]) -> str:
    skills = ", ".join(job["skills"]) if job["skills"] else "No verified skills supplied"
    return (
        "Draft a concise freelance proposal using only the facts below. "
        "Do not invent experience, credentials, results, identities, availability, "
        "or portfolio links. Do not claim the contract is accepted. Mention a clear "
        "delivery approach and one useful clarification question. Return only the "
        f"proposal in {job['language']}, between 120 and 220 words.\n\n"
        f"Title: {job['title']}\n"
        f"Platform: {job['platform']}\n"
        f"Budget: {job['budget']}\n"
        f"Verified skills: {skills}\n"
        f"Job description:\n{job['description']}"
    )


def call_anthropic(job: dict[str, Any], *, opener=urllib.request.urlopen) -> dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ServiceError("ANTHROPIC_API_KEY is not configured")
    model = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    body = {
        "model": model,
        "max_tokens": 700,
        "messages": [{"role": "user", "content": proposal_prompt(job)}],
    }
    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "user-agent": "DestinoGigAgent/1.0",
        },
    )
    try:
        with opener(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ServiceError(f"Anthropic rejected the request ({exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ServiceError(f"Anthropic request failed: {exc}") from exc

    blocks = result.get("content", []) if isinstance(result, dict) else []
    proposal = "".join(
        block.get("text", "")
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text"
    ).strip()
    if not proposal:
        raise ServiceError("Anthropic returned no proposal text")
    return {
        "proposal": proposal,
        "model": result.get("model", model),
        "request_id": result.get("id"),
        "submitted": False,
        "notice": "Draft only. Review facts and platform terms before submitting.",
    }


def authorized(header: str | None) -> bool:
    expected = os.getenv("APP_API_KEY", "").strip()
    if not expected:
        return False
    prefix = "Bearer "
    supplied = header[len(prefix):].strip() if header and header.startswith(prefix) else ""
    return bool(supplied) and secrets.compare_digest(supplied, expected)


class Handler(BaseHTTPRequestHandler):
    server_version = "DestinoGigAgent/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        # Keep standard request metadata but never log request bodies or secrets.
        super().log_message(format, *args)

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY", "").strip()),
                    "access_key_configured": bool(os.getenv("APP_API_KEY", "").strip()),
                },
            )
            return
        self.send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/proposal":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        if not authorized(self.headers.get("authorization")):
            self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ServiceError("Invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = call_anthropic(normalize_request(payload))
        except (ServiceError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        self.send_json(HTTPStatus.OK, result)


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Destino Gig Agent listening on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
