# Modelle

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
