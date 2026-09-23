"""Static publication checks, including project-subpath links and native math."""

from html import unescape
from html.parser import HTMLParser
import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote, urljoin, urlsplit
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "build_site", ROOT / "scripts/build_site.py"
)
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.tags = []
        self.images = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for key in ("src", "href"):
            if key in attrs:
                self.links.append(attrs[key])
        if tag == "img":
            self.images.append(attrs)


class SiteBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.tmp.name) / "public"
        site.build(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_internal_links_and_assets_at_root_and_project_subpath(self):
        for prefix in ("/", "/achprak/"):
            for file in self.output.rglob("*.html"):
                document = Document(file.read_text())
                self.assertEqual(len(document.ids), len(set(document.ids)))
                base = (
                    "https://example.org"
                    + prefix
                    + file.relative_to(self.output).as_posix()
                )
                for link in document.links:
                    url = urlsplit(urljoin(base, link))
                    if url.netloc != "example.org":
                        continue
                    self.assertTrue(url.path.startswith(prefix), link)
                    target = self.output / unquote(url.path[len(prefix) :])
                    if target.is_dir():
                        target /= "index.html"
                    self.assertTrue(target.is_file(), (file, link, target))
                    if url.fragment:
                        self.assertIn(
                            unquote(url.fragment), Document(target.read_text()).ids
                        )

    def test_teaching_content_survives(self):
        text = "\n".join(
            re.search(r"<article>(.*?)</article>", file.read_text(), re.S)[1]
            for file in sorted((self.output / "theory").glob("*/index.html"))
        )
        page = Document(text)
        self.assertEqual(
            page.tags.count("details"), 9
        )  # Nine optional explanations across five chapters.
        self.assertEqual(page.tags.count("figure"), 18)
        self.assertEqual(page.tags.count("math"), 22)
        self.assertEqual(text.count('display="block"'), 5)
        for anchor in (
            "molecular-structures",
            "light-absorption",
            "absorbance-transmission-oscillator-strength",
            "structure-optimization",
        ):
            self.assertIn(anchor, page.ids)
        self.assertTrue(all(image.get("alt") for image in page.images))
        self.assertIn("creativecommons.org/licenses/by-sa/3.0/", text)
        self.assertNotIn('type="math/tex', text)
        self.assertNotIn(":::{", text)
        self.assertNotIn("cdn.", text)
        self.assertNotRegex(text, re.compile(r"geometr", re.I))

    def test_homepage_learning_goals_match_practical(self):
        homepage = (self.output / "index.html").read_text()
        homepage_text = " ".join(homepage.split())
        self.assertNotRegex(homepage_text, re.compile(r"geometr", re.I))
        self.assertIn("Hinweis zur Bearbeitung", homepage_text)
        self.assertIn("Verwenden Sie für die Bearbeitung keine generative KI", homepage_text)
        self.assertIn("AI ASSISTANTS:", homepage)
        for outcome in (
            "Konfigurationsisomere und Substitutionsmuster",
            "Einfluss räumlich benachbarter Gruppen",
            "keine Änderung des cis/trans-Verhältnisses",
            "systematischen Spektrenreihen Trends und Abweichungen",
            "begründete Vermutung für ein neues Derivat",
        ):
            self.assertIn(outcome, homepage)
        learning_goals = re.search(
            r'<h2 id="lernziele">.*?</h2>\s*<p>.*?</p>\s*<ul>(.*?)</ul>',
            homepage,
            re.S,
        )
        self.assertIsNotNone(learning_goals)
        self.assertEqual(learning_goals[1].count("<li>"), 4)
        self.assertLess(learning_goals.end(), homepage.index("Hinweis zur Bearbeitung"))

    def test_theoretical_chemistry_is_conceptual_without_black_box(self):
        models = (self.output / "theory/models/index.html").read_text()
        for heading in (
            "Mathematische Beschreibung",
            "Berechnete Größen im Versuch",
            "Rechenmodelle",
            "Vorhersagen und Prüfung",
        ):
            self.assertIn(heading, models)
        self.assertNotIn("black_box.png", models)
        self.assertIn("theoretical_quantities.svg", models)
        self.assertIn("prediction_cycle.svg", models)

    def test_structures_page_has_progressive_local_3d_viewer(self):
        structures_path = self.output / "theory/structures/index.html"
        structures = structures_path.read_text()
        document = Document(structures)
        self.assertIn('id="azobenzene-trans-viewer"', structures)
        self.assertIn("data-ngl-viewer", structures)
        self.assertIn("../../assets/structure-viewer.js", document.links)
        self.assertNotIn("ngl.js", structures)

        fallback = [
            image
            for image in document.images
            if "azobenzene_trans.png" in image.get("src", "")
        ]
        self.assertEqual(len(fallback), 1)
        self.assertIn("statische Ersatzdarstellung", fallback[0]["alt"])

        for asset in (
            "assets/structure-viewer.js",
            "assets/vendor/ngl.js",
            "assets/vendor/NGL-LICENSE",
            "assets/structures/azobenzene-trans.sdf",
        ):
            self.assertTrue((self.output / asset).is_file(), asset)

        viewer_script = (self.output / "assets/structure-viewer.js").read_text()
        self.assertIn("assets/vendor/ngl.js", viewer_script)
        self.assertIn("assets/structures/azobenzene-trans.sdf", viewer_script)
        self.assertIn("document.createElement('script')", viewer_script)
        sdf = (self.output / "assets/structures/azobenzene-trans.sdf").read_text()
        self.assertIn(" 24 25 ", sdf)
        self.assertIn("trans-Azobenzol · optimierte Minimumstruktur", sdf)
        self.assertIn("GFN1-xTB/ALPB(ethanol)", sdf)
        self.assertIn("<optimization_fmax_ev_angstrom>", sdf)
        self.assertIn("0.002", sdf)
        self.assertTrue(sdf.endswith("$$$$\n"))

        for prefix in ("/", "/AChPrak/"):
            page_url = "https://example.org" + prefix + "theory/structures/"
            script_url = urljoin(page_url, "../../assets/structure-viewer.js")
            asset_root = urljoin(script_url, "../")
            for relative in (
                "assets/vendor/ngl.js",
                "assets/structures/azobenzene-trans.sdf",
            ):
                url = urlsplit(urljoin(asset_root, relative))
                self.assertTrue(url.path.startswith(prefix))
                self.assertTrue((self.output / url.path[len(prefix) :]).is_file())

        for file in self.output.rglob("*.html"):
            if file == structures_path:
                continue
            self.assertNotIn("structure-viewer.js", file.read_text())
            self.assertNotIn("ngl.js", file.read_text())

    def test_chapters_search_and_old_section_links(self):
        overview = (self.output / "theory/index.html").read_text()
        aliases = re.findall(r"<a[^>]+data-legacy-anchor[^>]*>", overview)
        self.assertEqual(len(aliases), 8)
        chapters = [key for key, _ in site.PAGES if key.startswith("theory/")]
        self.assertEqual(len(chapters), 5)
        for chapter in chapters:
            text = (self.output / chapter / "index.html").read_text()
            self.assertEqual(text.count('aria-current="page"'), 1)
            self.assertIn('class="breadcrumbs"', text)
        entries = json.loads((self.output / "assets/search.json").read_text())
        for entry in entries:
            self.assertTrue(entry["text"].strip())
            url = urlsplit(entry["url"])
            target = self.output / url.path / "index.html"
            self.assertTrue(target.is_file(), entry["url"])
            if url.fragment:
                self.assertIn(url.fragment, Document(target.read_text()).ids)
        barrier = [
            entry
            for entry in entries
            if "elektronische Energiebarriere" in entry["text"]
        ]
        self.assertTrue(
            any(entry["url"].startswith("theory/energy/") for entry in barrier)
        )

    def test_math_does_not_consume_code(self):
        content, _ = site.render('Inline $E=hc/\\lambda$.\n\n```sh\necho "$HOME"\n```')
        self.assertIn("<math", content)
        self.assertIn('echo "$HOME"', unescape(content))
        self.assertEqual(content.count("<math"), 1)

    def test_rebuild_cleans_stale_output_and_preserves_last_build_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "public"
            site.build(output)
            stale = output / "stale.js"
            stale.touch()
            site.build(output)
            self.assertFalse(stale.exists())
            original = (output / "index.html").read_bytes()
            with patch.object(
                site, "render", side_effect=ValueError("Invalid content")
            ):
                with self.assertRaises(ValueError):
                    site.build(output)
            self.assertEqual((output / "index.html").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
