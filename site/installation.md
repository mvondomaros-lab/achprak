# Webapp starten

Am Versuchstag erhalten Sie die Adresse der Webapp von Ihrer Betreuung.
Öffnen Sie diese Adresse im Browser und melden Sie sich gegebenenfalls mit dem
bereitgestellten Benutzerkonto an.

## Durchführung

Die Webapp führt Sie durch drei Schritte:

1. Wählen Sie *cis* oder *trans* und gegebenenfalls Substituenten. Erzeugen Sie eine Startstruktur und betrachten Sie sie als Strukturformel oder in 3D.
2. Suchen Sie eine Minimumstruktur. Von einer optimierten Minimumstruktur aus können Sie anschließend eine Übergangsstruktursuche starten.
3. Berechnen und untersuchen Sie das UV/Vis-Spektrum einer optimierten Minimumstruktur.

Die Aufgaben und Hinweise finden Sie direkt im Aufgabenbereich der Webapp.
Schritt 1 bietet nur Startstrukturen zur Auswahl; in Schritt 2 können Sie auch Minimumstrukturen und Übergangsstrukturen auswählen.
Der Methodenabschnitt jedes Schritts enthält Angaben zur Rechenmethode,
zu den dargestellten Ergebnissen und zu den Annahmen der Rechnung.
Exportieren Sie Strukturansichten und Spektren als PNG für Ihr Protokoll. Die Ergebnisse
bleiben bis zum Neustart des Servers oder bis zu 24 Stunden Inaktivität erhalten.

Während einer Optimierung zeigt die Webapp die berechneten Zwischenschritte. Nach Abschluss können Sie
den Optimierungsverlauf oder den Reaktionspfad einer Übergangsstruktur abspielen und untersuchen.
Die Wiedergabe zeigt eine Folge berechneter Strukturen, keinen zeitlichen Ablauf einer Molekülbewegung.
Bei der Spektrenrechnung werden die gemeldete Rechenphase und kurze Erläuterungen angezeigt.
Die Erläuterungen wechseln während längerer Rechenschritte; daraus lässt sich keine verbleibende Rechenzeit ableiten.

## Lokal auf dem eigenen Computer

Installieren Sie [Pixi](https://pixi.sh), klonen Sie das Repository und führen Sie
im Projektverzeichnis folgende Befehle aus:

```sh
pixi install -e web
pixi run -e web web
```

Öffnen Sie anschließend [http://127.0.0.1:8000/](http://127.0.0.1:8000/) im Browser.
Weitere Hinweise für Entwicklung und Serverbetrieb stehen in der
[README](https://github.com/mvondomaros-lab/achprak#readme).
