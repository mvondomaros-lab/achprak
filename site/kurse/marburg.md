# Praktikum in Marburg

<p class="subtitle">Allgemeines Chemiepraktikum · Universität Marburg</p>

Diese Hinweise gelten für Studierende im Allgemeinen Chemiepraktikum der
Universität Marburg. Die [Grundlagen](../theory.md) und die wissenschaftlichen
Aufgaben in der Webapp sind auch für die selbstständige Nutzung zugänglich.

## Zugang zum Universitätsserver

Öffnen Sie [https://lserver.chemie.uni-marburg.de](https://lserver.chemie.uni-marburg.de)
im Browser. Der Server ist nur aus dem Universitätsnetz erreichbar. Die Zugangsdaten
erhalten Sie vor Ort von Ihrer Betreuung.

Für die Arbeit auf dem eigenen Rechner folgen Sie der
[Installationsanleitung](https://github.com/mvondomaros-lab/photoswitchlab#auf-dem-eigenen-rechner-starten).
Starten Sie die Anwendung für das Marburger Praktikum anschließend mit:

```sh
pixi run --locked -e web web --course marburg
```

## Aufgaben bearbeiten

Bearbeiten Sie die Pflichtaufgaben in allen drei Versuchsschritten der Webapp.
Im Aufgabenbereich steht für jeden Schritt, was Sie untersuchen und welche
Ergebnisse Sie im Protokoll festhalten sollen. Freiwillige Vertiefungen gehören
nicht zum Pflichtteil. Die Substituentenreihen für die Gruppenarbeit erhalten Sie
von Ihrer Betreuung.

## Protokoll führen

Laden Sie die [Protokollvorlage im DOCX-Format](../../src/photoswitchlab/web/static/materials/protokollvorlage.docx)
herunter und bearbeiten Sie sie mit Word oder LibreOffice Writer. Die Überschriften entsprechen
den Aufgaben. Tragen Sie berechnete Werte mit Einheiten ein und fügen Sie die
geforderten Strukturansichten, Energieprofile und Spektren ein. Kennzeichnen Sie
Modellvorhersagen, wo die Aufgaben es verlangen.

Speichern Sie die Vorlage und exportierte Abbildungen während der Arbeit auf
Ihrem Computer. Ergebnisse in der Webapp gehen beim Serverneustart verloren und
werden nach 24 Stunden Inaktivität gelöscht.

## Protokoll besprechen und abgeben

Besprechen Sie das ausgefüllte Protokoll mit Ihrer Betreuung und laden Sie es
anschließend in [ILIAS](https://ilias.uni-marburg.de/) hoch.
