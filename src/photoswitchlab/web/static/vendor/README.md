# Bundled browser assets

The app serves these files locally; no CDN or npm build is needed at runtime.
Keep license notices when replacing a library.

| Asset | Version | Source | License |
| --- | --- | --- | --- |
| `ngl.js` | 2.5.0 | [Distribution](https://unpkg.com/ngl@2.5.0/dist/ngl.js), [upstream](https://github.com/nglviewer/ngl) | [MIT](NGL-LICENSE) |
| `chart.js` | 4.5.1 | [Distribution](https://registry.npmjs.org/chart.js/-/chart.js-4.5.1.tgz), [upstream](https://github.com/chartjs/Chart.js) | [MIT](ChartJS-LICENSE) |
| `cie-color.js` | CIE 2019 data | [Observer](https://doi.org/10.25039/CIE.DS.xvudnb9b), [D65](https://doi.org/10.25039/CIE.DS.hjfjmt59) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

The CIE tables are joined by wavelength and restricted to 380–780 nm in 1 nm
steps. See [data provenance](../../../../../docs/solution-color.md#data-provenance).
