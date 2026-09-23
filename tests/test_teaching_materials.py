"""Verify the student download and task presentation."""

import io
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from fastapi.testclient import TestClient

from achprak.web.server import create_app


def test_protocol_download_and_tasks_without_starting_a_session():
    with TestClient(create_app()) as client:
        response = client.get("/static/materials/protokollvorlage.docx")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert "set-cookie" not in response.headers
        guide = client.get("/static/guide.html").text
        styles = client.get("/static/app.css").text
        with ZipFile(io.BytesIO(response.content)) as archive:
            xml = ET.fromstring(archive.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = ["".join(p.itertext()) for p in xml.findall(".//w:p", ns)]
        titles = re.findall(
            r'<(?:section|details) class="task" id="task-[^"]+"><(?:h3|summary)>([^<]+)</(?:h3|summary)>',
            guide,
        )
        task_ids = re.findall(r'<details class="task" id="([^"]+)">', guide)
        assert len(task_ids) == len(set(task_ids)) == len(titles) == 9
        assert all(re.fullmatch(r"task-[a-z]+(?:-[a-z]+)*", task_id) for task_id in task_ids)
        for step, count in (("build", 2), ("optimize", 3), ("spectrum", 4)):
            page = re.search(
                rf'<section id="guide-{step}">(.*?)</section>', guide, re.S
            )
            assert page is not None
            assert len(re.findall(r'<details class="task"', page[1])) == count
            # A topic may recur in another step, but headings within a step are distinct.
            page_titles = re.findall(r'<summary>([^<]+)</summary>', page[1])
            assert len(page_titles) == len(set(page_titles))

        assert not re.search(r"Aufgabe \d|<details[^>]*\bopen\b", guide)
        assert "guide-scope" not in client.get("/").text
        text = "\n".join(paragraphs)
        assert "Atome zählen" not in guide and "Atome zählen" not in text
        assert (
            "die Verknüpfung der Atome" in guide and "die Verknüpfung der Atome" in text
        )
        assert "symmetrieäquivalenten Auswahlpositionen" in guide
        assert "Symmetrieäquivalente Auswahlpositionen" in text
        assert "Falls Sie nicht weiterkommen" in guide
        assert "Name des selbst gewählten Derivats" not in text
        assert ".task-panel details { margin: 8px 0;" in styles
        for title in (
            "Reaktionspfad analysieren",
            "Spektren vergleichen",
            "Sterischen Einfluss untersuchen",
            "Substituentenreihe untersuchen",
            "Reihenübergreifende Trends prüfen",
            "Eigenes Derivat untersuchen",
        ):
            assert title in guide and title in text
        for substituent in ("CH₃", "OCH₃", "N(CH₃)₂", "CF₃", "CN", "NO₂"):
            assert substituent in guide and substituent in text
        assert "trans-4,4′-X₂-Azobenzole" in guide
        assert "gemeinsame Ergebnismatrix" in guide
        assert "mindestens eine Abweichung" in guide
        for field in (
            "Sterischer Einfluss und Vergleich",
            "Zugeordnete Reihe",
            "Übergreifender Trend 1",
            "Bezug zur systematischen Reihe",
        ):
            assert field in text
        assert "ILIAS" in text
        assert "elektronische Energiebarriere" in text
        assert "Jupyter Notebook" not in text
        assert "Azobenzol farblos" not in text


def test_spectrum_terms_link_fundamentals_to_contextual_app_help():
    with TestClient(create_app()) as client:
        index = client.get("/").text
        guide = client.get("/static/guide.html").text
        progress = client.get("/static/progress.js").text

    anchor = "theory/light/#absorbance-transmission-oscillator-strength"
    assert index.count(anchor) == 2
    assert "Gewichtete Lichtdurchlässigkeit:" in index
    assert "gewichtete Lichtdurchlässigkeit" in guide
    assert "dimensionsloses Maß dafür, wie stark" not in index
    assert "Die ausgegebenen Übergänge werden" in progress
