# Webapp starten

Öffnen Sie die [Webapp](https://lserver.chemie.uni-marburg.de) im Browser.
Sie ist nur aus dem Universitätsnetz erreichbar. Die Zugangsdaten erhalten Sie
vor Ort von Ihrer Betreuung.

Die Aufgaben stehen in der Webapp. Hinweise zur Bearbeitung und Abgabe finden
Sie unter [Aufgaben und Protokoll](tasks.md).

## Optional: Lokal starten

Wenn Sie die Webapp unabhängig vom Praktikumsserver auf Ihrem Computer
ausführen möchten, installieren Sie [Pixi](https://pixi.sh), klonen Sie das
Repository und führen Sie im Projektverzeichnis folgende Befehle aus:

```sh
pixi install -e web
pixi run -e web web
```

Öffnen Sie anschließend [http://127.0.0.1:8000/](http://127.0.0.1:8000/) im Browser.
Weitere Hinweise für Entwicklung und Serverbetrieb stehen in der
[README](https://github.com/mvondomaros-lab/achprak#readme).
