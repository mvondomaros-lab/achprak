# Wie Moleküle auf Licht reagieren – ein theoretischer Blick auf Photoschalter 💡

## Motivation

Molekulare Photoschalter sind chemische Verbindungen, die auf Licht reagieren, indem sie ihre räumliche Struktur
verändern. Dadurch ändern sich auch ihre chemischen und physikalischen Eigenschaften. Man kann sie sich wie winzige
Kippschalter vorstellen – sie werden jedoch nicht mechanisch betätigt, sondern durch gezielte Lichtbestrahlung zwischen
zwei Zuständen umgeschaltet.

Solche Systeme sind nicht nur faszinierend, sondern auch technologisch relevant.
Sie kommen zum Beispiel in lichtaktivierbaren Arzneistoffen oder in Materialien zum Einsatz, die ihre Eigenschaften
unter Bestrahlung gezielt anpassen.

In diesem Computerexperiment untersuchen Sie exemplarisch einige Photoschalter und berechnen deren Absorptionsspektren
im sichtbaren und ultravioletten Bereich des elektromagnetischen Spektrums.
So erhalten Sie einen ersten Einblick, wie Methoden der theoretischen Chemie zur strukturellen und spektroskopischen
Analyse lichtinduzierter Schaltprozesse eingesetzt werden können.

:::{important} Computerexperiment  
Dieser Versuch wird ausschließlich am Computer durchgeführt.  
Das bedeutet:

- 🧯 keine Unfallgefahr
- 🥽 keine Schutzkleidung erforderlich
- ☕ Getränke sind erlaubt  
  :::

:::{important} Lernziele  
Nach Abschluss dieses Versuches können Sie:

- erklären, wie ein Photoschalter (am Beispiel Azobenzol) zwischen Isomeren wechselt und welche Rolle Licht dabei
  spielt.
- den Zusammenhang zwischen Energie $E$ und Wellenlänge $\lambda$ nutzen und Einheiten sicher umrechnen (J, eV, nm).
- mit den bereitgestellten Werkzeugen Strukturen erzeugen, Eigenschaften visualisieren, Minimumsstrukturen und
  Übergangszustände finden sowie ein UV/Vis‑Spektrum interpretieren.
- Verschiebungen im UV/Vis-Spektrum erknenn und einzelnen Substituenten zuorden.
  :::

## Grundlagen

### Azobenzol

In diesem Versuch arbeiten Sie mit dem Molekül Azobenzol.
Es besteht aus zwei Phenylgruppen, die über eine Azobrücke (–N=N–) miteinander verbunden sind.

:::{figure} ../assets/azobenzene.svg
:width: 350px
:align: left
Azobenzol, dargestellt als Skelettformel.
:::

::::{seealso} Summen-, Struktur- und Skelettformeln
:class: dropdown

Azobenzol besteht aus 12 Kohlenstoff-, 10 Wasserstoff- und 2 Stickstoffatomen und besitzt somit die Summenformel
C₁₂H₁₀N₂.

In den beiden Phenylringen ist jedes Kohlenstoffatom mit zwei weiteren Kohlenstoffatomen verbunden. Je ein
Kohlenstoffatom pro Ring bindet die Azobrücke. Die übrigen Kohlenstoffatome tragen jeweils ein Wasserstoffatom.

Die genauen Bindungsverhältnisse lassen sich mit einer Strukturformel darstellen:

:::{figure} ../assets/azobenzene-explicit.svg
:width: 380px
:align: left
Die Strukturformel des Azobenzols.
:::

Organische Moleküle besitzen häufig ein Grundgerüst aus Kohlenstoffatomen. Zur besseren Übersicht – und um Zeit beim
Zeichnen zu sparen – lässt man in der Skelettformel die Kohlenstoffatome sowie die daran gebundenen Wasserstoffatome
weg.
::::

Azobenzol selbst ist farblos, bildet aber das Grundgerüst für zahlreiche Farbstoffe.
Diese entstehen durch Substitution, also durch Austausch von Wasserstoffatomen gegen andere Atome oder Atomgruppen.
Wird beispielsweise am vierten Kohlenstoffatom eines Phenylrings ein Wasserstoffatom durch eine Methoxygruppe (–OCH₃)
ersetzt, entsteht eine gelbe Verbindung.

:::{figure} ../assets/4-methoxy-azobenzene.svg
:width: 400px
:align: left
4-Methoxyazobenzol – ein gelber Farbstoff.
:::

::::{seealso} Nomenklatur
:class: dropdown

Jede chemische Verbindung kann eindeutig benannt werden; die entsprechenden Regeln werden von der IUPAC (International
Union of Pure and Applied Chemistry) festgelegt.

Ein zentrales Element ist die Durchnummerierung der Kohlenstoffatome im Grundgerüst.
Beim Azobenzol werden die Kohlenstoffatome des ersten Phenylrings mit 1–6 und die des zweiten Rings mit 1′–6′
nummeriert. Die Atome 1 und 1′ sind dabei immer die beiden Kohlenstoffatome, die direkt an die Azobrücke gebunden sind.
In welcher Richtung anschließend weitergezählt wird (im oder gegen den Uhrzeigersinn) hängt normalerweise von den
vorhandenen Substituenten ab – in diesem Versuch wird zur Vereinfachung jedoch eine feste Nummerierung verwendet.

:::{figure} ../assets/azobenzene-numbering.svg
:width: 350px
:align: left
Die in diesem Versuch verwendete Nummerierung der Kohlenstoffatome.
:::

Wird nun beispielsweise am 2. Kohlenstoffatom ein Wasserstoff durch ein Chloratom ersetzt, erhält man die Verbindung
2-Chloroazobenzol.

In diesem Versuch treten die folgenden Substituenten auf:

| Summenformel | Abkürzung | Name des Substituenten |
|--------------|-----------|------------------------|
| CH₃          | Me        | Methyl                 |
| N(CH₃)₂      | NMe₂      | Dimethylamino          |
| CF₃          | CF₃       | Trifluormethyl         |
| OCH₃         | OMe       | Methoxy                |
| F            | F         | Fluor                  |
| SO₂CF₃       | SO₂CF₃    | Trifluormethylsulfonyl |

Tritt ein Substituent mehrfach auf, wird dies durch Präfixe wie *di-*, *tri-* oder *tetra-* angezeigt. Wird z. B. beim
2-Chloroazobenzol zusätzlich am dritten Kohlenstoffatom des zweiten Rings ein weiteres Chloratom eingeführt, entsteht
die Verbindung 2,3′-Dichloroazobenzol.

Mit diesen Regeln können Sie alle im Versuch vorkommenden Moleküle eindeutig benennen. Überprüfen Sie zur Übung, ob es
sich bei der folgenden Verbindung um 3,5-Dimethyl-4-methoxy-2′-fluoro-4′-trifluormethyl-5′-dimethylaminoazobenzol
handelt:

:::{figure} ../assets/azobenzene-derivative.svg
:width: 500px
:align: left
:::
::::

Durch die Azobrücke kann Azobenzol in zwei unterschiedlichen räumlichen Anordnungen (Konformationen) vorliegen.
Alle bisher gezeigten Strukturen entsprechen der trans-Form, bei der die beiden Phenylringe auf gegenüberliegenden
Seiten der Azobrücke stehen.
Bei der cis-Form befinden sich beide Ringsysteme auf derselben Seite.

::::{seealso} E,Z-Nomenklatur
:class: dropdown
Eine andere, systematischere Bezeichnungsweise für die Anordnung von Substituenten an Doppelbindungen verwendet die
Symbole E (für entgegen) und Z (für zusammen). Für unsere Zwecke reichen jedoch trans und cis aus.

::::

Moleküle mit gleicher Summenformel und Molekülmasse, die sich jedoch in der räumlichen Anordnung oder Verknüpfung der
Atome unterscheiden, bezeichnet man als Isomere.

:::{figure} ../assets/cis-azobenzene.svg
:width: 230px
:align: left
Cis-Azobenzol.
:::

Die trans-Form ist energetisch stabiler und wird unter normalen Bedingungen bevorzugt.
Durch Bestrahlung mit Licht geeigneter Wellenlänge kann jedoch eine Umwandlung in die cis-Form ausgelöst werden.
Diese lichtinduzierte Isomerisierung bildet die Grundlage für die photoschaltbaren Eigenschaften des Moleküls.

Ein Beispiel hierfür ist das oben erwähnte 4-Methoxyazobenzol:
Bei Bestrahlung mit ultraviolettem Licht wechselt es von seiner gelblichen trans-Form in eine rot-braune cis-Form.

:::{figure} ../assets/azobenzene-isomerism.svg
:width: 800px
:align: left
Die lichtinduzierte Isomerisierung des Azobenzols.
:::

::::{seealso} Dreidimensionale Visualisierung
:class: dropdown

Chemische Strukturformeln eignen sich gut zur Darstellung grundlegender räumlicher Eigenschaften wie der
cis-trans-Isomerie, sind jedoch durch ihre zweidimensionale Darstellung begrenzt.
Eine Alternative bietet die [3D-Visualisierung](https://de.wikipedia.org/wiki/3D-Visualisierung).
So genannte Kalotten- oder Kugel-Stab-Modelle zeigen Moleküle im Raum. Durch Rotation und Bewegung des Moleküls –
ähnlich wie in einem Computerspiel – entsteht ein umfassenderes räumliches Bild.

:::
{figure} https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Azobenzene-trans-3D-balls.png/512px-Azobenzene-trans-3D-balls.png
:width: 512px
:align: left
Kugel-Stab-Modell des Azobenzols.
:::
::::

### Das elektromagnetische Spektrum

Das Licht, das wir mit dem Auge wahrnehmen können, ist nur ein kleiner Teil des sogenannten elektromagnetischen
Spektrums.
Dieses umfasst alle Formen elektromagnetischer Strahlung – von energiearmen Radiowellen über Mikrowellen und
Infrarotstrahlung bis hin zu sichtbarem Licht, UV-Strahlung, Röntgenstrahlen und hochenergetischen Gammastrahlen.

Die einzelnen Bereiche unterscheiden sich in ihrer Energie $E$ bzw. Wellenlänge $\lambda$.
Grundsätzlich gilt: je höher die Energie, desto kürzer die Wellenlänge.
Dies wird durch folgende Gleichung beschrieben:

$$
E = \frac{hc}{\lambda}\,,
$$

wobei $h$ die Planck-Konstante und $c$ die Lichtgeschwindigkeit im Vakuum ist.
Das Produkt der beiden Konstanten beträgt

$$
hc \approx 1{,}9864 \times 10^{-25}\;\text{J\ m} \;\;\approx\;\; 1239{,}8\;\text{eV\ nm}.
$$

In der Atom- und Molekülphysik verwendet man häufig die Einheiten Elektronenvolt (eV) und Nanometer (nm), da sich damit
deutlich handlichere Zahlenwerte ergeben als mit Joule bzw. Meter.

:::{figure} https://upload.wikimedia.org/wikipedia/commons/f/fc/Spectre.svg
:width: 800px
:align: left
:alt: Tatoute and Phrood~commonswiki, CC BY-SA 3.0, via Wikimedia Commons

Das elektromagnetische Spektrum. Die obere Reihe zeigt (von links nach rechts) stilisierte Darstellungen von
Gammastrahlen, Röntgenstrahlen, UV-Strahlung, sichtbarem Licht, Infrarotstrahlung, Mikrowellen und Radiowellen.
Die untere Reihe vergrößert den sichtbaren Teil des Spektrums.
:::

### Absorption elektromagnetischer Strahlung

Moleküle können mit Licht wechselwirken, indem sie dieses absorbieren. Wie diese Wechselwirkung abläuft, wird durch die
Gesetze der Quantenmechanik beschrieben.
Eine der grundlegenden Erkenntnisse dieser Theorie ist, dass Moleküle nicht Licht beliebiger Energie absorbieren können,
sondern nur ganz bestimmte Energien.
Stimmt die Energie, so wird das Licht aufgenommen und das Molekül in einen um diesen Energiebetrag höheren energetischen
Zustand versetzt.
Schematisch lässt sich dieser Prozess wie folgt darstellen:

:::{figure} ../assets/jablonski.png
:width: 600px
:align: left

Jablonskitermschema eines Absorptionsprozesses.
Das (fiktive) Molekül kann entweder Licht mit 3.0 eV oder 4.0 eV absorbieren, um in den ersten bzw. zweiten angeregten
Zustand versetzt zu werden.
:::

Trägt man auf, wie stark ein Molekül Licht mit einer bestimmten Energie absorbiert, so erhält man ein Linienspektrum.

:::{figure} ../assets/line-spectrum.png
:width: 600px
:align: left

Das Spektrum eines Moleküls, das Licht mit 3.0 eV und 4.0 eV absorbiert.
Die genauen Zahlenwerte der Absorption sind für unseren Versuch nicht relevant; daher wird die Einheit *a.u.* (arbitrary
units) verwendet.
:::

In experimentellen Absorptionsspektren erscheinen jedoch keine scharfen Linien, sondern breite Banden.
Das liegt unter anderem daran, dass im Experiment viele miteinander wechselwirkende Moleküle untersucht werden – häufig
sogar in Lösung.
Außerdem bewegen sich Moleküle aufgrund der Temperatur ständig, wodurch die bevorzugte Übergangsenergie leicht variiert.
Hinzu kommen instrumentelle Effekte (z. B. begrenzte Auflösung) sowie fundamentale quantenmechanische Effekte (z. B.
endliche Lebensdauer der angeregten Zustände).
All dies führt zu einer sogenannten Linienverbreiterung.

Es entsteht ein Bandenspektrum.
Aus der Lage und Form dieser Banden lassen sich wichtige Informationen über den elektronischen Aufbau eines Moleküls
gewinnen.

:::{figure} ../assets/uvvis-spectrum.png
:width: 600px
:align: left

Das Bandenspektrum eines Moleküls, das bevorzugt Licht mit 3.0 eV und 4.0 eV absorbiert.
Zur besseren Orientierung wurde das zugrunde liegende Linienspektrum im Hintergrund dargestellt.
:::

::::{seealso} Für besonders Interessierte: Absorption, Transmission, Extinktion, Übergangswahrscheinlichkeiten
:class: dropdown

Absorption bezeichnet die Aufnahme von Licht durch ein Molekül.
Transmission ist der Anteil des Lichts, der vom Molekül nicht aufgenommen wird und hindurchtritt.
Die Extinktion beschreibt die gesamte Abschwächung der Strahlung und umfasst sowohl Absorption als auch Streuung.
In spektroskopischen Experimenten wird häufig die Extinktion genutzt, da sie direkt von der Konzentration der
absorbierenden Substanz abhängt (Lambert-Beer-Gesetz, siehe auch PC-Versuch).

In diesem Computerversuch wird die Übergangswahrscheinlichkeit berechnet, also die Wahrscheinlichkeit, dass ein Molekül
durch Licht in einen höheren energetischen Zustand angeregt wird.
Diese Größe ist direkt proportional zur Absorption.
::::

::::{seealso} Motivation: Das elektromagnetische Fenster der Atmosphäre
:class: dropdown

Absorptionsspektren spielen nicht nur bei der Charakterisierung einzelner Moleküle eine Rolle, sondern sind auch
entscheidend für das Verständnis des Energiehaushalts unserer Erde – und damit des Klimawandels.

Eines der wichtigsten Beispiele ist das Absorptionsspektrum unserer Atmosphäre. Die folgende Darstellung zeigt die
relative Durchlässigkeit (Transmission) für elektromagnetische Strahlung.
Das gelb markierte elektromagnetische Fenster ist dabei von besonderer Bedeutung für den Wärmehaushalt unseres Planeten.

:::{figure} https://upload.wikimedia.org/wikipedia/commons/8/83/Atmosph%C3%A4rische_Durchl%C3%A4ssigkeit_DE.svg
:width: 1024px
:alt: PNG-Version: Herbertweidner (Public domain, via Wikimedia Commons)

Atmosphärische Durchlässigkeit
:::

Das elektromagnetische Fenster ist deshalb so wichtig, weil nur in diesem Bereich die Sonnenstrahlung nahezu ungehindert
zur Erdoberfläche gelangen kann – und gleichzeitig die von der Erde abgegebene Wärmestrahlung wieder ins Weltall
entweichen kann.
Würde die Atmosphäre in diesem Bereich stärker absorbieren, würde sich die Erde deutlich stärker aufheizen. 🌍
::::

### Theoretische Chemie

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

Für diesen Versuch können Sie sich die eingesetzten Verfahren zunächst als *Blackbox* vorstellen:  
Der innere Aufbau muss nicht bekannt sein – wichtig ist lediglich, dass bestimmte Eingaben (z. B. eine Molekülstruktur)
zu bestimmten Ausgaben führen (z. B. Energie oder Spektrum).

:::{figure} https://upload.wikimedia.org/wikipedia/commons/4/44/Blackbox3D.png
:alt: Krauss, CC BY-SA 4.0 <https://creativecommons.org/licenses/by-sa/4.0>, via Wikimedia Commons
:align: left
:::

::::{danger} Genauigkeit

Die Entwicklung theoretischer Methoden mit dem Ziel, Moleküleigenschaften vollständig *ab initio* vorherzusagen, ist ein
aktiver Bereich der Forschung.
Für einige Eigenschaften existieren bereits sehr zuverlässige Verfahren – teilweise sogar genauer als entsprechende
Experimente.
Andere Eigenschaften lassen sich dagegen deutlich schwieriger vorhersagen.

Für die hier betrachteten Moleküle wäre eine genaue Vorhersage energetischer und spektroskopischer Eigenschaften zwar
grundsätzlich möglich, würde aber sehr rechenintensive Verfahren erfordern. Solche Berechnungen können Stunden, Tage
oder sogar Wochen dauern.

Da dieser Versuch in erster Linie das Interesse an theoretischen Methoden wecken soll, wurden bewusst Verfahren
ausgewählt, die schnelle Ergebnisse liefern – auch wenn diese im Vergleich zum Experiment leichte Abweichungen aufweisen
können.

➡️ **Beachten Sie daher**:  
Absolute Aussagen wie *„Molekül A absorbiert bei 3.0 eV“* sollten vorsichtig interpretiert werden.  
**Vergleichende Aussagen wie *„Molekül B absorbiert bei höheren Energien als Molekül A“* sind hingegen in den meisten
Fällen zuverlässig**.
::::

### Atomkoordinaten

Strukturformeln sind für Chemiker*innen zwar intuitiv verständlich, für die maschinelle Weiterverarbeitung jedoch
ungeeignet.
Deutlich besser geeignet sind atomare Koordinaten, d. h. die Positionen (x, y, z) eines jeden Atoms im Raum.

Das Strukturerstellungswerkzeug erzeugt für Sie solche atomaren Koordinaten im sogenannten XYZ-Format.
Dieses einfache Textformat ist wie folgt aufgebaut:

```text
[Anzahl Atome]
[Kommentar oder Leerzeile]
[Elementsymbol des ersten Atoms]  [X] [Y] [Z]
[Elementsymbol des zweiten Atoms] [X] [Y] [Z]
[...]
```

Die Koordinaten werden dabei in der Einheit Ångström angegeben ($1\ \mathrm{\AA} = 10^{-10}\ \mathrm{m}$).
Die Struktur eines einfachen Wassermoleküls (H₂O) kann zum Beispiel wie folgt im XYZ-Format beschrieben werden:

```text
3

O  0.000  0.000  0.000
H  0.000 -0.757  0.587
H  0.000  0.757  0.587
```

Dieses Format zeigt, dass sich das Sauerstoffatom im Ursprung des Koordinatensystems $(x=0,y=0,z=0)$ befindet und dass
die beiden Wasserstoffatome in der XY-Ebene liegen $(x = 0)$.

Das XYZ-Format dient in diesem Versuch zur Übergabe molekularer Strukturen zwischen den einzelnen Werkzeugen. Es
fungiert damit sowohl als Eingabe- als auch als Ausgabeformat der jeweiligen *Black Boxes*.
Sie selbst müssen keine XYZ-Dateien erstellen – sollten den grundlegenden Aufbau dieses Formats jedoch kennen und
beschreiben können.

### Molekulare Energien

Die vermutlich wichtigste Größe in der theoretischen Chemie ist die Energie eines Moleküls.
Alle Moleküle bestehen aus Atomen – diese wiederum aus Atomkernen und Elektronen.
Diese Teilchen wechselwirken miteinander:
anziehende Wechselwirkungen senken die Energie des Systems, abstoßende Wechselwirkungen erhöhen sie.
Ist die Summe aller Wechselwirkungen anziehend, so bleibt das Molekül stabil und zerfällt nicht in seine Einzelteile.
Das ist bei allen hier betrachteten Molekülen der Fall – aus diesem Grund sind die berechneten Energien negativ.

Vom Betrag her erscheinen die berechneten Energien sehr groß (typischerweise in der Größenordnung
von $-100\,000\ \text{kJ mol}^{-1}$.
Das liegt daran, dass Energien immer relativ zu einem Bezugspunkt angegeben werden.
In theoretisch-chemischen Rechnungen ist dieser Bezugspunkt oft ein hypothetischer Zustand, bei dem alle Atomkerne und
Elektronen unendlich weit voneinander entfernt sind.
Bringt man diese Teilchen in Molekülform zusammen, wird eine sehr große Energiemenge frei – daher der große negative
Wert.
In der Realität betrachtet man jedoch häufig Prozesse, bei denen Moleküle ihre Konformation ändern oder durch chemische
Reaktionen ineinander übergehen.
Bei solchen Veränderungen spielen meist deutlich kleinere Energiemengen eine Rolle.

Die Energieunterschiede zwischen zwei Konformationen lassen sich einfach berechnen.  
Liegt ein Azobenzolderivat beispielsweise in der trans-Konformation mit einer Energie von  
$E_\mathrm{trans} = -90\,000\ \text{kJ mol}^{-1}$ vor und wechselt anschließend in die cis-Konformation mit  
$E_\mathrm{cis} = -89\,950\ \text{kJ mol}^{-1}$, so ergibt sich für den Energieunterschied

$$
\Delta_{\mathrm{trans\to cis}}
= E_\mathrm{cis} - E_\mathrm{trans}
= -89\,950\ \text{kJ mol}^{-1} - (-90\,000\ \text{kJ mol}^{-1})
= +50\ \text{kJ mol}^{-1}.
$$

Ein positiver Wert bedeutet, dass die cis-Konformation energetisch ungünstiger ist (höhere Energie) – der Übergang von
trans nach cis erfordert also Energiezufuhr.

:::{note} Energiedifferenzen

Bitte berechnen Sie Energiedifferenzen zwischen einem Anfangszustand und einem Endzustand immer wie folgt:

$$
\Delta_{\mathrm{Anfang\to Ende}} = E_\mathrm{Ende} - E_\mathrm{Anfang}
$$
:::

### Strukturoptimierung

Moleküle können viele verschiedene räumliche Strukturen annehmen, die sich in ihren Atompositionen – und damit auch in
ihrer Energie – unterscheiden.
Einige dieser Strukturen entsprechen lokalen Energieminima; ihre Energie lässt sich durch kleine Auslenkungen der
Atomkoordinaten nicht weiter verringern.
Im Falle des Azobenzols sind dies die Strukturen, die den cis- und trans-Konformationen zugeordnet werden können.
Eine zentrale Aufgabe der computergestützten Chemie besteht darin, solche Minimumsstrukturen zu finden und zu
charakterisieren – dieser Vorgang wird als Strukturoptimierung bezeichnet.

:::{figure} ../assets/profile.png
:align: left
:width: 600px

Könnte man die Auslenkung aller Atomkoordinaten auf eine einzelne Koordinate projizieren (Reaktionskoordinate), so
würden die cis- und trans-Konformationen des Azobenzols den lokalen Minima dieser Funktion entsprechen. Schon kleinste
geometrische Änderungen weg von diesen Strukturen führen zu einem Energieanstieg.
Der Übergangsstruktur (ÜS) für die cis–trans-Umwandlung entspräche in diesem Fall dem lokalen Maximum zwischen den
beiden Minima.
:::

Mindestens genauso interessant ist jedoch die Suche nach Übergangsstrukturen, also nach lokalen Maxima (bzw.
Sattelpunkten in mehreren Dimensionen).
Die Energiedifferenz zwischen stabilen Minimumsstrukturen und Übergangsstrukturen (Aktivierungsenergie, $E_A$) bestimmt
maßgeblich die Geschwindigkeit chemischer Reaktionen und Umwandlungen.

### Funktionsweise von Photoschaltern

Wie eingangs erwähnt, bezeichnet man als Photoschalter ein Molekül, das durch Licht zwischen zwei definierten Zuständen
umgeschaltet werden kann.  
Diese beiden Zustände unterscheiden sich in ihrer räumlichen Struktur – und damit auch in ihren chemischen bzw.
physikalischen Eigenschaften.  
Das Umschalten erfolgt durch Licht, da die Barrieren zwischen den beiden Zuständen im Grundzustand so hoch sind, dass
sie durch die thermische Energie bei Raumtemperatur nicht überwunden werden können.

Die grundlegende Funktionsweise eines Photoschalters lässt sich wie folgt zusammenfassen:

1. Das Molekül befindet sich zunächst in einem Ausgangszustand (z. B. der trans-Form bei Azobenzol).
2. Trifft Licht der passenden Energie auf das Molekül, wird es absorbiert – das Molekül gelangt in einen angeregten
   elektronischen Zustand.
3. In diesem angeregten Zustand kann sich die räumliche Struktur ändern (z. B. Rotation an einer Doppelbindung). Dadurch
   „schaltet“ das Molekül in den zweiten Zustand um.
4. Nach der strukturellen Veränderung entspannt das Molekül wieder in einen neuen Grundzustand (z. B. cis-Form).

Da cis- und trans-Form unterschiedliche Eigenschaften besitzen (etwa Farbe, Polarität oder Reaktivität), lässt sich das
Molekül wie ein Schalter verwenden – mit Licht als Signal zum Ein- bzw. Umschalten.

:::{figure} ../assets/photoswitch-mechanism.png
:align: left
:width: 600px

Schematische Darstellung der Funktionsweise eines Photoschalters.
Der Wechsel zwischen cis- und trans-Form erfolgt nicht im Grundzustand durch Überwinden des Übergangszustandes.
Stattdessen wird das Molekül zunächst in einen angeregten elektronischen Zustand angeregt, in dem die Umwandlung
stattfinden kann.
:::
