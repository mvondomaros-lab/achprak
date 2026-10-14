# PhotoSwitchLab

**Computerexperiment**

PhotoSwitchLab ist eine deutschsprachige Webapp für Chemiestudierende im ersten
Studienjahr. Sie können Molekülstrukturen erzeugen, Minimumstrukturen optimieren,
Übergangsstrukturen suchen und Spektren berechnen.

## Über Binder starten

[![Mit Binder starten](https://mybinder.org/badge_logo.svg)](https://mvondomaros-lab.github.io/photoswitchlab/installation/?binder=1#uber-binder-starten)

Der Start kann einige Minuten dauern; Berechnungen können langsamer sein als auf
Ihrem eigenen Rechner. Exportieren Sie Ihre Ergebnisse vor dem Ende der Sitzung.
Lange Berechnungen können die Laufzeitgrenzen von Binder erreichen.

## Auf dem eigenen Rechner starten

Unterstützt werden **macOS mit Apple Silicon** und **Linux mit x86-64-Prozessor**.
Für andere Plattformen können Sie Binder verwenden.

1. Installieren Sie [Pixi](https://pixi.sh) und [Git](https://git-scm.com/downloads).
2. Öffnen Sie ein Terminal und laden Sie das Projekt herunter:

   ```sh
   git clone https://github.com/mvondomaros-lab/photoswitchlab.git
   cd photoswitchlab
   ```

3. Installieren und starten Sie die Anwendung:

   ```sh
   pixi install --locked -e web
   pixi run --locked -e web web
   ```

4. Öffnen Sie **http://127.0.0.1:8000/**. Lassen Sie das Terminal während der
   Arbeit geöffnet; mit **Strg+C** beenden Sie die Anwendung.

Für spätere Starts führen Sie im Projektordner erneut
`pixi run --locked -e web web` aus. Ist Port 8000 belegt, ergänzen Sie
`--port 8001` und öffnen Sie **http://127.0.0.1:8001/**.

Für das Marburger Praktikum verwenden Sie:

```sh
pixi run --locked -e web web --course marburg
```

## Anleitung und Lehrveranstaltungen

Die [Website](https://mvondomaros-lab.github.io/photoswitchlab/) erklärt die
Grundlagen. Die wissenschaftlichen Aufgaben stehen in der Webapp.

Für einen eigenen JupyterHub folgen Sie der [Deployment-Anleitung](deploy/README.md).
Technische Dokumentation ist auf Englisch:

- [Binder-Konfiguration](binder/README.md)
- [Entwicklung und Tests](docs/development.md)
- [Rechenmethoden und Auswertungen](docs/README.md)
