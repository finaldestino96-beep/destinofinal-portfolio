#!/usr/bin/env python3
"""Bounty Agent: collect and rank legitimate public earning opportunities."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Opportunity:
    title: str
    url: str
    platform: str
    reward_usd: float = 0
    currency: str = "unknown"
    difficulty: int = 3
    kyc: str = "unknown"
    status: str = "review_required"
    score: float = 0


NETWORK_ALIASES = {
    "solana": "solana",
    "sol": "solana",
    "ethereum": "ethereum_evm",
    "erc20": "ethereum_evm",
    "evm": "ethereum_evm",
    "bitcoin": "bitcoin",
    "btc": "bitcoin",
}


def payout_route(config: dict, network: str) -> dict:
    """Return a public payout route without handling signing material."""
    canonical = NETWORK_ALIASES.get(network.strip().lower())
    wallets = config.get("identity", {}).get("wallets", {})
    address = wallets.get(canonical, "") if canonical else ""
    if not canonical or not address or address == "CONFIGURE_LOCALLY":
        return {"accepted": False, "reason": "unsupported_or_unconfigured_network"}
    return {"accepted": True, "network": canonical, "address": address}


def score(item: Opportunity) -> float:
    reward_points = min(item.reward_usd / 10, 50)
    difficulty_penalty = max(1, item.difficulty) * 6
    kyc_penalty = {"no": 0, "unknown": 5, "yes": 10}.get(item.kyc, 5)
    return round(reward_points - difficulty_penalty - kyc_penalty, 2)


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "BountyAgent/0.1"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def collect(config: dict, demo: bool) -> list[Opportunity]:
    items: list[Opportunity] = []
    if demo:
        for raw in config.get("demo_opportunities", []):
            items.append(Opportunity(**raw))
        return items

    for source in config.get("sources", []):
        try:
            text = fetch_text(source["url"])
        except Exception as exc:
            print(f"Source unavailable: {source['name']}: {exc}")
            continue
        # Generic discovery only. Every result requires human verification.
        for match in re.finditer(r'href=["\'](https?://[^"\']+)["\'][^>]*>([^<]{5,120})<', text, re.I):
            title = re.sub(r"\s+", " ", match.group(2)).strip()
            if any(word in title.lower() for word in ("bounty", "reward", "challenge")):
                items.append(Opportunity(title, match.group(1), source["name"]))
    return items


def write_report(items: list[Opportunity], output: Path) -> None:
    for item in items:
        item.score = score(item)
    items.sort(key=lambda x: x.score, reverse=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "notice": "Discovery only. Verify terms and obtain human approval before claiming or submitting.",
        "opportunities": [asdict(item) for item in items],
    }
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--output", default="opportunities.json")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    config = load_config(Path(args.config))
    items = collect(config, args.demo)
    write_report(items, Path(args.output))
    print(f"Saved {len(items)} opportunities to {args.output}")


if __name__ == "__main__":
    main()
