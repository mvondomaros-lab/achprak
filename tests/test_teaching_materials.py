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
        with ZipFile(io.BytesIO(response.content)) as archive:
            xml = ET.fromstring(archive.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = ["".join(p.itertext()) for p in xml.findall(".//w:p", ns)]
        titles = re.findall(
            r'<section class="task" id="task-[^"]+"><h3>([^<]+)</h3>', guide
        )
        # The Word template is synchronized after the task editorial review.
        assert titles
        assert len(titles) == len(set(titles))
        assert not re.search(r"Aufgabe \d|<details[^>]*\bopen\b", guide)
        assert "guide-scope" not in client.get("/").text
        text = "\n".join(paragraphs)
        assert "Atome zählen" not in guide and "Atome zählen" not in text
        assert (
            "die Verknüpfung der Atome" in guide and "die Verknüpfung der Atome" in text
        )
        assert "ILIAS" in text
        assert "elektronische Energiebarriere" in text
        assert "Jupyter Notebook" not in text
        assert "Azobenzol farblos" not in text
