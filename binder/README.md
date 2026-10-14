# Experimental Binder deployment

This configuration runs AChPrak as a web application in a temporary Binder
session. Binder's Jupyter server authenticates browser access, and
[Jupyter Server Proxy](https://jupyter-server-proxy.readthedocs.io/en/latest/server-process.html)
starts AChPrak on demand under `achprak/`. The application listens on a private
Unix socket. No notebook is required.

## Launch the branch

Once `binder-support` is available on GitHub, open:

<https://mybinder.org/v2/gh/mvondomaros-lab/achprak/binder-support?urlpath=achprak%2F>

The branch must be pushed before this URL can build it. After merging, replace
`binder-support` with `main`, or use a commit SHA for a fixed repository version.
Use `?urlpath=lab` to open JupyterLab instead; its launcher also offers AChPrak.

## Environment and startup

- `requirements.txt` installs the proxy in the Jupyter environment supplied by
  repo2docker. Binder manages Jupyter and its Hub integration; the project's
  `web-hub` environment and independently managed Hub configuration are not used.
- `postBuild` downloads Pixi 0.81.0 and installs the existing `web` environment
  with `--locked`, including the Linux chemistry packages in `pixi.lock`. There
  is no second chemistry dependency list. It checks imports and the MOPAC
  executable and installs the Jupyter configuration.
- `start` supplies the checkout path and preserves Binder's startup command.
- `jupyter_server_config.py` launches the environment's Python directly, without
  installing packages at session startup. It puts the chemistry executables on
  PATH, limits the instance to one calculation at a time and one thread per
  numerical backend, and retains the application's 600-second job timeout.
  Session cookies use the full proxied application path and are Secure on Binder.

The build targets **x86-64 Linux**, matching the project's existing lockfile.
The chemistry environment is locked; Binder's base image and transitive proxy
dependencies are managed separately and can change. The configuration follows
repo2docker's [build and startup script conventions](https://repo2docker.readthedocs.io/en/latest/configuration/actions/).

## Verify locally

With Docker and [repo2docker](https://repo2docker.readthedocs.io/) installed,
run from the repository root on an x86-64 Linux host:

```sh
jupyter-repo2docker --no-run --image-name achprak-binder .
jupyter-repo2docker --image-name achprak-binder .
```

Open the token-bearing URL printed by repo2docker, then navigate to `achprak/`
under that server's base URL, or launch AChPrak from JupyterLab. An ARM host
requires an x86-64 Docker runtime/emulation; a native ARM build is not supported
by this configuration.

Check the following locally, then repeat on a real Binder session:

1. Open the application and its exercise guide; download the protocol template.
2. Generate the parent molecule, optimize a minimum structure and calculate a
   spectrum. These exercise RDKit, tblite and MOPAC, respectively.
3. Cancel a calculation, reload the page and verify that results remain available
   within the same running session. Check structure and image exports.
4. Open a second independent Binder session and confirm that its results are
   separate. Check that API requests stay under the proxied `achprak/` URL and
   session cookies have the correct path and Secure flag on HTTPS.
5. Try a transition-structure search and record runtime and peak memory before
   deciding whether Binder has enough resources for the intended exercises.

A local configuration check does not establish that Binder can build the image
or that its resource allocation can complete all calculations. A live launch is
required before advertising this as a supported deployment.

### Validation status

Verified on macOS with Apple Silicon on 2026-10-14:

- Installation of the locked `web` environment and the build's backend import
  and MOPAC executable checks.
- A real Jupyter Server 2.21.1 / Jupyter Server Proxy 4.6.0 launch through
  `binder/start`, with AChPrak running on the configured Unix socket. Checked a
  nested user prefix, application assets, guide and protocol downloads, cookie
  scope, structure generation through a chemistry worker, session reload and
  browser-session isolation. The HTTPS command's Secure cookie option was
  checked separately; the local server used HTTP.
- `pixi run --locked -e dev test-web`: 183 passed, 21 skipped. The optional
  chemistry regressions remained disabled; no calculation code changed.
- Shell syntax and Git whitespace checks.

The Linux repo2docker image build and live mybinder.org launch remain unverified.
Docker was unavailable on the verification host. The local smoke check does not
measure Binder memory consumption or transition-structure search runtimes.

## Suitability and limits

Binder is useful for trying the app without installing its chemistry software.
It provides temporary compute sessions, rather than persistent hosting. Results
must be exported before a session ends; AChPrak stores session results in memory,
and Binder does not provide persistent storage.

The public service currently guarantees at least 1 GB RAM, permits up to 2 GB,
and can end sessions after 10 minutes of inactivity. It aims for up to six hours
per session or one CPU-hour for computationally intensive work. See the current
[mybinder.org usage guidelines](https://mybinder.readthedocs.io/en/latest/about/user-guidelines.html)
for limits and workshop policies. Transition-structure searches or larger
substituted molecules may exceed these resources even with one worker. Initial
builds and image pulls also take time because of the chemistry dependencies.

For scheduled teaching that needs predictable capacity or persistent accounts,
use the [managed JupyterHub deployment](../deploy/README.md) or a BinderHub whose
resources you control.
