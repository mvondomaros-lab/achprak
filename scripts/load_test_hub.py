"""Run the AChPrak student workflow through an authenticated JupyterHub.

Example (test accounts only):
    ACHPRAK_LOAD_PASSWORD_TEMPLATE='<password pattern with {n}>' \
        pixi run -e dev python \
        scripts/load_test_hub.py --origin https://hub.example.edu \
        --hub-prefix /jhub --output results/hub-load/run.json

The password template is read from the environment and never written to results.
"""

import argparse
import asyncio
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import platform
import time

import httpx


class LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.xsrf = None
        self.action = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "form" and self.action is None:
            self.action = attributes.get("action")
        if tag == "input" and attributes.get("name") == "_xsrf":
            self.xsrf = attributes.get("value")


def settings(configuration, first=None, second=None):
    substituents = ["H"] * 10
    if first:
        substituents[0] = first
    if second:
        substituents[5] = second
    return {"configuration": configuration, "substituents": substituents}


SCENARIOS = {
    "baseline": [settings("trans") for _ in range(12)],
    "double": (
        [settings("trans", "NMe2", "NMe2") for _ in range(4)]
        + [settings("trans", "NMe2", "CF3") for _ in range(4)]
        + [settings("cis", "CF3", "CF3") for _ in range(4)]
    ),
}


def percentile(values, percent):
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower), 3)


async def request(client, method, url, latencies, **kwargs):
    started = time.monotonic()
    response = await client.request(method, url, **kwargs)
    latencies.append(round(time.monotonic() - started, 3))
    return response


async def open_session(client, origin, prefix, username, password, latencies):
    start = time.monotonic()
    login_url = f"{origin}{prefix}/hub/login"
    response = await request(client, "GET", login_url, latencies)
    response.raise_for_status()
    form = LoginForm()
    form.feed(response.text)
    if not form.xsrf or not form.action:
        raise RuntimeError("Hub login form or XSRF field was not found")
    response = await request(
        client,
        "POST",
        origin + form.action,
        latencies,
        data={"_xsrf": form.xsrf, "username": username, "password": password},
    )
    if response.status_code != 200 or "Invalid username or password" in response.text:
        raise RuntimeError(f"Hub login failed: HTTP {response.status_code}")
    app_url = f"{origin}{prefix}/user/{username}"
    retries = 0
    while time.monotonic() - start < 120:
        response = await request(client, "GET", app_url + "/api/session", latencies)
        if response.status_code == 200 and response.headers.get(
            "content-type", ""
        ).startswith("application/json"):
            state = response.json()
            if state.get("user") != username:
                raise RuntimeError("The application returned the wrong Hub identity")
            return app_url, round(time.monotonic() - start, 3), retries
        if response.status_code not in {200, 404, 424, 502, 503}:
            raise RuntimeError(f"Application startup failed: HTTP {response.status_code}")
        retries += 1
        await asyncio.sleep(1)
    raise TimeoutError("Application did not become ready within 120 seconds")


async def job(client, app_url, kind, molecule_id, molecule_settings, latencies, timeout):
    payload = {"kind": kind}
    if kind == "template":
        payload["settings"] = molecule_settings
    else:
        payload["molecule_id"] = molecule_id
    start = time.monotonic()
    response = await request(
        client,
        "POST",
        app_url + "/api/jobs",
        latencies,
        headers={"X-AChPrak-Request": "1"},
        json=payload,
    )
    if response.status_code != 202:
        raise RuntimeError(f"{kind} submission failed: HTTP {response.status_code}")
    submitted = time.monotonic()
    job_id = response.json()["id"]
    first_running = None
    polls = 0
    while time.monotonic() - start < timeout + 30:
        response = await request(client, "GET", app_url + f"/api/jobs/{job_id}", latencies)
        response.raise_for_status()
        polls += 1
        state = response.json()
        if state["status"] == "running" and first_running is None:
            first_running = time.monotonic()
        if state["status"] not in {"running", "queued"}:
            end = time.monotonic()
            result = state.get("result") or {}
            molecule = result.get("molecule") or {}
            return {
                "kind": kind,
                "status": state["status"],
                "error": state.get("error"),
                "submit_s": round(submitted - start, 3),
                "queue_observed_s": (
                    round(first_running - submitted, 3) if first_running else None
                ),
                "total_s": round(end - start, 3),
                "server_elapsed_s": state.get("elapsed"),
                "polls": polls,
                "converged": molecule.get("converged") if kind == "minimum" else None,
                "atom_count": molecule.get("atom_count") if molecule else None,
            }, result
        await asyncio.sleep(1)
    raise TimeoutError(f"{kind} did not finish within {timeout + 30} seconds")


async def student(origin, prefix, username, password, molecule_settings, gate, timeout):
    latencies = []
    output = {"user": username, "settings": molecule_settings, "jobs": []}
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        try:
            app_url, output["login_spawn_s"], output["startup_retries"] = await open_session(
                client, origin, prefix, username, password, latencies
            )
            output["ready"] = True
        except Exception as exc:
            output["ready"] = False
            output["error"] = f"{type(exc).__name__}: {exc}"
            gate["ready"].set()
            output["http_latencies_s"] = latencies
            return output
        gate["ready"].set()
        await gate["start"].wait()
        molecule_id = None
        for kind in ("template", "minimum", "uvvis"):
            try:
                metrics, result = await job(
                    client, app_url, kind, molecule_id, molecule_settings, latencies, timeout
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
    output["http_latencies_s"] = latencies
    return output


async def phase(origin, prefix, usernames, password_template, scenario, timeout):
    gates = [{"ready": asyncio.Event(), "start": asyncio.Event()} for _ in usernames]
    phase_start = time.monotonic()
    tasks = [
        asyncio.create_task(
            student(
                origin,
                prefix,
                username,
                password_template.format(n=index),
                SCENARIOS[scenario][index - 1],
                gate,
                timeout,
            )
        )
        for index, (username, gate) in enumerate(zip(usernames, gates), start=1)
    ]
    await asyncio.gather(*(gate["ready"].wait() for gate in gates))
    ready_at = time.monotonic()
    for gate in gates:
        gate["start"].set()
    students = await asyncio.gather(*tasks)
    end = time.monotonic()
    latencies = [v for s in students for v in s["http_latencies_s"]]
    for student_result in students:
        student_result.pop("http_latencies_s")
    return {
        "scenario": scenario,
        "users": len(usernames),
        "preparation_s": round(ready_at - phase_start, 3),
        "workload_s": round(end - ready_at, 3),
        "ready_users": sum(s["ready"] for s in students),
        "http_requests": len(latencies),
        "http_latency_p50_s": percentile(latencies, 50),
        "http_latency_p95_s": percentile(latencies, 95),
        "http_latency_max_s": round(max(latencies), 3) if latencies else None,
        "students": students,
    }


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True, help="HTTPS origin of the JupyterHub")
    parser.add_argument("--hub-prefix", default="/jhub")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario", choices=["baseline", "double"], required=True)
    parser.add_argument("--users", type=int, choices=[1, 12], default=12)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    password_template = os.environ.get("ACHPRAK_LOAD_PASSWORD_TEMPLATE")
    if not password_template or "{n}" not in password_template:
        parser.error("ACHPRAK_LOAD_PASSWORD_TEMPLATE must contain {n}")
    usernames = [f"test{n}" for n in range(1, args.users + 1)]
    result = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "origin": args.origin,
        "hub_prefix": args.hub_prefix,
        "client_platform": platform.platform(),
        "scenario_settings": SCENARIOS[args.scenario][: args.users],
        "measurement": "Client-side HTTP timings; no host CPU or memory sampling",
        "phase": await phase(
            args.origin.rstrip("/"),
            args.hub_prefix.rstrip("/"),
            usernames,
            password_template,
            args.scenario,
            args.timeout,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result["phase"].items() if k != "students"}, indent=2))
    print("results:", args.output)


if __name__ == "__main__":
    asyncio.run(main())
