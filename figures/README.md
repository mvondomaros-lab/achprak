# Teaching figures

Original teaching illustrations use CC BY-SA 4.0; generation scripts use MIT.
External illustrations retain their own terms. See the [licensing policy](../LICENSES.md).

Regenerate one figure or the complete set from the repository root:

```sh
pixi run -e dev python figures/scripts/spectrum_bands.py
pixi run -e dev python figures/scripts/generate.py
```

Both commands accept `--format svg|png|both` (default: `svg`) and
`--output-dir PATH`. Review regenerated figures before committing them.

## Sources and output

- `scripts/`: executable figure sources. Sources and exports share the same stem.
- `outputs/`: published diagrams; PNG previews are ignored.
- `drawings/`: molecular illustrations from the `azobenzene*.py` sources.
- `commons/`: external illustrations; preserve [attribution](commons/ATTRIBUTION.md).
- `dihedral.py`: generates the app's [dihedral illustration](../src/photoswitchlab/web/static/dihedral.svg).

The website uses SVGs; keep published exports in version control.

## Editing

[plot_style.py](../src/photoswitchlab/plot_style.py) defines the shared plot style;
[scripts/style.py](scripts/style.py) handles figure export. Put figure data and
annotations in the individual sources. If you change a published image's display
width, update its export setting so text retains its intended size. Use decimal
commas in German labels.

Molecular drawings use the app's [RDKit renderer](../src/photoswitchlab/structure_drawing.py).
Preserve labels and numbering required by the exercises. External illustrations
and chemical element colors retain their attribution and scientific meaning.
