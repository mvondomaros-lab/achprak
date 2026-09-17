"""Static publication checks, including project-subpath links and native math."""

from html import unescape
from html.parser import HTMLParser
import importlib.util
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
        text = (self.output / "theory/index.html").read_text()
        page = Document(text)
        self.assertEqual(
            page.tags.count("details"), 9
        )  # Eight supplements plus outline.
        self.assertEqual(page.tags.count("figure"), 17)
        self.assertEqual(page.tags.count("math"), 26)
        self.assertEqual(text.count('display="block"'), 5)
        for anchor in (
            "molecular-structures",
            "light-absorption",
            "structure-optimization",
        ):
            self.assertIn(anchor, page.ids)
        self.assertTrue(all(image.get("alt") for image in page.images))
        self.assertIn("creativecommons.org/licenses/by-sa/3.0/", text)
        self.assertNotIn('type="math/tex', text)
        self.assertNotIn(":::{", text)
        self.assertNotIn("cdn.", text)

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
