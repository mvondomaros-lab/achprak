"""Time one local AChPrak user through the same jobs as the Hub load test."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import time

import httpx

from load_test_hub import job, settings


CASES = [
    ("trans-H", settings("trans")),
    ("trans-NMe2-NMe2", settings("trans", "NMe2", "NMe2")),
    ("trans-NMe2-CF3", settings("trans", "NMe2", "CF3")),
    ("cis-CF3-CF3", settings("cis", "CF3", "CF3")),
]


async def run_case(socket, label, molecule_settings, timeout):
    latencies = []
    output = {"case": label, "settings": molecule_settings, "jobs": []}
    transport = httpx.AsyncHTTPTransport(uds=socket)
    async with httpx.AsyncClient(transport=transport, timeout=120) as client:
        response = await client.get("http://localhost/api/session")
        response.raise_for_status()
        molecule_id = None
        start = time.monotonic()
        for kind in ("template", "minimum", "uvvis"):
            try:
                metrics, result = await job(
                    client,
                    "http://localhost",
                    kind,
                    molecule_id,
                    molecule_settings,
                    latencies,
                    timeout,
                )
                output["jobs"].append(metrics)
                if metrics["status"] != "complete":
                    break
                if kind != "uvvis":
                    molecule_id = result["molecule"]["id"]
                if kind == "minimum" and not metrics["converged"]:
                    break
            except Exception as exc:
                output["error"] = f"{type(exc).__name__}: {exc}"
                break
        output["workflow_s"] = round(time.monotonic() - start, 3)
        output["http_requests"] = len(latencies) + 1
    return output


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    result = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "client_platform": platform.platform(),
        "transport": "local Unix socket, no Hub or network proxy",
        "cases": [],
    }
    for label, molecule_settings in CASES:
        case = await run_case(args.socket, label, molecule_settings, args.timeout)
        result["cases"].append(case)
        print(label, case["workflow_s"], case.get("error"), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("results:", args.output)


if __name__ == "__main__":
    asyncio.run(main())
