#!/usr/bin/env python3
"""Execute a small allowlist of file-based gigs and produce audit evidence.

The worker deliberately does not execute shell commands or downloaded code. A job
must be approved by the owner and carry a verified-escrow reference before it can
run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JobBlocked(RuntimeError):
    """Raised when a job fails a safety or payment gate."""


JOB_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_path(root: Path, relative: str, *, must_exist: bool = False) -> Path:
    if not relative or Path(relative).is_absolute():
        raise JobBlocked("Paths must be non-empty and relative to the workspace")
    root = root.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise JobBlocked("Path escapes the configured workspace")
    if must_exist and not candidate.is_file():
        raise JobBlocked(f"Input file does not exist: {relative}")
    return candidate


def payment_gate(job: dict[str, Any], config: dict[str, Any]) -> None:
    rules = config.get("rules", {})
    minimum = float(rules.get("minimum_reward_usd", 5))
    reward = float(job.get("reward_usd", 0))
    if reward < minimum:
        raise JobBlocked(f"Reward ${reward:.2f} is below the ${minimum:.2f} minimum")
    if job.get("approved_by_owner") is not True:
        raise JobBlocked("Owner approval is required")

    payment = job.get("payment") or {}
    if rules.get("require_verified_escrow_before_execution", True):
        if payment.get("escrow_verified") is not True:
            raise JobBlocked("Verified escrow is required")
        if not str(payment.get("reference", "")).strip():
            raise JobBlocked("Escrow reference is required")
        if not str(payment.get("verified_by", "")).strip():
            raise JobBlocked("Escrow verifier identity is required")


def json_to_csv(source: Path, destination: Path) -> dict[str, Any]:
    data = load_json(source)
    if not isinstance(data, list) or not data:
        raise JobBlocked("json_to_csv input must be a non-empty JSON array")
    if not all(isinstance(row, dict) for row in data):
        raise JobBlocked("Every JSON array item must be an object")

    fields: list[str] = []
    for row in data:
        for key in row:
            if key not in fields:
                fields.append(key)

    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".job-", dir=destination.parent, text=True)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in data:
                normalized = {
                    key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                    for key, value in row.items()
                }
                writer.writerow(normalized)
        os.replace(temporary, destination)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return {"rows": len(data), "columns": fields}


TASKS = {"json_to_csv": json_to_csv}


def run_job(job_path: Path, config_path: Path, workspace: Path) -> dict[str, Any]:
    job = load_json(job_path)
    config = load_json(config_path)
    if not isinstance(job, dict):
        raise JobBlocked("Job specification must be a JSON object")

    job_id = str(job.get("job_id", ""))
    if not JOB_ID.fullmatch(job_id):
        raise JobBlocked("Invalid job_id")
    payment_gate(job, config)

    task_type = str(job.get("task_type", ""))
    handler = TASKS.get(task_type)
    if handler is None:
        raise JobBlocked(f"Unsupported task_type: {task_type}")

    source = safe_path(workspace, str(job.get("input_path", "")), must_exist=True)
    destination = safe_path(workspace, str(job.get("output_path", "")))
    if source == destination:
        raise JobBlocked("Input and output paths must differ")

    started_at = utc_now()
    input_hash = sha256_file(source)
    task_result = handler(source, destination)
    finished_at = utc_now()

    evidence_dir = safe_path(workspace, str(job.get("evidence_dir", "evidence")))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "job_id": job_id,
        "task_type": task_type,
        "status": "completed",
        "reward_usd": float(job.get("reward_usd", 0)),
        "payment_reference": job["payment"]["reference"],
        "started_at": started_at,
        "finished_at": finished_at,
        "input": {"path": str(source.relative_to(workspace.resolve())), "sha256": input_hash},
        "output": {
            "path": str(destination.relative_to(workspace.resolve())),
            "sha256": sha256_file(destination),
            **task_result,
        },
    }
    manifest_path = evidence_dir / f"{job_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    note_path = evidence_dir / f"{job_id}-delivery.md"
    note_path.write_text(
        "\n".join(
            [
                f"# Delivery: {job_id}",
                "",
                f"- Status: completed",
                f"- Task: `{task_type}`",
                f"- Deliverable: `{manifest['output']['path']}`",
                f"- SHA-256: `{manifest['output']['sha256']}`",
                f"- Escrow reference: `{manifest['payment_reference']}`",
                f"- Completed: {finished_at}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest["evidence_manifest"] = str(manifest_path.relative_to(workspace.resolve()))
    manifest["delivery_note"] = str(note_path.relative_to(workspace.resolve()))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path, help="Path to an approved job JSON file")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = run_job(args.job, args.config, args.workspace)
    except (JobBlocked, json.JSONDecodeError, OSError, ValueError) as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
