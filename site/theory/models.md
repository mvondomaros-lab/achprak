# Theoretische Chemie

Die theoretische Chemie untersucht chemische Fragestellungen mithilfe mathematischer Beschreibungen und
computergestützter Verfahren. Sie ergänzt experimentelle Untersuchungen, indem sie beispielsweise
Molekülstrukturen, Energien, Spektren oder Reaktionswege beschreibt und überprüfbare Vorhersagen ermöglicht.
Zum Fachgebiet gehören grundlegende Theorien wie die Quantenmechanik und die statistische Mechanik,
quantitative Berechnungen und Simulationen sowie vereinfachte qualitative Modelle.

Dieser Praktikumsversuch bietet einen ersten anwendungsbezogenen Einblick in das Fachgebiet. Die mathematischen
Grundlagen und die Herleitung der verwendeten Verfahren sind nicht Bestandteil des Versuchs. Sie werden im
weiteren Studium der theoretischen Chemie vertieft: im 3. oder 4. Semester sowie in einem optionalen Modul im
5. oder 6. Semester. Die Zuordnung richtet sich jeweils danach, ob das Studium im Winter- oder Sommersemester
begonnen wurde. Weitere Lehrveranstaltungen folgen im Masterstudium.

## Mathematische Beschreibung

Eine Strukturformel zeigt, welche Atome miteinander verbunden sind. Aus ihr folgen jedoch nicht unmittelbar die
genauen Atompositionen, die elektronische Energie oder das Absorptionsspektrum. Die theoretische Chemie beschreibt
Zusammenhänge zwischen dem Aufbau eines Moleküls und solchen Größen mathematisch.

Dabei werden die Atomkerne durch ihre Atomsorten und Positionen beschrieben. Die Elektronen bestimmen wesentlich
die chemischen Bindungen, die elektronische Energie und die Wechselwirkung mit Licht. Für Moleküle mit vielen
Elektronen lassen sich diese Zusammenhänge nicht ohne Näherungen berechnen. Das Ergebnis einer Rechnung ist daher
keine vollständige Beschreibung des Moleküls, sondern eine Aussage innerhalb eines festgelegten Modells.

<figure markdown="1">
<img src="../../figures/outputs/theoretical_quantities.svg" alt="Schematische Übersicht: Im Rechenmodell werden Atomkerne und Elektronen beschrieben. Daraus werden Molekülstrukturen, elektronische Energien und elektronische Anregungen berechnet." width="800" loading="lazy">

<figcaption markdown="1">
Die Beschreibung von Atomkernen und Elektronen verbindet den molekularen Aufbau mit den im Versuch berechneten
Größen.
</figcaption>
</figure>

## Berechnete Größen im Versuch

Die Rechnungen dieses Versuchs liefern mehrere miteinander verbundene Größen. Eine berechnete Molekülstruktur gibt die
Positionen der Atomkerne an. Elektronische Energien ermöglichen den Vergleich verschiedener Anordnungen desselben
Moleküls. Eine Folge von Strukturen und Energien beschreibt einen untersuchten Reaktionspfad. Berechnete Energien und
relative Stärken elektronischer Anregungen bilden die Grundlage des dargestellten Absorptionsspektrums.

Diese Ergebnisse beantworten unterschiedliche chemische Fragestellungen. Eine Struktur mit niedrigerer elektronischer Energie ist
nicht automatisch stärker gefärbt, und ein Absorptionsspektrum bestimmt keine Reaktionsgeschwindigkeit. Für jede
Aussage muss deshalb die dafür berechnete Größe verwendet werden.

## Rechenmodelle

Ein Rechenmodell bildet gezielt diejenigen Eigenschaften eines Moleküls ab, die für eine bestimmte Fragestellung
benötigt werden. Andere Eigenschaften werden vereinfacht oder nicht berücksichtigt. Ein Modell ist daher keine
vollständige Kopie des untersuchten Moleküls, sondern eine festgelegte Beschreibung mit bekannten Annahmen.

Das Modell legt fest, welche physikalischen Beiträge berücksichtigt werden. Ein numerisches Verfahren wertet die
daraus entstehenden Gleichungen näherungsweise aus. Dasselbe Molekül kann deshalb je nach gesuchter Größe mit
unterschiedlichen Modellen und Verfahren untersucht werden. Die optionalen Methodenabschnitte in der Webapp
dokumentieren die im Versuch eingesetzten Programme, Algorithmen, Prüfungen und Darstellungsannahmen.

## Vorhersagen und Prüfung

Ein Rechenmodell kann Werte oder Trends für Moleküle liefern, die noch nicht experimentell untersucht wurden. Eine
solche Vorhersage ist wissenschaftlich prüfbar, wenn die berechnete Größe, das verwendete Modell und der betrachtete
Anwendungsbereich klar angegeben werden. Ein Modell kann für den Vergleich ähnlicher Moleküle nützlich sein, auch
wenn einzelne berechnete Werte vom Experiment abweichen.

<figure markdown="1">
<img src="../../figures/outputs/prediction_cycle.svg" alt="Schematischer Ablauf von der chemischen Fragestellung über Rechenmodell und Vorhersage zur Prüfung durch Experiment oder Referenzrechnung." width="800" loading="lazy">

<figcaption markdown="1">
Berechnete Vorhersagen werden durch Experimente oder geeignete Referenzrechnungen geprüft. Der Vergleich zeigt, für
welche Fragestellungen ein Modell geeignet ist.
</figcaption>
</figure>

Wie genau ein konkretes Ergebnis ist, hängt vom Modell, von der untersuchten Größe und vom Molekül ab. Aufwendigere
Verfahren können zusätzliche Wechselwirkungen berücksichtigen, liefern aber nicht automatisch genauere Ergebnisse.
Numerische Konvergenz zeigt nur, dass ein Rechenverfahren sein festgelegtes Abbruchkriterium erreicht hat; sie belegt
nicht die Genauigkeit des Modells.

In diesem Versuch vergleichen Sie systematische Reihen substituierter Azobenzole. Wiederholt sich ein berechneter
Trend in mehreren Reihen, können Sie daraus eine begründete Vermutung für ein weiteres Derivat entwickeln. Die
anschließende Rechnung prüft, ob diese Vermutung innerhalb desselben Modells zutrifft. Ob der Zusammenhang auch das
Verhalten realer Moleküle beschreibt, muss durch Experimente oder geeignete Referenzrechnungen geprüft werden.
