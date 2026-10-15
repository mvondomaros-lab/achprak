# Licensing policy

PhotoSwitchLab uses MIT for software and CC BY-SA 4.0 for educational content.
The licenses apply to different parts of the project, not as a choice of license
for every file. Copyright for original project material: mvondomaros-lab.

## Software

The [MIT license](LICENSE-MIT) applies to Python and JavaScript code, CSS, HTML
templates and markup, build and figure-generation scripts, configuration, and
tests. It also applies to developer documentation about installation, deployment,
repository maintenance, and testing.

## Educational content

Unless separately credited, original educational content is licensed under
[Creative Commons Attribution-ShareAlike 4.0 International](LICENSE-CC-BY-SA-4.0).
This includes:

- The educational prose in `site/`, including course instructions.
- Exercise text in `src/photoswitchlab/web/static/guide.html` and scientific
  explanations in the app, including prose embedded in HTML or JavaScript.
- Scientific and methodological explanations in `docs/`.
- Original teaching illustrations in `figures/outputs/`, `figures/drawings/`,
  and `src/photoswitchlab/web/static/dihedral.svg`.
- The protocol template in `src/photoswitchlab/web/static/materials/` and its
  educational text in `scripts/build_protocol.py`.

In mixed files, the educational text and illustrations use CC BY-SA 4.0; the
implementation uses MIT. Figure-generation code uses MIT; original teaching
illustrations produced by it use CC BY-SA 4.0.

Suggested attribution: “PhotoSwitchLab, Michael von Domaros,
https://github.com/mvondomaros-lab/photoswitchlab, CC BY-SA 4.0.” Include a
license link and identify changes when sharing adaptations. Shared adaptations
must use CC BY-SA 4.0 or a license permitted by its ShareAlike terms. Commercial
reuse is permitted. The license does not automatically apply to students' own
answers or independently created results.

Permissions already granted for earlier MIT-licensed versions remain available
for those versions. This policy does not revoke them.

## Third-party material

Third-party material retains its own terms and attribution; it is excluded from
the project's general license grants. In particular:

- The electromagnetic spectrum illustration is CC BY-SA 3.0, not CC BY-SA 4.0;
  the atmospheric transmission illustration is public domain. See
  [the image credits](figures/commons/ATTRIBUTION.md).
- The bundled CIE data is CC BY-SA 4.0. Its sources and wavelength restriction
  are recorded in [the vendor guide](src/photoswitchlab/web/static/vendor/README.md)
  and [data provenance](docs/solution-color.md#data-provenance).
- NGL and Chart.js retain their bundled MIT notices; other dependencies retain
  their upstream licenses.

Keep these notices when redistributing the relevant material. Merely collecting
independent works together does not make every work an adaptation of the others.
