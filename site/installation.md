# Webapp starten

Am Versuchstag erhalten Sie die Adresse der Webapp von Ihren Betreuung.
Öffnen Sie diese Adresse im Browser und melden Sie sich gegebenenfalls mit dem
bereitgestellten Benutzerkonto an.

## Durchführung

Die Webapp führt Sie durch drei Schritte:

1. Wählen Sie *cis* oder *trans* und gegebenenfalls Substituenten. Erzeugen Sie eine Startstruktur und betrachten Sie sie als Strukturformel oder in 3D.
2. Optimieren Sie die Geometrie. Eine Übergangszustandssuche startet von einem erfolgreich optimierten Minimum.
3. Berechnen und untersuchen Sie das UV/Vis-Spektrum eines optimierten Minimums.

Die Aufgaben und Hinweise finden Sie direkt in der Webapp unter **Versuch & Aufgaben**.
Schritt 1 bietet nur Startstrukturen zur Auswahl; in Schritt 2 können Sie auch Minima und Übergangszustände auswählen.
Unter **Was passiert im Hintergrund?** finden Sie in jedem Schritt eine kurze Erklärung der Rechenmethode.
Laden Sie Koordinaten, Bilder und Spektren für Ihr Protokoll herunter. Die Ergebnisse
bleiben bis zum Neustart des Servers oder bis zu 24 Stunden Inaktivität erhalten.

## Lokal auf dem eigenen Computer

Installieren Sie [Pixi](https://pixi.sh), klonen Sie das Repository und führen Sie
im Projektverzeichnis folgende Befehle aus:

```sh
pixi install -e web
pixi run -e web web
```

Öffnen Sie anschließend **http://127.0.0.1:8000/** im Browser.
Weitere Hinweise für Entwicklung und Serverbetrieb stehen in der
[README](https://github.com/mvondomaros-lab/achprak#readme).
