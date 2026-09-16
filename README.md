# AChPrak: Theoretische Chemie im Praktikum

AChPrak ist eine deutschsprachige Browser-Anwendung für Chemiestudierende im
ersten Studienjahr. Sie können Molekülstrukturen erzeugen, ihre Geometrie
optimieren, Übergangszustände suchen und Spektren berechnen. Die
[Praktikumsanleitung](https://mvondomaros-lab.github.io/achprak/) erklärt die
Grundlagen und führt durch die Aufgaben.

Studierende und Lehrende können AChPrak auf dem eigenen Rechner ausführen.
Für Lehrveranstaltungen ist auch die Bereitstellung über einen eigenen
JupyterHub möglich.

## Auf dem eigenen Rechner starten

Unterstützt werden **macOS mit Apple Silicon** und **Linux mit x86-64-Prozessor**.
Für Windows und Intel-Macs enthält das Projekt derzeit keine vorbereitete
Umgebung.

Sie benötigen [Pixi](https://pixi.sh) zur Installation der Rechenprogramme und
[Git](https://git-scm.com/downloads) zum Herunterladen des Projekts. Für die
Installation ist eine Internetverbindung erforderlich. Python und die
Chemieprogramme werden von Pixi installiert; eine separate Jupyter-Installation
ist für den lokalen Betrieb nicht nötig.

1. Installieren Sie Pixi und Git. Öffnen Sie anschließend ein Terminal.
2. Laden Sie das Projekt herunter:

   ```sh
   git clone https://github.com/mvondomaros-lab/achprak.git
   ```

3. Wechseln Sie in den Projektordner:

   ```sh
   cd achprak
   ```

4. Installieren Sie die Anwendung und ihre Abhängigkeiten:

   ```sh
   pixi install --locked -e web
   ```

5. Starten Sie die Anwendung:

   ```sh
   pixi run --locked -e web web
   ```

6. Öffnen Sie **http://127.0.0.1:8000/** in Ihrem Browser. Lassen Sie das Terminal
   während der Arbeit geöffnet. Mit **Strg+C** im Terminal beenden Sie die Anwendung.

Für einen späteren Start öffnen Sie erneut ein Terminal im Projektordner und
führen den Befehl aus Schritt 5 aus. Die Berechnungen laufen auf Ihrem Rechner.
Die benötigten Browser-Bibliotheken sind im Projekt enthalten.

Falls Port 8000 bereits belegt ist, verwenden Sie:

```sh
pixi run --locked -e web web --port 8001
```

Öffnen Sie dann **http://127.0.0.1:8001/**.

## Mit AChPrak arbeiten

1. **Startstruktur erzeugen:** Wählen Sie die cis- oder trans-Konfiguration und
   das Substitutionsmuster. Betrachten Sie die Struktur als Formel oder im
   dreidimensionalen Modell.
2. **Minimum optimieren:** Optimieren Sie die Geometrie. Aus einem konvergierten
   Minimum können Sie anschließend einen Übergangszustand suchen. Dafür sind
   höchstens zwei Substituenten außer H über beide Ringe zusammen zulässig.
3. **Spektrum berechnen:** Berechnen Sie für ein optimiertes Minimum ein
   Absorptionsspektrum im ultravioletten und sichtbaren Bereich (UV/Vis).

<details>
<summary>Hinweise zur Interpretation der Berechnungen</summary>

Ein optimiertes Minimum ist ein lokales Minimum und nicht zwangsläufig die
energieärmste Struktur des Moleküls. Die elektronische Energiebarriere ΔE‡
enthält keine Nullpunkts-, thermischen oder entropischen Korrekturen; sie ist
weder eine Arrhenius-Aktivierungsenergie noch eine freie Aktivierungsenthalpie.
Die Farbansicht veranschaulicht das berechnete Spektrum und ist nicht auf eine
bestimmte Konzentration oder gemessene Lösungsfarbe kalibriert. Erläuterungen zu
den Methoden und ihrer Interpretation finden Sie direkt in der Anwendung und
in der Praktikumsanleitung.

</details>

**Sichern Sie Ihre Ergebnisse vor dem Beenden.** Ergebnisse gehören zur jeweiligen
Browsersitzung. Sie gehen beim Neustart der Anwendung oder nach 24 Stunden ohne
Aktivität verloren. Ein Neuladen der Seite innerhalb derselben Sitzung erhält
die Ergebnisse und verbindet Sie wieder mit einer laufenden Berechnung.
Strukturabbildungen und Spektren können Sie als Bilddateien herunterladen.

## Für Lehrende: Bereitstellung über JupyterHub

Für die Nutzung auf einem einzelnen Rechner gelten dieselben Schritte wie oben.
Für den gemeinsamen Zugang in einer Lehrveranstaltung verwenden Sie die
[Deployment-Anleitung](deploy/README.md) (englisch).

Die Integration setzt einen unabhängig verwalteten JupyterHub voraus. Dieser
übernimmt die Anmeldung und startet für jede Person eine eigene AChPrak-Instanz.
Die Umgebung `web-hub` enthält die Anwendung und den dafür nötigen Proxy.
Die Anleitung beschreibt Installation, Hub-Konfiguration, Funktionsprüfung und
Ressourcenplanung. Der lokale Start allein stellt keine Anmeldung für einen
öffentlich zugänglichen Server bereit.

## Methoden und Weiterentwicklung

Die [Dokumentationsübersicht für Wissenschaft und Lehre](docs/README.md) hilft
bei der Auswahl. Die folgenden technischen Dokumentationen sind auf Englisch:

- [Rechenmethoden, Einstellungen und Grenzen](docs/science-decisions.md)
- [Übergangszustände und Prüfung der Ergebnisse](docs/transition-state.md)
- [Untersuchung der Empfindlichkeit gegenüber Recheneinstellungen](docs/science-benchmark.md)
- [Modell zur Darstellung der Lösungsfarbe](docs/solution-color.md)
- [Entwicklung und Tests](docs/development.md)
