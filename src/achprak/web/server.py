"""Local app server. Deploy one instance per Unix user behind an authenticated proxy."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .ts_policy import with_ts_policy

STATIC = Path(__file__).parent / "static"
SUBSTITUENTS = ["H", "Me", "OMe", "NMe2", "CF3", "CN", "NO2"]
ACTIVE = {"queued", "running"}


class Settings(BaseModel):
    configuration: Literal["trans", "cis"] = "trans"
    substituents: list[Literal["H", "Me", "OMe", "NMe2", "CF3", "CN", "NO2"]] = Field(
        default_factory=lambda: ["H"] * 10, min_length=10, max_length=10
    )


class JobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["template", "minimum", "ts", "uvvis"]
    settings: Settings = Field(default_factory=Settings)
    molecule_id: str | None = None


@dataclass
class Session:
    molecules: dict = field(default_factory=dict)
    jobs: dict = field(default_factory=dict)
    touched: float = field(default_factory=time.monotonic)


def matching_results(session, base_name, kind):
    if kind not in {"minimum", "ts"}:
        return []
    return [
        key
        for key, m in session.molecules.items()
        if m.get("base_name") == base_name
        and (
            m.get("kind") == kind
            or (
                m.get("kind") == "unconverged"
                and ("ts" if m.get("ts_search") else "minimum") == kind
            )
        )
    ]


class JobManager:
    def __init__(self, max_jobs=2, timeout=600, session_ttl=86400):
        self.sessions = {}
        self.max_jobs, self.timeout, self.session_ttl = max_jobs, timeout, session_ttl
        self.root = Path(tempfile.mkdtemp(prefix="achprak-web-"))
        self.tasks = {}

    def submit(self, session, payload):
        if any(j["status"] in ACTIVE for j in session.jobs.values()):
            raise HTTPException(409, "Eine Berechnung läuft bereits in dieser Sitzung.")
        replacing = matching_results(
            session, payload.get("molecule", {}).get("base_name"), payload["kind"]
        )
        if (
            not replacing
            and len(session.molecules) >= 100
            and payload["kind"]
            in {
                "template",
                "minimum",
                "ts",
            }
        ):
            raise HTTPException(
                409,
                "Die Sitzung enthält bereits 100 Strukturen. Löschen Sie nicht mehr benötigte Strukturen, bevor Sie weitere erstellen.",
            )
        while len(session.jobs) >= 12:
            old = next(iter(session.jobs))
            session.jobs.pop(old)
            shutil.rmtree(self.root / old, ignore_errors=True)
        job_id = secrets.token_hex(16)
        folder = self.root / job_id
        folder.mkdir(mode=0o700)
        (folder / "input.json").write_text(json.dumps(payload))
        job = {
            "id": job_id,
            "kind": payload["kind"],
            "status": "queued",
            "created": time.time(),
            "elapsed": 0,
            "error": None,
            "result": None,
        }
        session.jobs[job_id] = job
        self.tasks[job_id] = (session, job, folder, None)
        return job

    def stop(self, job_id, status="cancelled"):
        task = self.tasks.pop(job_id, None)
        if not task:
            return
        _, job, _, proc = task
        if proc is not None:
            # Workers own a process group, including any MOPAC child processes.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
        job["status"] = status
        if status == "timeout":
            job["error"] = (
                "Die Berechnung wurde nach Erreichen des Zeitlimits beendet. Wählen Sie eine Struktur mit weniger Substituenten oder besprechen Sie die Berechnung mit Ihrer Betreuung."
            )

    def tick(self):
        for job_id, (session, job, folder, proc) in list(self.tasks.items()):
            if proc is None:
                continue
            job["elapsed"] = round(time.monotonic() - job["started"], 1)
            if job["elapsed"] > self.timeout:
                self.stop(job_id, "timeout")
            elif proc.poll() is not None:
                self.tasks.pop(job_id)
                try:
                    envelope = json.loads((folder / "result.json").read_text())
                    if not envelope["ok"]:
                        raise ValueError(envelope["error"])
                    result = envelope["result"]
                    if "molecule" in result:
                        m = result["molecule"]
                        # Keep the previous result until a complete replacement
                        # arrives. Failed/cancelled jobs never remove it.
                        for old_id in matching_results(
                            session, m.get("base_name"), job["kind"]
                        ):
                            session.molecules.pop(old_id)
                        session.molecules[m["id"]] = m
                    else:
                        m = session.molecules.get(result["molecule_id"])
                        if m is not None:
                            m.update(
                                {k: v for k, v in result.items() if k != "molecule_id"}
                            )
                    job.update(status="complete", result=result)
                except Exception as exc:
                    job.update(
                        status="failed",
                        error=str(exc)
                        if (folder / "result.json").exists()
                        else f"Die Berechnung wurde unerwartet beendet (Fehlercode {proc.returncode}). Wenden Sie sich mit dieser Meldung an Ihre Betreuung.",
                    )
        running = sum(task[3] is not None for task in self.tasks.values())
        for job_id, (session, job, folder, proc) in list(self.tasks.items()):
            if proc is not None or running >= self.max_jobs:
                continue
            try:
                env = os.environ.copy()
                env.update(MPLBACKEND="Agg", PYTHONUNBUFFERED="1")
                for key in (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                ):
                    env[key] = "1"
                # Editable installs remain importable after changing the job directory.
                env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
                with (folder / "output.log").open("wb") as log:
                    proc = subprocess.Popen(
                        [sys.executable, "-m", "achprak.web.worker", str(folder)],
                        cwd=folder,
                        env=env,
                        stdout=log,
                        stderr=log,
                        start_new_session=True,
                    )
                job.update(status="running", started=time.monotonic())
                self.tasks[job_id] = (session, job, folder, proc)
                running += 1
            except OSError as exc:
                job.update(status="failed", error=str(exc))
                self.tasks.pop(job_id)
        for sid, session in list(self.sessions.items()):
            if time.monotonic() - session.touched > self.session_ttl:
                for job_id in session.jobs:
                    self.stop(job_id)
                    shutil.rmtree(self.root / job_id, ignore_errors=True)
                del self.sessions[sid]

    def close(self):
        for job_id in list(self.tasks):
            self.stop(job_id)
        shutil.rmtree(self.root, ignore_errors=True)


def create_app(max_jobs=2, timeout=600, cookie_path="/", secure_cookie=False):
    cookie_path = "/" + cookie_path.strip("/") + "/" if cookie_path.strip("/") else "/"
    manager = JobManager(max_jobs, timeout)
    cookie_name = "achprak_" + secrets.token_hex(5)

    @asynccontextmanager
    async def lifespan(app):
        async def monitor():
            while True:
                manager.tick()
                await asyncio.sleep(0.25)

        task = asyncio.create_task(monitor())
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            manager.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.manager = manager

    @app.middleware("http")
    async def browser_session(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            # A non-simple header prevents cross-origin forms/fetch from mutating sessions.
            # No CORS permission is granted by this app.
            if (
                request.method not in {"GET", "HEAD"}
                and request.headers.get("x-achprak-request") != "1"
            ):
                return JSONResponse({"detail": "Ungültige Anfrage."}, status_code=403)
            sid = request.cookies.get(cookie_name)
            fresh = sid not in manager.sessions
            if fresh:
                if request.url.path != "/api/session" or request.method != "GET":
                    return JSONResponse(
                        {
                            "detail": "Die Sitzung ist abgelaufen. Laden Sie die Seite neu, um eine neue Sitzung zu starten."
                        },
                        status_code=401,
                    )
                if len(manager.sessions) >= 100:
                    return JSONResponse(
                        {
                            "detail": "Die maximale Anzahl gleichzeitiger Sitzungen ist erreicht. Versuchen Sie es später erneut."
                        },
                        status_code=503,
                    )
                sid = secrets.token_urlsafe(32)
                manager.sessions[sid] = Session()
            request.state.session = manager.sessions[sid]
            request.state.session.touched = time.monotonic()
            response = await call_next(request)
            if fresh:
                response.set_cookie(
                    cookie_name,
                    sid,
                    httponly=True,
                    samesite="strict",
                    secure=secure_cookie,
                    path=cookie_path,
                )
            response.headers["Cache-Control"] = "no-store"
        else:
            response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; worker-src 'self' blob:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'self'"
        )
        return response

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/session")
    async def state(request: Request):
        s = request.state.session
        return {
            "molecules": [with_ts_policy(m) for m in s.molecules.values()],
            "jobs": list(s.jobs.values()),
            "user": os.environ.get("JUPYTERHUB_USER"),
            "timeout": timeout,
        }

    @app.post("/api/jobs", status_code=202)
    async def submit(body: JobRequest, request: Request):
        session = request.state.session
        payload = body.model_dump()
        if body.kind != "template":
            m = session.molecules.get(body.molecule_id)
            if m is None:
                raise HTTPException(404, "Struktur nicht gefunden.")
            m = with_ts_policy(m)
            if body.kind == "minimum" and m["kind"] == "minimum":
                raise HTTPException(
                    422,
                    "Diese Struktur ist bereits ein Minimum. Der vorhandene Verlauf bleibt erhalten.",
                )
            if body.kind == "ts" and (m["kind"] != "minimum" or not m.get("converged")):
                raise HTTPException(
                    422,
                    "Die Übergangszustandssuche benötigt ein optimiertes Minimum als Ausgangsstruktur. Führen Sie zuerst eine Minimumsuche durch.",
                )
            if body.kind == "ts" and m["ts_restriction"]:
                raise HTTPException(422, m["ts_restriction"])
            if body.kind == "uvvis" and m["kind"] != "minimum":
                raise HTTPException(
                    422,
                    "Die Spektrenrechnung benötigt ein optimiertes Minimum. Führen Sie zuerst eine Minimumsuche durch.",
                )
            if body.kind == "uvvis" and m.get("spectrum"):
                raise HTTPException(
                    422, "Für dieses Minimum wurde bereits ein Spektrum berechnet."
                )
            payload["molecule"] = m
        return manager.submit(session, payload)

    @app.get("/api/jobs/{job_id}")
    async def get_job(job_id: str, request: Request):
        job = request.state.session.jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "Berechnung nicht gefunden.")
        log = manager.root / job_id / "output.log"
        output = ""
        if log.exists():
            with log.open("rb") as handle:
                handle.seek(max(0, log.stat().st_size - 24000))
                output = handle.read().decode("utf-8", errors="replace")
        spectrum_progress = None
        progress_path = manager.root / job_id / "spectrum-progress.json"
        if job["kind"] == "uvvis" and progress_path.exists():
            spectrum_progress = json.loads(progress_path.read_text())
        return {**job, "log": output, "spectrum_progress": spectrum_progress}

    @app.delete("/api/jobs/{job_id}")
    async def cancel_job(job_id: str, request: Request):
        if job_id not in request.state.session.jobs:
            raise HTTPException(404, "Berechnung nicht gefunden.")
        manager.stop(job_id)
        return {"status": request.state.session.jobs[job_id]["status"]}

    @app.delete("/api/molecules")
    async def clear_molecules(request: Request):
        session = request.state.session
        if any(j["status"] in ACTIVE for j in session.jobs.values()):
            raise HTTPException(
                409,
                "Warten Sie auf den Abschluss der laufenden Berechnung oder brechen Sie diese ab.",
            )
        session.molecules.clear()
        return {"status": "deleted"}

    @app.delete("/api/molecules/{molecule_id}")
    async def delete_molecule(molecule_id: str, request: Request):
        session = request.state.session
        if any(j["status"] in ACTIVE for j in session.jobs.values()):
            raise HTTPException(
                409,
                "Warten Sie auf den Abschluss der laufenden Berechnung oder brechen Sie diese ab.",
            )
        if session.molecules.pop(molecule_id, None) is None:
            raise HTTPException(404, "Struktur nicht gefunden.")
        return {"status": "deleted"}

    @app.get("/")
    async def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
