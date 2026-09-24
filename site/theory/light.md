# Licht und Absorption

## Das elektromagnetische Spektrum

Sichtbares Licht umfasst einen kleinen Bereich des elektromagnetischen Spektrums.
Dieses umfasst alle Formen elektromagnetischer Strahlung – von energiearmen Radiowellen über Mikrowellen und
Infrarotstrahlung bis hin zu sichtbarem Licht, UV-Strahlung, Röntgenstrahlen und hochenergetischen Gammastrahlen.

Die einzelnen Bereiche unterscheiden sich in der Energie $E$ eines Lichtquants (Photons) und seiner Wellenlänge $\lambda$.
Für ein Photon gilt: Je höher die Energie, desto kürzer die Wellenlänge im Vakuum.
Dies wird durch folgende Gleichung beschrieben:

$$
E = \frac{hc}{\lambda}\,,
$$

wobei $h$ die Planck-Konstante und $c$ die Lichtgeschwindigkeit im Vakuum ist.
Das Produkt der beiden Konstanten beträgt

$$
hc \approx 1{,}9864 \times 10^{-25}\;\text{J m} \;\;\approx\;\; 1239{,}8\;\text{eV nm}.
$$

Ein Elektronenvolt (eV) ist eine Energieeinheit: 1 eV ≈ 1,602 × 10⁻¹⁹ J.
Ein Nanometer (nm) ist ein Milliardstel Meter: 1 nm = 10⁻⁹ m. Mit diesen Einheiten
lassen sich die hier betrachteten Photonenenergien und Wellenlängen ohne sehr kleine Dezimalzahlen angeben.

<figure markdown="1">
<img src="../../figures/commons/electromagnetic_spectrum.svg" alt="Übersicht über das elektromagnetische Spektrum mit markiertem sichtbarem Bereich." width="800" loading="lazy">

<figcaption markdown="1">
Das elektromagnetische Spektrum. Die obere Reihe zeigt (von links nach rechts) stilisierte Darstellungen von
Gammastrahlen, Röntgenstrahlen, UV-Strahlung, sichtbarem Licht, Infrarotstrahlung, Mikrowellen und Radiowellen.
Die untere Reihe vergrößert den sichtbaren Teil des Spektrums.
Tatoute und Phrood~commonswiki, Lizenz: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Quelle: [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Spectre.svg).
</figcaption>
</figure>

## Absorption elektromagnetischer Strahlung {#light-absorption}

Moleküle können mit Licht wechselwirken, indem sie dieses absorbieren. Wie diese Wechselwirkung abläuft, wird durch die
Gesetze der Quantenmechanik beschrieben.
Moleküle besitzen bestimmte, erlaubte Energiezustände. Bei der Absorption eines Photons geht ein Molekül in einen energetisch
höheren Zustand über. Die Energie des Photons entspricht dabei der Energiedifferenz zwischen den beiden Zuständen.
Nicht jeder energetisch passende Übergang ist gleich wahrscheinlich: Manche tragen stark, andere kaum zur Absorption bei.
Schematisch lässt sich dieser Prozess wie folgt darstellen:

<figure markdown="1">
<img src="../../figures/outputs/energy_levels.svg" alt="Zwei alternative Absorptionsübergänge vom Grundzustand: Ein Photon mit 3,0 eV führt in den ersten, eines mit 4,0 eV in den zweiten angeregten Zustand." width="600" loading="lazy">

<figcaption markdown="1">
Zwei mögliche Absorptionsübergänge eines fiktiven Moleküls. Jeder Pfeil steht für die Aufnahme eines Photons,
dessen Energie dem Abstand zwischen Grundzustand und dem jeweiligen angeregten Zustand entspricht.
Beide Übergänge beginnen im Grundzustand; die Pfeile zeigen keine aufeinanderfolgenden Schritte.
Die Energie des Grundzustands ist als Nullpunkt gewählt.
</figcaption>
</figure>

Für eine festgehaltene Molekülstruktur liefert die im Versuch verwendete Rechnung einzelne elektronische Übergänge.
Trägt man ihre Energien und Stärken auf, erhält man das folgende Linienspektrum.

<figure markdown="1">
<img src="../../figures/outputs/spectrum_lines.svg" alt="Das Spektrum eines Moleküls, das Licht mit 3,0 eV und 4,0 eV absorbiert." width="600" loading="lazy">

<figcaption markdown="1">
Schematisches Linienspektrum mit elektronischen Übergängen bei 3,0 eV und 4,0 eV.
Die Linienhöhen zeigen relative Übergangsstärken.
</figcaption>
</figure>

UV/Vis bezeichnet den ultravioletten und den sichtbaren Spektralbereich (englisch *visible*).
UV/Vis-Spektren von Molekülen in Lösung zeigen meist breite Absorptionsbanden. Dazu tragen viele nahe beieinanderliegende
Übergänge mit unterschiedlichen Schwingungszuständen sowie Wechselwirkungen mit der Umgebung bei.
Auch die endliche Lebensdauer angeregter Zustände und die Auflösung des Messgeräts beeinflussen die Linienbreite.
Für die Darstellung eines berechneten Bandenspektrums werden die einzelnen Übergänge mit einer
vorgegebenen Breite dargestellt und überlagert.
Die Bandenlagen zeigen, welche Anregungsenergien zur Absorption beitragen.
Ihre relativen Höhen hängen von den Übergangsstärken und der Überlagerung benachbarter Banden ab.

<figure markdown="1">
<img src="../../figures/outputs/spectrum_bands.svg" alt="Das Bandenspektrum eines Moleküls, das bevorzugt Licht mit 3,0 eV und 4,0 eV absorbiert." width="600" loading="lazy">

<figcaption markdown="1">
Das Bandenspektrum eines Moleküls, das bevorzugt Licht mit 3,0 eV und 4,0 eV absorbiert.
Zur besseren Orientierung wurde das zugrunde liegende Linienspektrum im Hintergrund dargestellt.
</figcaption>
</figure>

<details id="absorbance-transmission-oscillator-strength" markdown="1">
<summary markdown="span">Ergänzung: Absorption, Transmission und Oszillatorstärke</summary>


Absorption ist die Aufnahme von Strahlungsenergie. Die wellenlängenabhängige Transmission
$T(\lambda) = I(\lambda)/I_0(\lambda)$ gibt an, welcher Anteil der einfallenden Lichtintensität
$I_0(\lambda)$ als Intensität $I(\lambda)$ durch eine Probe hindurchtritt. Die dekadische Absorbanz ist
$A(\lambda) = -\log_{10}(T(\lambda))$. Für geeignete verdünnte Lösungen ist sie nach dem
Lambert-Beer-Gesetz proportional zur Konzentration und zur durchstrahlten Schichtdicke.
In Praktika wird dafür oft auch „Extinktion“ gesagt; dieser Begriff kann jedoch zusätzlich Streuverluste einschließen.
Siehe die [IUPAC-Definition der Absorbanz](https://goldbook.iupac.org/terms/view/A00028).

Die Rechnung liefert Oszillatorstärken: dimensionslose Maße für die Stärke elektronischer Übergänge.
Sie sind keine Absorptionswahrscheinlichkeiten zwischen 0 und 1 und keine Absorbanzwerte einer konkreten Probe.
Zusammen mit den Anregungsenergien bestimmen sie die Lage und relative Intensität der berechneten
Absorptionsbanden. Eine gemessene Absorbanz lässt sich daraus ohne weitere Angaben zur Probe nicht ableiten.

</details>

## Lichtabsorption und Lösungsfarbe

Wenn weißes Licht durch eine klare, nicht fluoreszierende Lösung fällt, werden bestimmte Wellenlängen
stärker absorbiert als andere. Die Farbe beim Blick durch die Lösung entsteht aus dem verbleibenden,
durchgelassenen Licht. Absorbiert eine Lösung vor allem blaues Licht, kann sie beispielsweise gelb bis
orange erscheinen. Absorption ausschließlich im UV-Bereich verursacht dagegen keine sichtbare Färbung.

Entscheidend ist die Absorption im gesamten sichtbaren Bereich, ungefähr von 380 bis 780 nm.
Das stärkste Absorptionsmaximum allein legt die Farbe nicht fest: Es kann im UV-Bereich liegen,
während schwächere Banden im sichtbaren Bereich den Farbeindruck bestimmen.
Neben dem Spektrum beeinflussen die Konzentration und die durchstrahlte Schichtdicke, wie viel Licht
die Lösung durchlässt. Auch die Beleuchtung wirkt sich auf die wahrgenommene Farbe aus.

## Einfluss der Substituenten auf die Absorption

Substituenten verändern die Elektronenverteilung und können Grundzustand und angeregte
Zustände unterschiedlich beeinflussen. Wird die Energiedifferenz zwischen zwei Zuständen
kleiner, verschiebt sich der zugehörige Übergang zu kleinerer Anregungsenergie und längerer Wellenlänge (bathochrom).
Eine größere Energiedifferenz entspricht höherer Anregungsenergie und kürzerer Wellenlänge (hypsochrom).
Das Absorptionsmaximum hängt zusätzlich von den Oszillatorstärken und der Überlagerung
der verbreiterten Übergänge ab.

Ein Beispiel ist das auf der Seite zu den [Molekülstrukturen](structures.md#substituenten) gezeigte
4-Methoxy-4′-nitroazobenzol. Die Methoxygruppe (–OCH₃) an Position 4 wirkt als Elektronendonator,
das heißt hier als elektronenschiebender Substituent, der die Elektronendichte im verbundenen
Azobenzol-Gerüst erhöht. Die Nitrogruppe (–NO₂) an Position 4′ wirkt als Elektronenakzeptor:
Sie zieht Elektronendichte aus dem Gerüst ab. Dieses Donator-Akzeptor-Muster
beeinflusst Grundzustand und angeregte Zustände unterschiedlich und kann dadurch die Energiedifferenz
für einen elektronischen Übergang verkleinern. Bei dieser Verbindung liegen Absorptionsbeiträge deshalb
bei kleineren Anregungsenergien als bei unsubstituiertem Azobenzol.

Auch die Position eines Substituenten und die räumliche Anordnung der Molekülteile beeinflussen
diese Wechselwirkungen. Aus der Einordnung als Donator oder Akzeptor allein ergibt sich deshalb
keine feste Reihenfolge der Absorptionsmaxima für alle Substitutionsmuster.

<figure markdown="1">
<img src="../../figures/outputs/substituent_effects.svg" alt="Drei schematische Energieniveausysteme: Nach Substitution kann der Energieabstand zum angeregten Zustand kleiner oder größer sein als im unsubstituierten Vergleichssystem. Die Pfeile zeigen die jeweilige Anregungsenergie." width="700" loading="lazy">

<figcaption markdown="1">
Mögliche Verschiebungen eines elektronischen Übergangs durch Substitution.
Die Pfeillänge zeigt die Anregungsenergie: Links ist der Energieabstand zwischen Grundzustand und angeregtem
Zustand kleiner als beim unsubstituierten Vergleichssystem in der Mitte, rechts ist er größer.
Für jedes Molekül ist die Energie seines eigenen Grundzustands als Nullpunkt gewählt;
verglichen werden die Energieabstände, nicht die Gesamtenergien der Moleküle.
</figcaption>
</figure>

<details markdown="1">
<summary markdown="span">Ergänzung: Orbitale und Delokalisierung</summary>

Ein Orbital ist eine mathematische Funktion zur Beschreibung des räumlichen Zustands eines Elektrons.
Aus ihr lässt sich ableiten, mit welcher Wahrscheinlichkeit das Elektron in einem bestimmten Raumbereich
gefunden wird. Die typische Darstellung eines p-Orbitals zeigt zwei Bereiche hoher Aufenthaltswahrscheinlichkeit
auf gegenüberliegenden Seiten des Atomkerns.
Benachbarte, passend ausgerichtete p-Orbitale können seitlich überlappen und ein π-System bilden.
Die darin beschriebenen Elektronen können über mehrere Atome verteilt sein; dies heißt Delokalisierung.

Eine Veränderung der Delokalisierung beeinflusst die Energien der elektronischen Zustände und damit
auch die Anregungsenergien. Verdrehen sich benachbarte Molekülteile gegeneinander, kann die Überlappung
der p-Orbitale geringer werden. Deshalb können Substituenten die Absorption sowohl durch ihre Wirkung
auf die Elektronenverteilung als auch durch eine Änderung der räumlichen Struktur beeinflussen.

</details>

<details markdown="1">
<summary markdown="span">Ergänzung: Das elektromagnetische Fenster der Atmosphäre</summary>


Absorptionsspektren spielen nicht nur bei der Charakterisierung einzelner Moleküle eine Rolle, sondern sind auch
entscheidend für das Verständnis des Energiehaushalts unserer Erde – und damit des Klimawandels.

Eines der wichtigsten Beispiele ist das Absorptionsspektrum unserer Atmosphäre. Die folgende Darstellung zeigt die
relative Durchlässigkeit (Transmission) für elektromagnetische Strahlung.
Bereiche mit hoher Durchlässigkeit heißen atmosphärische Fenster. Sonnenlicht und die Wärmestrahlung der Erde liegen dabei in unterschiedlichen Wellenlängenbereichen.

<figure markdown="1">
<img src="../../figures/commons/atmospheric_transmission.svg" alt="Diagramm der atmosphärischen Transmission; markiert ist das elektromagnetische Fenster." width="1024" loading="lazy">

<figcaption markdown="1">
Atmosphärische Durchlässigkeit. PNG-Version: Herbertweidner; SVG-Umsetzung: Cepheiden. Quelle/Lizenz: [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Atmosph%C3%A4rische_Durchl%C3%A4ssigkeit_DE.svg).
</figcaption>
</figure>

Ein großer Teil des sichtbaren Sonnenlichts kann die Atmosphäre durchdringen. Die deutlich kühlere Erde gibt
Energie dagegen vor allem als langwellige Infrarotstrahlung ab. Ein anderes, infrarotes Fenster lässt einen Teil
dieser Wärmestrahlung ins Weltall entweichen. Treibhausgase absorbieren in Teilen des Infrarotbereichs und verändern
so den Energieaustausch. Sichtbares Licht und terrestrische Wärmestrahlung passieren also unterschiedliche
Spektralbereiche. Eine Einführung bietet die [NASA zum Strahlungshaushalt der Erde](https://science.nasa.gov/ems/13_radiationbudget/).

</details>
