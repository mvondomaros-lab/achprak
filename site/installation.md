# Webapp starten

Am Versuchstag erhalten Sie die Adresse der Webapp von Ihren Assistent*innen.
Öffnen Sie diese Adresse im Browser und melden Sie sich gegebenenfalls mit dem
bereitgestellten Benutzerkonto an.

## Durchführung

Die Webapp führt Sie durch drei Schritte:

1. Wählen Sie die cis-/trans-Konfiguration und die Substituenten und erzeugen Sie eine Struktur.
2. Optimieren Sie die Geometrie. Eine Übergangszustandssuche startet von einem konvergierten Minimum.
3. Berechnen und untersuchen Sie das UV/Vis-Spektrum.

Die Aufgaben und Hinweise finden Sie direkt in der Webapp unter **Versuch & Aufgaben**.
Strukturen und Ergebnisse können Sie in den folgenden Schritten wieder auswählen.
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
