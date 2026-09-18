"""Build the editable German protocol from the app's task titles and outputs.

Requires python-docx and lxml in a document-authoring environment, not in the app.
Render and visually inspect the DOCX after running this script; see docs/development.md.
"""

from pathlib import Path
import re

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src/achprak/web/static"
OUTPUT = STATIC / "materials/protokollvorlage.docx"


def build():
    source = html.fromstring((STATIC / "guide.html").read_text())
    tasks = {el.get("id"): el for el in source.xpath('.//details[@class="task"]')}
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    sec.left_margin = sec.right_margin = Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string("192D43")
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.12
    for name, size in [("Title", 25), ("Heading 1", 18), ("Heading 2", 13)]:
        style = doc.styles[name]
        style.font.name, style.font.size = "Arial", Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(7)
    subtitle = doc.styles["Subtitle"]
    subtitle.font.name, subtitle.font.size = "Arial", Pt(14)
    subtitle.font.color.rgb = RGBColor(0, 0, 0)
    subtitle.paragraph_format.space_after = Pt(10)
    for border in doc.styles.element.xpath(".//w:pBdr"):
        border.getparent().remove(border)
    doc.core_properties.title = "Molekulare Photoschalter"
    doc.core_properties.subject = "ACh-Pr · TC Versuch · Praktikumsprotokoll"
    doc.core_properties.author = "ACh-Pr"
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "de-DE")
    normal.element.get_or_add_rPr().append(lang)
    footer = sec.footer.paragraphs[0]
    footer.add_run("ACh-Pr · TC Versuch    |    ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    for run in footer.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor.from_string("586B80")

    def p(text):
        para = doc.add_paragraph()
        for part in re.split(r"(E(?:trans|cis|TS)|ΔE‡)", text):
            if part in ("Etrans", "Ecis", "ETS"):
                para.add_run("E")
                para.add_run(part[1:]).font.subscript = True
            elif part == "ΔE‡":
                para.add_run("ΔE")
                para.add_run("‡").font.superscript = True
            else:
                para.add_run(part)
        return para

    def answer(text="[Ihre Antwort]"):
        para = p(text)
        for run in para.runs:
            run.font.color.rgb = RGBColor.from_string("586B80")

    def task(task_id):
        el = tasks[task_id]
        title = el.find("summary").text.strip()
        doc.add_heading(title, 2)
        text = el.xpath('.//p[@class="protocol-output"]')[0].text_content()
        p(text.removeprefix("Für Ihr Protokoll:").strip())

    def table(headers, rows, widths):
        t = doc.add_table(rows=1, cols=len(headers))
        t.autofit = False
        for col, width in zip(t.columns, widths):
            col.width = Cm(width)
        for c, name, width in zip(t.rows[0].cells, headers, widths):
            c.text = name
            c.width = Cm(width)
        for row in rows:
            for c, value, width in zip(t.add_row().cells, row, widths):
                c.text = value
                c.width = Cm(width)
        for i, row in enumerate(t.rows):
            trpr = row._tr.get_or_add_trPr()
            no_split = OxmlElement("w:cantSplit")
            trpr.append(no_split)
            if i == 0:
                trpr.append(OxmlElement("w:tblHeader"))
            for c in row.cells:
                pr = c._tc.get_or_add_tcPr()
                shade = OxmlElement("w:shd")
                shade.set(
                    qn("w:fill"),
                    "102238" if i == 0 else ("F3F6FA" if i % 2 else "FFFFFF"),
                )
                pr.append(shade)
                margins = OxmlElement("w:tcMar")
                for side in ("top", "left", "bottom", "right"):
                    margin = OxmlElement("w:" + side)
                    margin.set(qn("w:w"), "90")
                    margin.set(qn("w:type"), "dxa")
                    margins.append(margin)
                pr.append(margins)
                borders = OxmlElement("w:tcBorders")
                for side in ("top", "left", "bottom", "right"):
                    border = OxmlElement("w:" + side)
                    border.set(qn("w:val"), "single")
                    border.set(qn("w:sz"), "4")
                    border.set(qn("w:color"), "D9D9D9")
                    borders.append(border)
                pr.append(borders)
                align = OxmlElement("w:vAlign")
                align.set(qn("w:val"), "center")
                pr.append(align)
                for para in c.paragraphs:
                    para.paragraph_format.space_after = Pt(2)
                    for run in para.runs:
                        run.font.size = Pt(9)
                        if i == 0:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)
        p("")

    doc.add_heading("Molekulare Photoschalter", 0)
    doc.add_paragraph("Struktur, Energie und Absorption im Vergleich", "Subtitle")
    p("ACh-Pr · TC Versuch")
    p("Praktikumsprotokoll")
    p("Name: [Name]    Gruppe: [Gruppe]    Datum: [Datum]")
    p(
        "Dokumentieren Sie Ihre Berechnungen und deren Interpretation. Bearbeiten Sie die Aufgaben in der Webapp. Ersetzen Sie die Angaben in eckigen Klammern und fügen Sie gespeicherte Abbildungen mit Beschriftungen ein. Die Überschriften entsprechen den Aufgaben in der Webapp. Die Felder erweitern sich beim Schreiben."
    )
    p(
        "Speichern Sie die Datei regelmäßig. Laden Sie das ausgefüllte Protokoll in ILIAS hoch. Die Grundlagen finden Sie unter https://mvondomaros-lab.github.io/achprak/theory/."
    )
    doc.add_heading("Strukturen erstellen", 1)
    task("task-compare-configurations")
    answer("Name des selbst gewählten Derivats: [Name einschließlich Konfiguration]")
    answer("Unterschied zwischen cis und trans: [höchstens zwei Sätze]")

    doc.add_page_break()
    doc.add_heading("Geometrien und Energiebarrieren untersuchen", 1)
    task("task-compare-optimized-geometries")
    table(
        [
            "Struktur",
            "Elektronische Energie / eV",
            "Diederwinkel / °",
            "Ringabstand / pm",
        ],
        [
            [label, "[Wert]", "[Wert]", "[Wert]"]
            for label in (
                "cis-Startstruktur",
                "trans-Startstruktur",
                "cis-Minimumstruktur",
                "trans-Minimumstruktur",
            )
        ],
        [5, 4, 4, 4],
    )
    answer(
        "ΔE = Etrans − Ecis / (kJ/mol): [Wert]\nGeometrieänderungen und Einordnung des Vorzeichens: [höchstens drei Sätze]"
    )
    task("task-analyze-reaction-path")
    p("")
    answer("[Energieprofil einfügen und beschriften]")
    p("\n\n")
    table(
        ["Richtung", "ΔE‡ / (kJ/mol)", "ΔE‡ / RT bei 298 K"],
        [["trans → cis", "[Wert]", "[Wert]"], ["cis → trans", "[Wert]", "[Wert]"]],
        [5, 6, 6],
    )
    answer(
        "Pfad, Verbindungsprüfung, Barrieren- und RT-Vergleich: [höchstens drei Sätze]"
    )

    doc.add_page_break()
    doc.add_heading("UV/Vis-Spektrum", 1)
    task("task-compare-isomer-spectra")
    table(
        [
            "Minimumstruktur",
            "Maximum / eV",
            "Wellenlänge / nm",
            "UV oder sichtbar",
            "Farbvorhersage",
        ],
        [
            ["cis", "[Wert]", "[Wert]", "[Bereich]", "[Farbe]"],
            ["trans", "[Wert]", "[Wert]", "[Bereich]", "[Farbe]"],
        ],
        [3, 3, 3.5, 3.2, 4.3],
    )
    answer(
        "Bevorzugte Anregung und Grenze der Vorhersage: [höchstens drei Sätze]"
    )
    task("task-compare-substituent-spectra")
    table(
        ["Name und Substitution der trans-Form", "Maximum / eV", "Wellenlänge / nm"],
        [
            [label + " [Name]", "[Wert]", "[Wert]"]
            for label in [
                "unsubstituiert",
                "4-OMe",
                "4-NMe₂",
                "4-CF₃",
                "4-NO₂",
            ]
        ],
        [8, 4, 5],
    )
    answer(
        "Stärkste Verschiebung zu kleinerer Energie: [Derivat und Verschiebung in eV]"
    )

    doc.add_page_break()
    doc.add_heading("UV/Vis-Spektrum", 1)
    task("task-plan-experiment-series")
    answer(
        "Name und Substitutionsmuster des eigenen Derivats: [Name]\nErwartete Verschiebung gegenüber den unsubstituierten Formen: [Vorhersage]"
    )
    table(
        [
            "Konfiguration",
            "Maximum / eV",
            "Wellenlänge / nm",
            "Farbvorhersage",
        ],
        [
            ["cis", "[Wert]", "[Wert]", "[Farbe]"],
            ["trans", "[Wert]", "[Wert]", "[Farbe]"],
        ],
        [3.5, 4, 5, 4.5],
    )
    answer("cis: [Spektrum einfügen und beschriften]")
    p("\n\n")
    answer("trans: [Spektrum einfügen und beschriften]")
    p("\n\n")
    answer("Vorhersage und Ergebnis: [höchstens zwei Sätze]")
    answer("Längstwelliges Gruppenresultat: [Name und Wellenlänge]")
    answer(
        "Stärkster vorhergesagter cis/trans-Farbunterschied: [Name und Farben bei Faktor 1,0]"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
