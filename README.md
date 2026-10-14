# PhotoSwitchLab

**Molekulare Photoschalter · Computerexperiment**

PhotoSwitchLab ist eine deutschsprachige Browser-Anwendung für Chemiestudierende im
ersten Studienjahr. Sie können Molekülstrukturen erzeugen, Strukturoptimierungen
durchführen, Übergangsstrukturen suchen und Spektren berechnen.

Sie können PhotoSwitchLab über Binder im Browser oder auf Ihrem eigenen Rechner
ausführen. Für Lehrveranstaltungen ist auch die Bereitstellung über einen eigenen
JupyterHub möglich.

## Über Binder starten

Starten Sie die Webapp ohne lokale Installation:

[![Mit Binder starten](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mvondomaros-lab/photoswitchlab/main?urlpath=photoswitchlab%2F)

Der Start kann einige Minuten dauern. Berechnungen können langsamer sein als auf
Ihrem eigenen Rechner. Die Sitzung ist zeitlich begrenzt; exportieren Sie Ihre
Ergebnisse, bevor sie endet. Aufwendige Berechnungen, insbesondere die Suche nach
Übergangsstrukturen, können die Laufzeitgrenzen von Binder erreichen.

Technische Hinweise finden Sie in der [Binder-Anleitung](binder/README.md) (englisch).

## Auf dem eigenen Rechner starten

Unterstützt werden **macOS mit Apple Silicon** und **Linux mit x86-64-Prozessor**.
Für Windows und Intel-Macs enthält das Projekt derzeit keine vorbereitete
Umgebung.

Sie benötigen [Pixi](https://pixi.sh) zur Installation der Rechenprogramme und
[Git](https://git-scm.com/downloads) zum Herunterladen des Projekts.

1. Installieren Sie Pixi und Git. Öffnen Sie anschließend ein Terminal.
2. Laden Sie das Projekt herunter:

   ```sh
   git clone https://github.com/mvondomaros-lab/photoswitchlab.git
   ```

3. Wechseln Sie in den Projektordner:

   ```sh
   cd photoswitchlab
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
führen den Befehl aus Schritt 5 aus.

Falls Port 8000 bereits belegt ist, verwenden Sie:

```sh
pixi run --locked -e web web --port 8001
```

Öffnen Sie dann **http://127.0.0.1:8001/**.

Für die Nutzung im Praktikum der Universität Marburg starten Sie die Anwendung mit:

```sh
pixi run --locked -e web web --course marburg
```

## Für Lehrende: Bereitstellung über JupyterHub

Für den gemeinsamen Zugang in einer Lehrveranstaltung verwenden Sie die
[Deployment-Anleitung](deploy/README.md) (englisch).

## Anleitung und Grundlagen

Die [Praktikumswebsite](https://mvondomaros-lab.github.io/photoswitchlab/) erklärt die
theoretischen Grundlagen und die Durchführung des Computerexperiments. Die Aufgaben
und Erläuterungen zu den Berechnungen finden Sie direkt in der Webapp.

## Methoden und Weiterentwicklung

Die [Dokumentationsübersicht für Wissenschaft und Lehre](docs/README.md) hilft
bei der Auswahl. Die folgenden technischen Dokumentationen sind auf Englisch:

- [Rechenmethoden, Einstellungen und Grenzen](docs/science-decisions.md)
- [Übergangsstrukturen und Prüfung der Ergebnisse](docs/transition-state.md)
- [Untersuchung der Empfindlichkeit gegenüber Recheneinstellungen](docs/science-benchmark.md)
- [Modell zur Darstellung der Lösungsfarbe](docs/solution-color.md)
- [Entwicklung und Tests](docs/development.md)
