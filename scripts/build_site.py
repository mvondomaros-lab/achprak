"""Build the teaching pages as self-contained HTML/CSS, or serve a live preview."""

from __future__ import annotations

import argparse
import functools
import html
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
from string import Template
import tempfile
import threading
import time
from urllib.parse import urlsplit

import markdown
from latex2mathml.converter import convert

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUTPUT = SITE / "_build"
PAGES = (
    ("index", "Molekulare Photoschalter"),
    ("theory/structures", "Molekülstruktur und Isomerie"),
    ("theory/light", "Licht und Absorption"),
    ("theory/models", "Theoretische Chemie"),
    ("theory/energy", "Energien und Strukturoptimierung"),
    ("theory/photoswitches", "Funktionsweise von Photoschaltern"),
    ("installation", "Webapp starten"),
    ("tasks", "Aufgaben und Protokoll"),
)


def render(source: str) -> tuple[str, str]:
    md = markdown.Markdown(
        extensions=["extra", "toc", "pymdownx.arithmatex"],
        extension_configs={
            "toc": {"toc_depth": "2-3"},
            "pymdownx.arithmatex": {"preview": False},
        },
    )
    content = md.convert(source)

    def math(match):
        display = "block" if "mode=display" in match[1] else "inline"
        return convert(html.unescape(match[2]), display=display)

    content = re.sub(
        r'<script type="(math/tex[^"]*)">(.*?)</script>', math, content, flags=re.S
    )
    return content, md.toc


def page_url(slug: str) -> str:
    return "" if slug == "index" else slug + "/"


def build(output: Path = OUTPUT) -> None:
    """Render everything before replacing output, leaving the last build on errors."""
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".site-build-", dir=output.parent) as tmp:
        stage = Path(tmp)
        shutil.copytree(SITE / "assets", stage / "assets")
        shutil.copy2(
            ROOT / "src/achprak/web/static/header.css", stage / "assets/header.css"
        )
        vendor = stage / "assets/vendor"
        vendor.mkdir(parents=True, exist_ok=True)
        for name in ("ngl.js", "NGL-LICENSE"):
            shutil.copy2(ROOT / "src/achprak/web/static/vendor" / name, vendor / name)
        template = Template((SITE / "template.html").read_text())
        search = []
        for index, (slug, label) in enumerate(
            (*PAGES, ("theory", "Theoretische Grundlagen"))
        ):
            source = (SITE / f"{slug}.md").read_text()
            title, body = source.split("\n", 1)
            title = title.removeprefix("# ")
            subtitle = ""
            subtitle_match = re.search(r'<p class="subtitle">(.*?)</p>', body)
            if subtitle_match:
                subtitle = subtitle_match[0]
                body = body.replace(subtitle, "", 1)
            content, outline = render(body)
            root = "./" if slug == "index" else "../" * len(Path(slug).parts)

            def local_url(match):
                attr, url = match.groups()
                parts = urlsplit(html.unescape(url))
                if parts.scheme or parts.netloc or not parts.path:
                    return match[0]
                path = (SITE / f"{slug}.md").parent.joinpath(parts.path).resolve()
                if path.suffix == ".md" and path.is_relative_to(SITE):
                    target = root + page_url(
                        path.relative_to(SITE).with_suffix("").as_posix()
                    )
                else:
                    relative = path.relative_to(ROOT)
                    target = root + "media/" + relative.as_posix()
                    destination = stage / "media" / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, destination)
                if parts.fragment:
                    target += "#" + parts.fragment
                return f'{attr}="{html.escape(target, quote=True)}"'

            content = re.sub(r'(href|src)="([^"]+)"', local_url, content)

            if slug == "theory":
                destination = stage / "theory/index.html"
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(
                    '<!doctype html><html lang="de"><meta charset="utf-8">'
                    "<title>Grundlagen</title>"
                    + content
                    + "<script>const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));"
                    'location.replace(target?.href || "structures/");</script></html>'
                )
                continue

            def nav_link(key, text):
                return (
                    f'<a href="{root}{page_url(key)}"'
                    + (' aria-current="page"' if key == slug else "")
                    + f">{html.escape(text)}</a>"
                )

            navigation = nav_link("index", "Versuchsüberblick")
            navigation += '<section class="nav-group"><h2>Grundlagen</h2>'
            navigation += "<ul>"
            for key, text in PAGES:
                if key.startswith("theory/"):
                    navigation += "<li>" + nav_link(key, text) + "</li>"
            navigation += (
                '</ul></section><section class="nav-group"><h2>Durchführung</h2>'
                "<ul>"
            )
            navigation += "<li>" + nav_link("installation", "Webapp starten") + "</li>"
            navigation += (
                "<li>" + nav_link("tasks", "Aufgaben und Protokoll") + "</li>"
                "</ul></section>"
            )
            chapter_keys = [key for key, _ in PAGES if key.startswith("theory/")]
            if slug in chapter_keys:
                eyebrow = "Grundlagen"
            else:
                eyebrow = {
                    "index": "ACh-Pr · TC Versuch",
                    "installation": "Durchführung",
                    "tasks": "Durchführung",
                }[slug]
            pagination = []
            for other, direction in ((index - 1, "Zurück"), (index + 1, "Weiter")):
                if 0 <= other < len(PAGES):
                    key, text = PAGES[other]
                    pagination.append(
                        f'<a href="{root}{page_url(key)}"><span>{direction}</span>{text}</a>'
                    )
            document = template.substitute(
                title=html.escape(title),
                subtitle=subtitle,
                tab_title="Molekulare Photoschalter"
                if slug == "index"
                else html.escape(title) + " · ACh-Pr",
                root=root,
                slug=slug,
                content=content,
                navigation=navigation,
                pagination="".join(pagination),
                outline_sidebar=(
                    f'<nav class="outline" aria-label="Auf dieser Seite"><details open><summary>Auf dieser Seite</summary>{outline}</details></nav>'
                    if outline.count("<a ") >= 2
                    else ""
                ),
                eyebrow=eyebrow,
                page_scripts=(
                    f'<script src="{root}assets/structure-viewer.js" defer></script>'
                    if slug == "theory/structures"
                    else ""
                ),
                breadcrumbs=(
                    f'<nav class="breadcrumbs" aria-label="Pfad"><span>Grundlagen</span><span aria-hidden="true"> / </span><span>{html.escape(label)}</span></nav>'
                    if slug in chapter_keys
                    else ""
                ),
            )
            destination = stage / page_url(slug) / "index.html"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(document)
            # Section-sized search results include optional explanations and captions.
            search_content = re.sub(
                r'<details class="legacy-links".*?</details>', "", content, flags=re.S
            )
            for section in re.split(r"(?=<h[23] id=)", search_content):
                heading = re.match(r'<h[23] id="([^"]+)">(.*?)</h[23]>', section)
                text = html.unescape(re.sub(r"<[^>]+>", " ", section))
                if not text.strip():
                    continue
                search.append(
                    {
                        "title": label
                        + (
                            " · " + re.sub("<[^>]+>", "", heading[2]) if heading else ""
                        ),
                        "url": page_url(slug) + ("#" + heading[1] if heading else ""),
                        "text": " ".join(text.split()),
                    }
                )
        (stage / "assets/search.json").write_text(
            json.dumps(search, ensure_ascii=False)
        )
        (stage / ".nojekyll").touch()
        # Replace individual files atomically so an open preview never observes
        # a missing output directory, even when another build runs alongside it.
        published = set()
        for source in stage.rglob("*"):
            if source.is_file():
                relative = source.relative_to(stage)
                published.add(relative)
                destination = output / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(source, destination)
        for old in output.rglob("*"):
            if old.is_file() and old.relative_to(output) not in published:
                old.unlink(missing_ok=True)
        for directory in sorted(output.rglob("*"), reverse=True):
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
    print(f"Built {len(PAGES)} pages in {output}", flush=True)


RELOAD = b"""<script>
let revision;
setInterval(async () => {
  try {
    const next = await (await fetch('/__revision', {cache: 'no-store'})).text();
    if (revision !== undefined && next !== revision) location.reload();
    revision = next;
  } catch (_) {}
}, 700);
</script>"""


def snapshot():
    paths = [SITE, ROOT / "figures", ROOT / "src/achprak/web/static"]
    files = []
    for path in paths:
        files.extend(
            p
            for p in path.rglob("*")
            if p.is_file() and OUTPUT not in p.parents and ".site-build-" not in str(p)
        )
    state = []
    for path in sorted(files):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue  # Editors may replace a file between directory scan and stat.
        state.append((str(path), stat.st_mtime_ns, stat.st_size))
    return tuple(state)


def serve(port: int):
    build()
    revision = str(time.time_ns())
    lock = threading.RLock()
    stopped = threading.Event()

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            if self.path != "/__revision":
                super().log_message(format, *args)

        def do_GET(self):
            with lock:
                if self.path == "/__revision":
                    data = revision.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                path = Path(self.translate_path(self.path))
                if path.is_dir():
                    path /= "index.html"
                if (
                    path.is_file()
                    and path.suffix == ".html"
                    and urlsplit(self.path).path.endswith(("/", ".html"))
                ):
                    data = path.read_bytes().replace(b"</body>", RELOAD + b"</body>")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    super().do_GET()

    def watch():
        nonlocal revision
        previous = snapshot()
        while not stopped.wait(0.5):
            current = snapshot()
            if current == previous:
                continue
            previous = current
            try:
                with lock:
                    build()
                    revision = str(time.time_ns())
            except Exception as error:
                print(
                    f"Build failed; keeping last successful preview: {error}",
                    flush=True,
                )

    server = ThreadingHTTPServer(
        ("127.0.0.1", port), functools.partial(Handler, directory=str(OUTPUT))
    )
    threading.Thread(target=watch, daemon=True).start()
    print(f"Live preview: http://127.0.0.1:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stopped.set()
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=3000)
    args = parser.parse_args()
    serve(args.port) if args.serve else build()
