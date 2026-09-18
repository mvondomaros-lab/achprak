# Modelle und Atomkoordinaten

## Theoretische Chemie

Die theoretische Chemie beschäftigt sich mit chemischen Fragestellungen, die mithilfe nichtexperimenteller Methoden
untersucht werden.  
Dazu gehören:

- grundlegende Theorien wie die Quantenmechanik oder statistische Mechanik,
- computergestützte Berechnungen und Simulationen, mit denen Molekülstrukturen, Energien oder Reaktivitäten bestimmt
  werden,
- die Modellierung komplexer Systeme (z. B. Protein-Docking oder Drug-Design)
- sowie vereinfachte, qualitative Modelle, mit denen sich allgemeine Trends abschätzen lassen.

In diesem Praktikumsversuch werden Sie verschiedene solcher Berechnungen durchführen.  
Wie die zugrundeliegenden Methoden im Detail funktionieren, lernen Sie im Verlauf Ihrer theoretisch-chemischen
Ausbildung (3./4. Semester, optional 5./6. Semester sowie im Masterstudium).

Jede Rechnung verwendet definierte Eingaben, etwa die Molekülstruktur, und liefert Ergebnisse wie Energien
oder Spektren. Die folgende Abbildung stellt diesen Zusammenhang als *Blackbox* dar: Das Rechenverfahren
zwischen Eingabe und Ausgabe ist darin nicht im Detail gezeigt. Für die Einordnung der Ergebnisse sind vor allem
die berechneten Größen und die zugrunde liegenden Annahmen wichtig; die mathematische Herleitung der Verfahren
ist nicht Bestandteil dieses Versuchs. Die optionalen Methodenabschnitte
in der Webapp erläutern, wie die Programme aus Ihren Eingaben Ergebnisse erzeugen, welche numerischen
Prüfungen sie ausführen und wie sie die Ergebnisse darstellen.

<figure markdown="1">
<img src="../../figures/commons/black_box.png" alt="Schematische Darstellung einer Blackbox mit Eingabe und Ausgabe." loading="lazy">

<figcaption markdown="1">
Krauss, Lizenz: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Quelle: [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Blackbox3D.png).
</figcaption>
</figure>

<aside class="callout" markdown="1">
<p class="callout-title" markdown="span">Modell und Genauigkeit</p>


Eine Rechnung beschreibt ein Molekül mit einem Modell. Wie genau ein konkretes Ergebnis ist, hängt von der
Methode, der untersuchten Eigenschaft und dem Molekül ab. Aufwendigere Verfahren können zusätzliche
Wechselwirkungen berücksichtigen, benötigen aber meist mehr Rechenzeit. Sie liefern für eine bestimmte
Fragestellung nicht automatisch genauere Ergebnisse; eine längere Rechenzeit allein belegt keine höhere Genauigkeit.

Dieser Versuch verwendet schnelle Näherungsverfahren. Berechnete Energieunterschiede und Bandenlagen können
deshalb merklich vom Experiment abweichen. Auch relative Verschiebungen der Absorptionsmaxima innerhalb einer
Reihe unterschiedlich substituierter Azobenzole sind Vorhersagen des verwendeten Modells. Ob ein berechneter
Trend das Verhalten der untersuchten Moleküle wiedergibt, muss durch Experimente oder geeignete
Referenzrechnungen geprüft werden.

</aside>

## Atomkoordinaten

Eine Strukturformel zeigt, welche Atome miteinander verbunden sind. Programme können diese Information beispielsweise
als SMILES-Text verarbeiten. Diese Zeichenfolge beschreibt Atome, Bindungen und gegebenenfalls die räumliche Anordnung von Gruppen. Für eine Rechnung an einer räumlichen Struktur werden zusätzlich Atomkoordinaten
benötigt: die Positionen $(x, y, z)$ aller Atome.

Das Strukturerstellungswerkzeug erzeugt für Sie solche atomaren Koordinaten im sogenannten XYZ-Format.
Dieses einfache Textformat ist wie folgt aufgebaut:

```text
[Anzahl Atome]
[Kommentar oder Leerzeile]
[Elementsymbol des ersten Atoms]  [X] [Y] [Z]
[Elementsymbol des zweiten Atoms] [X] [Y] [Z]
[...]
```

Die Koordinaten werden dabei in der Einheit Ångström angegeben ($1\ \text{Å} = 10^{-10}\ \mathrm{m}$).
Die Struktur eines einfachen Wassermoleküls (H₂O) kann zum Beispiel wie folgt im XYZ-Format beschrieben werden:

```text
3

O  0.000  0.000  0.000
H  0.000 -0.757  0.587
H  0.000  0.757  0.587
```

Dieses Format zeigt, dass sich das Sauerstoffatom im Ursprung des Koordinatensystems $(x=0,y=0,z=0)$ befindet und dass
die beiden Wasserstoffatome in der YZ-Ebene liegen $(x = 0)$.

Das XYZ-Format dient in diesem Versuch zur Übergabe molekularer Strukturen zwischen den einzelnen Werkzeugen. Es
fungiert damit sowohl als Eingabe- als auch als Ausgabeformat der jeweiligen Rechenprogramme. Die XYZ-Dateien
werden dabei automatisch erzeugt.
