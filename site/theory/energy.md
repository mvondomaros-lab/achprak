# Energien und Strukturoptimierung

## Molekulare Energien

Die Energie ist eine zentrale Größe der theoretischen Chemie. Sie hängt unter anderem von der Anordnung der
Atomkerne und der Verteilung der Elektronen ab. Neben anziehenden und abstoßenden Wechselwirkungen geht auch
die kinetische Energie der Elektronen in die Rechnung ein.

Die Webapp zeigt elektronische Energien einschließlich der im Modell berücksichtigten Lösungsmittelwirkung.
Die Werte sind häufig groß und negativ; ihr Nullpunkt hängt vom Rechenmodell ab. Für den Vergleich verschiedener
Strukturen sind deshalb die Energiedifferenzen entscheidend.

Verglichen werden Strukturen mit gleicher Zusammensetzung, die mit demselben Rechenmodell untersucht wurden,
beispielsweise die cis- und trans-Konfiguration desselben Azobenzolderivats. Die Struktur mit der niedrigeren
elektronischen Energie ist in diesem Vergleich energetisch günstiger.

Eine Energiedifferenz wird als Energie der Zielstruktur minus Energie der Ausgangsstruktur angegeben.
Ein Zahlenbeispiel verdeutlicht die Vorzeichenkonvention: Für die angenommenen Werte
$E_\mathrm{cis} = -932{,}48\ \text{eV}$ und
$E_\mathrm{trans} = -933{,}00\ \text{eV}$ ergibt sich für die Richtung von cis nach trans:

$$
\Delta E_{\mathrm{cis\to trans}} = E_\mathrm{trans} - E_\mathrm{cis} = -0{,}52\ \text{eV}.
$$

Das negative Vorzeichen bedeutet, dass die trans-Struktur um 0,52 eV niedriger liegt als die cis-Struktur.
Für die umgekehrte Richtung ist die Energiedifferenz positiv: +0,52 eV.

Energiedifferenzen können pro Molekül oder pro Mol angegeben werden. 1 eV pro Molekül entspricht etwa
96,49 kJ/mol. Die molare Energiedifferenz beträgt in diesem Beispiel daher:

$$
\Delta E_\mathrm{m} \approx -50\ \text{kJ mol}^{-1}.
$$

## Strukturoptimierung {#structure-optimization}

Bei einer Strukturoptimierung werden die Atompositionen ausgehend von einer vorgegebenen Struktur verändert.
Für die Suche nach einer Minimumstruktur berechnet das Programm die Energie und wie sie sich bei kleinen
Verschiebungen der Atome ändert. Daraus bestimmt es neue Positionen, mit denen eine niedrigere Energie gesucht
wird. Diese Schritte werden wiederholt, bis die verbleibenden Kräfte auf die Atome unter
einem vorgegebenen Grenzwert liegen.

Die Abhängigkeit der Energie von allen Atompositionen wird als Energiefläche bezeichnet.
Eine Minimumstruktur entspricht einem lokalen Minimum dieser Fläche: Ihre Energie lässt sich durch kleine
Änderungen der inneren Struktur nicht weiter verringern.

Bei Azobenzol und seinen Derivaten gibt es Minima sowohl in der *cis*- als auch in der *trans*-Konfiguration.
Innerhalb einer Konfiguration können weitere Minima auftreten, etwa mit anders verdrehten Substituenten.
Eine Minimumsuche findet nicht zwangsläufig die Anordnung mit der insgesamt niedrigsten Energie.
Die Ausgangsstruktur beeinflusst, welches dieser Minima bei der Optimierung gefunden wird.
Die dargestellte Folge der Optimierungsschritte zeigt den Verlauf der rechnerischen Suche,
nicht die Bewegung eines Moleküls in Echtzeit.

## Reaktionspfade und Energiebarrieren

Ein Reaktionspfad beschreibt eine Folge von Molekülstrukturen, die Ausgangs- und Produktstruktur
miteinander verbindet. Die Reaktionskoordinate gibt die Position entlang dieses Pfads an,
nicht die verstrichene Zeit.

<figure markdown="1">
<img src="../../figures/outputs/energy_profile.svg" alt="Das schematische Energieprofil zeigt die Energie entlang eines Reaktionspfads. cis und trans liegen in lokalen Minima." width="600" loading="lazy">

<figcaption markdown="1">
Das schematische Energieprofil zeigt die Energie entlang eines Reaktionspfads. *cis* und *trans* liegen in lokalen Minima.
Der dargestellte Weg führt über eine Übergangsstruktur (TS, englisch *transition structure*),
die hier am Maximum des Energieprofils liegt.
</figcaption>
</figure>

Eine Übergangsstruktur liegt an einem Sattelpunkt erster Ordnung der Energiefläche.
Entlang einer Richtung der Strukturänderung fällt die Energie auf beiden Seiten ab;
in den übrigen unabhängigen Richtungen steigt sie bei kleinen Änderungen an.
Ein Maximum auf einem beliebig gewählten Pfad reicht deshalb nicht aus, um eine Übergangsstruktur zu erkennen.
Zusätzlich wird geprüft, welche Minimumstrukturen die beiden abwärtsführenden Wege erreichen.

Die elektronische Energiebarriere gegenüber einem Ausgangsminimum ist

$$
\Delta E^\ddagger = E_\mathrm{TS} - E_\mathrm{Minimum}.
$$

Sie charakterisiert den untersuchten Weg. Für Hin- und Rückrichtung wird die Energie derselben
Übergangsstruktur mit der Energie des jeweiligen Ausgangsminimums verglichen. Liegt ein Minimum tiefer,
ist die Barriere von dort aus entsprechend größer. Die Barriere beeinflusst die Reaktionsgeschwindigkeit,
bestimmt sie aber nicht allein.

<details markdown="1">
<summary markdown="span">Ergänzung: Schwingungen und Sattelpunkte</summary>

Eine Schwingungsmode beschreibt ein gemeinsames Auslenkungsmuster der Atome.
Eine imaginäre Frequenz kennzeichnet eine instabile Mode: Bei kleinen Auslenkungen
entlang dieser Richtung nimmt die Energie am Sattelpunkt auf beiden Seiten ab.
Ein Sattelpunkt erster Ordnung besitzt genau eine solche unabhängige innere Mode.
Mit „inneren“ Bewegungen sind Änderungen der relativen Atompositionen gemeint,
nicht Verschiebungen oder Drehungen des gesamten Moleküls.

</details>

<details markdown="1">
<summary markdown="span">Ergänzung: Übergangsstruktur und Übergangszustand</summary>


Die Übergangsstruktur ist die berechnete Molekülstruktur am Sattelpunkt der
Potentialenergiefläche. Diesen Begriff verwenden wir in der Webapp für das
geprüfte Ergebnis. Die Struktur ist kein langlebiges, isolierbares Zwischenprodukt.

Der Übergangszustand (englisch *transition state*) ist ein Begriff der
Übergangszustandstheorie. Er bezeichnet eine Menge von Zuständen an der Grenze
zwischen Edukten und Produkten, nicht nur eine einzelne Molekülstruktur.
Siehe die IUPAC-Begriffe [transition state](https://goldbook.iupac.org/terms/view/T06468)
und [transition structure](https://goldbook.iupac.org/terms/view/T06471).

</details>

<details markdown="1">
<summary markdown="span">Ergänzung: Energiebarriere und Aktivierungsenergie</summary>


Die Aktivierungsenergie $E_\mathrm{a}$ beschreibt, wie sich die Geschwindigkeitskonstante einer Reaktion
mit der Temperatur ändert. Sie ist nicht generell mit unserer elektronischen Energiebarriere
$\Delta E^\ddagger$ identisch. In der Übergangszustandstheorie wird die Geschwindigkeit über eine freie
Aktivierungsenergie $\Delta G^\ddagger$ beschrieben; darin gehen auch thermische Beiträge und Entropie ein.
Diese Größen berechnet die Webapp nicht. Siehe die [IUPAC-Definition der Aktivierungsenergie](https://goldbook.iupac.org/terms/view/A00102).

Die Rechnung untersucht außerdem nur den elektronischen Grundzustand. Bei Azobenzolen können
Wechsel zwischen Zuständen mit unterschiedlicher Elektronenspin-Anordnung (Singulett und Triplett)
zur thermischen Isomerisierung beitragen. Solche Zustandswechsel werden hier nicht berechnet.
Auch eine numerisch bestätigte Übergangsstruktur belegt deshalb nicht den experimentell maßgeblichen
Reaktionsweg oder die Lebensdauer der cis-Form.

</details>
