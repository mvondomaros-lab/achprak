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
    tasks = {
        el.get("id"): el
        for el in source.xpath('.//details[@class="task"]')
    }
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
    for border in doc.styles.element.xpath(".//w:pBdr"):
        border.getparent().remove(border)
    doc.core_properties.title = "Photoschalter Praktikumsprotokoll"
    doc.core_properties.subject = "AChPrak Aufgaben und Ergebnisse"
    doc.core_properties.author = "AChPrak"
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "de-DE")
    normal.element.get_or_add_rPr().append(lang)
    footer = sec.footer.paragraphs[0]
    footer.add_run("AChPrak · Photoschalter    |    ")
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

    doc.add_heading("Photoschalter", 0)
    p("Praktikumsprotokoll · AChPrak")
    p("Name: [Name]    Gruppe: [Gruppe]    Datum: [Datum]")
    p(
        "Dokumentieren Sie Ihre Berechnungen und deren Interpretation. Bearbeiten Sie die Aufgaben in der Webapp. Ersetzen Sie die Angaben in eckigen Klammern und fügen Sie gespeicherte Abbildungen mit Beschriftungen ein. Die Überschriften entsprechen den Aufgaben in der Webapp. Die Felder erweitern sich beim Schreiben."
    )
    p(
        "Speichern Sie die Datei regelmäßig. Laden Sie das ausgefüllte Protokoll in ILIAS hoch. Die Grundlagen finden Sie unter https://mvondomaros-lab.github.io/achprak/theory/."
    )
    doc.add_heading("Strukturen erstellen", 1)
    task("task-compare-configurations")
    answer("[Erklärung, Namen und 3D-Ansichten von cis- und trans-Azobenzol]")
    task("task-build-structures")
    for li in tasks["task-build-structures"].xpath(".//li"):
        answer(li.text_content() + ": [Strukturformel einfügen]")
    answer("Positionsangabe 4,4′: [Erklärung]")
    task("task-interpret-structure-formulas")
    answer("[Namen beider Moleküle einschließlich cis/trans]")
    answer("Überlagerungen in der Zeichnung und räumliche Anordnung: [Text]")

    doc.add_page_break()
    doc.add_heading("Geometrien und Energiebarrieren untersuchen", 1)
    task("task-examine-ring-geometry")
    table(
        ["Struktur", "Elektronische Energie / eV", "Diederwinkel / °", "Ringabstand / pm"],
        [
            [label, "[Wert]", "[Wert]", "[Wert]"]
            for label in (
                "cis-Startstruktur", "trans-Startstruktur",
                "cis-Minimumstruktur", "trans-Minimumstruktur",
            )
        ],
        [5, 4, 4, 4],
    )
    answer("Anordnung der Ringe: [Text]")
    task("task-compare-optimized-geometries")
    answer("[Erwartung und beobachtete Ringstellung für cis und trans; je zwei 3D-Ansichten]")
    answer("ΔE / (kJ/mol): [Wert]\nVorzeichen und energieärmere Konfiguration: [Text]")
    task("task-examine-substituent-geometry")
    answer("[Name, Erwartung, Beobachtung und zwei 3D-Ansichten; Vergleich mit unsubstituiertem trans-Azobenzol]")
    task("task-analyze-reaction-path")
    answer("[Energieprofil; Konfiguration der Enden; Anordnung und Diederwinkel am Anfang, am Energiemaximum und am Ende]")
    answer("Verbindung zwischen cis und trans bestätigt: [Ergebnis der Prüfung]")
    task("task-compare-energy-barriers")
    table(
        ["Richtung", "ΔE‡ / (kJ/mol)", "ΔE‡ / RT bei 298 K"],
        [["trans → cis", "[Wert]", "[Wert]"], ["cis → trans", "[Wert]", "[Wert]"]],
        [5, 6, 6],
    )
    answer("Rechenweg, Unterschied der Barrieren und Vergleich mit RT: [Text]")
    task("task-examine-substituent-barrier")
    answer("Derivat, Vermutung und Ergebnis der Verbindungsprüfung: [Text]")
    answer("[Energieprofil und Ansicht der Übergangsstruktur]")
    answer("Elektronische Energiebarrieren für trans → cis / (kJ/mol): [Derivat] / [unsubstituiert]\nVergleich der Übergangsstrukturen und Prüfung der Vermutung: [Text]")

    doc.add_page_break()
    doc.add_heading("UV/Vis-Spektrum", 1)
    task("task-compare-isomer-spectra")
    table(
        ["Minimumstruktur", "Maximum / eV", "Wellenlänge / nm", "UV oder sichtbar"],
        [
            ["cis", "[Wert]", "[Wert]", "[Bereich]"],
            ["trans", "[Wert]", "[Wert]", "[Bereich]"],
        ],
        [3, 4, 5, 5],
    )
    answer("cis-Azobenzol: [Spektrum einfügen]")
    p("\n\n")
    answer("trans-Azobenzol: [Spektrum einfügen]")
    p("\n\n")
    answer(
        "Verwendeter Faktor für die optische Dichte: [Wert]\nVergleich der Farbvorhersagen und zwei Gründe für Abweichungen: [Text]"
    )

    doc.add_page_break()
    doc.add_heading("UV/Vis-Spektrum", 1)
    task("task-compare-substituent-spectra")
    table(
        ["Name und Substitution der trans-Form", "Maximum / eV", "Wellenlänge / nm"],
        [
            [label + " [Name]", "[Wert]", "[Wert]"]
            for label in [
                "unsubstituiert",
                "4-Me",
                "4-OMe",
                "4-NMe₂",
                "4-CF₃",
                "4-CN",
                "4-NO₂",
            ]
        ],
        [8, 4, 5],
    )
    answer("[Spektren mit Beschriftungen einfügen]")
    p("\n\n")
    answer("Derivat mit stärkster Verschiebung: [Name]\nVerschiebung gegenüber unsubstituiertem trans-Azobenzol / eV: [Wert]\nMaximum im ultravioletten oder sichtbaren Bereich: [Text]")

    doc.add_page_break()
    doc.add_heading("UV/Vis-Spektrum", 1)
    task("task-plan-experiment-series")
    answer("Mindestens zehn Varianten in der Gruppe; Auswahl, Referenz und Verteilung der Rechnungen: [Text]")
    table(
        [
            "Variante und Konfiguration",
            "Erwartete Verschiebung zur Referenz",
            "Maximum / eV",
            "Wellenlänge / nm",
        ],
        [
            [
                f"{n}  [Konfiguration, Positionen, Gruppen]",
                "[Erwartung]",
                "[Wert]",
                "[Wert]",
            ]
            for n in range(1, 11)
        ],
        [6, 5, 3, 3],
    )
    answer("[Referenzspektrum und zwei ausgewählte Spektren mit Beschriftungen einfügen]")
    answer("Vergleich der Erwartungen mit den berechneten Ergebnissen: [Text]")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
