# Einrichtung ⚙️

## Was Sie brauchen

- 💻 einen Laptop  
- 🌐 eine funktionierende Verbindung mit **Eduroam**  
- 📝 ein Programm für Ihr Protokoll, z. B. Word, LibreOffice oder Online Office  

Falls Sie keinen eigenen Laptop dabeihaben, können Sie auch einen Poolrechner mit LibreOffice verwenden.

## Einrichtung in JupyterHub

Bitte folgen Sie diesen Schritten nacheinander.

### 1. JupyterHub öffnen und anmelden

Öffnen Sie im Browser diese Seite:

https://jupyter.uni-marburg.de

Melden Sie sich dort mit Ihrer StudentID an.

```{figure} ../figures/screenshots/screenshot1.png
:alt: Login-Seite von JupyterHub
:width: 800px
:align: center

Anmeldung in JupyterHub.
```

---

### 2. Profil auswählen

Wählen Sie das Profil:

**Basic Usage: 2 CPU cores, 2GB RAM, 12 hours runtime**

Klicken Sie anschließend auf den Start-Button.

```{figure} ../figures/screenshots/screenshot2.png
:alt: Auswahl des Profils in JupyterHub
:width: 800px
:align: center

Auswahl des passenden Profils.
```

---

### 3. Terminal öffnen

Nach dem Start sehen Sie die Jupyter-Oberfläche.

Öffnen Sie dort ein **Terminal**.

```{figure} ../figures/screenshots/screenshot3.png
:alt: Jupyter-Oberfläche mit markierter Schaltfläche Terminal
:width: 800px
:align: center

Die Jupyter-Oberfläche. Öffnen Sie hier ein Terminal.
```

:::{note} Hinweis
Ein Terminal ist ein Fenster, in das man Befehle eingeben kann.  
Sie müssen dafür keine Programmierkenntnisse haben: In diesem Versuch kopieren Sie nur eine Zeile und führen sie aus.
:::

---

### 4. Installationsbefehl kopieren und einfügen

Kopieren Sie die folgende Zeile genau so, wie sie hier steht:

```bash
curl -fsSL https://raw.githubusercontent.com/mvondomaros-lab/achprak/main/install.sh | sh
```

Fügen Sie die Zeile in das Terminal ein und drücken Sie danach die **Enter-Taste**.

```{figure} ../figures/screenshots/screenshot4.png
:alt: Terminal mit eingefügtem Installationsbefehl
:width: 800px
:align: center

Der Installationsbefehl im Terminal.
```

:::{tip} Tipp
Das Einfügen funktioniert meist mit **Strg + V** oder mit Rechtsklick.  
Falls das nicht klappt, hilft Ihnen eine Assistenzperson weiter.
:::

---

### 5. Warten, bis die Installation fertig ist

Nach dem Start der Installation erscheinen mehrere Zeilen im Terminal. Das ist normal.

Bitte warten Sie, bis der Vorgang vollständig abgeschlossen ist.

```{figure} ../figures/screenshots/screenshot5.png
:alt: Terminal während oder nach der Installation
:width: 800px
:align: center

Die Installation läuft im Terminal.
```

:::{important} Wichtig
Schließen Sie das Terminal während der Installation nicht.
:::

---

### 6. Das Notebook öffnen

Öffnen Sie nun die Datei **achprak.ipynb**.

Sie finden sie im Ordner:

**achprak/notebooks**

```{figure} ../figures/screenshots/screenshot6.png
:alt: Dateiansicht mit markiertem Notebook achprak.ipynb
:width: 800px
:align: center

Öffnen Sie das Notebook `achprak.ipynb`.
```

---

### 7. Prüfen, ob der richtige Kernel ausgewählt ist

Oben rechts im Notebook-Fenster sehen Sie die **Kernelauswahl**.

Dort sollte **AChPrak** stehen.

```{figure} ../figures/screenshots/screenshot7.png
:alt: Notebook mit markierter Kernelauswahl AChPrak
:width: 800px
:align: center

Prüfen Sie, ob der Kernel `AChPrak` ausgewählt ist.
```

Falls dort **nicht** AChPrak steht:

- klicken Sie auf den angezeigten Kernel-Namen
- wählen Sie **AChPrak** aus der Liste aus

:::{note} Hinweis
Falls **AChPrak** nicht in der Liste auftaucht, laden Sie die Browserseite einmal neu und öffnen Sie das Notebook anschließend erneut.
:::

```{figure} ../figures/screenshots/screenshot8.png
:alt: Auswahl des Kernels AChPrak
:width: 800px
:align: center

Wählen Sie bei Bedarf den Kernel `AChPrak` aus.
```

---

### 8. Das Notebook starten

Klicken Sie oben auf das Symbol **⏩**.

Damit werden die vorbereiteten Schritte im Notebook gestartet.

```{figure} ../figures/screenshots/screenshot9.png
:alt: Start-Button (⏩) im Notebook
:width: 800px
:align: center

Das ⏩-Symbol zum Starten des Notebooks.
```

## Wenn etwas nicht klappt

Kein Problem. Melden Sie sich einfach bei einer Assistenzperson.  
Wir helfen Ihnen direkt bei der Einrichtung.
