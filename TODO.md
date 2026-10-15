# TODO

## Binder startup performance and launch experience

Follow up after the initial Binder exploration (2026-10-14). The user confirmed
that the public Binder session launches and the application works. This confirms
a live launch, but does not establish that all chemistry workflows fit Binder's
resource limits.

The configuration installs the locked Pixi `web` environment during image
construction and opens PhotoSwitchLab through Jupyter Server Proxy. The website
provides a German launch display and uses the fixed commit in `binder/launch.json`.
JupyterLab also has an app launcher entry. Binder's native launch page remains
available as a fallback.

- [x] Measure two cached public launches of the same commit and application
      startup separately. Results are recorded below.
- [ ] Measure a complete cold build, registry upload and public image size;
      repeat cached launches to assess variability. The public API combines
      image pull and session startup in one stage.
- [x] Use writable build caches and remove the installer, archive and caches
      in the same image layer, preserving the installed chemistry environment.
      Exclude local environments and outputs from repo2docker's build context.
      Local image size, chemistry imports and public launch have been checked.
- [x] Pin the teaching launch to a fixed commit, independent of website-only
      changes to `main`. Update `binder/launch.json` when publishing app or
      environment changes. The published reference has passed a live check;
      warm the link again before a course.
- [x] Evaluate CI prebuilding and separate environment/content repositories.
      Neither is introduced: a fixed application commit provides reuse without
      another repository or registry workflow. Public Binder still has to pull
      its image and start a session. Prebuilding is supported through a registry
      image referenced by a Binder Dockerfile; defer that extra publishing
      workflow until repeated live measurements justify it.
- [x] Add a German launch display to the existing installation page using
      Binder's public event stream. Explain first-build delays, show actual
      stages and elapsed waiting time, and offer explicit retry and a native
      Binder fallback. No automatic reconnect creates extra sessions.
- [x] Check the public Binder workflow for unsubstituted azobenzene: structure
      generation, minimum optimization, UV/Vis calculation, export data,
      cancellation of a running calculation and browser-session isolation.
- [ ] Check complete transition-structure searches and substituted molecules
      on Binder, recording memory use and runtimes. Verify file downloads and
      image exports through the browser before claiming every exercise works.
- [x] Update `binder/README.md` for the build cleanup, fixed teaching reference
      and German launch display. Keep live validation distinguished from local
      Docker and browser checks.

### Evidence from the initial public launch

The supplied log showed Pixi environment installation completing at 18 seconds,
the entire `postBuild` step completing in 29 seconds, and image layer export
taking 66 seconds. The session subsequently launched after the registry upload.
These timings suggest that image export and transfer warrant investigation;
they do not measure cached session startup time.

Repeated attempts displayed `failed to create fsnotify watcher: too many open
files`. This matches a reported Binder infrastructure issue. Do not assume a
repository change will fix it; distinguish build failures from interrupted
infrastructure log streaming and session startup failures.

### Local build checks, 2026-10-14

The local Linux x86-64 build reproduced the reported lockfile error. Detailed
Pixi logs identified an unwritable UV cache directory, not changed dependencies.
Explicit writable Pixi and UV cache paths fixed the build while retaining
`--locked`.

With the same dependencies, Docker's image size fell from 5,742,175,659 to
5,370,816,512 bytes (354 MiB, 6.5%). Export took 62.6 s before cleanup and 52.1 s
afterward. Total builds took 89.4 s and 95.8 s respectively. These were single
Apple Silicon runs under x86-64 emulation, with cached base-image layers; they
do not establish faster first launches on public Binder. Raw logs stay local
under the ignored `results/binder-startup/` directory.

The cleaned image passed the real Jupyter proxy check: structure generation,
minimum optimization, UV/Vis calculation, structure exports, cancellation and
separate browser sessions. The three calculations took approximately 3, 9 and
8 seconds under emulation. This is local validation, not a Binder resource test.

The launch display passed six lifecycle tests and browser checks at desktop and
phone widths, including explicit retry and the no-JavaScript native link. The
combined Binder, deployment, teaching-material and website checks passed (22 tests).
The build fix is published as `41b5346`. The public API's `launching` stage combines
image pull and server startup, so it cannot isolate those two timings on its own.

### Public Binder checks, 2026-10-15

The supplied build log for `41b5346` shows `postBuild` completing in 40.2 s,
including temporary-cache cleanup, and image export completing in 59.4 s. The
log ends during registry upload, so it does not establish total build or upload
time. The fixed version subsequently became available in Binder's registry.

Two sequential launches through the public API on the same Binder deployment
found the cached image in 1.0 s and 0.9 s. Their Jupyter servers became ready
after 53.1 s and 8.8 s, respectively; PhotoSwitchLab's first health request then
took another 1.0 s and 0.8 s. These are two observations, not guaranteed startup
times. Neither request rebuilt the image.

On the first test session, unsubstituted trans-azobenzene generation took 3.1 s,
minimum optimization 11.5 s and UV/Vis calculation 6.2 s, including HTTP polling.
The minimum converged. XYZ, SDF and spectrum SVG data were present; a second
browser session could neither see nor delete the first session's structures.
A running transition-structure search was successfully cancelled; it was not
allowed to finish. Both test servers were shut down afterward. Memory use and
complete transition-structure searches remain unmeasured.

The published website serves the German launch display and the correct fixed
reference. Sanitized timing and check results remain local under the ignored
`results/binder-startup/public-live.json` path; no session tokens are recorded.

### References

- [Binder startup speed guide](https://mybinder.readthedocs.io/en/latest/howto/speed.html)
- [Startup optimization discussion linked by the guide](https://discourse.jupyter.org/t/how-to-reduce-mybinder-org-repository-startup-time/4956)
- [Binder interface configuration](https://mybinder.readthedocs.io/en/latest/howto/user_interface.html)
- [Binder launch events](https://binderhub.readthedocs.io/en/latest/api.html)
- [repo2docker CI image prebuilding](https://github.com/jupyterhub/repo2docker-action)
- [Binder startup stages and resource limits](https://mybinder.readthedocs.io/en/latest/about/user-guidelines.html)
- [Reported BIDS file-watcher issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/3654)
- [Binder operations guidance for file-watcher limits](https://mybinder-sre.readthedocs.io/en/latest/deployment/k3s.html#increase-some-fs-limits)

## OER content and naming migration

The project, app and website are named **PhotoSwitchLab**. The app and website
use the subtitle **Computerexperiment** and optional local suffix
** · ACh-PR · Marburg**. Public branding is the default;
Marburg branding can be selected explicitly. The course setting selects branding,
documentation and Marburg's additions to the shared exercises.

- [x] Separate shared exercises from Marburg's protocol-specific assignments,
      required deliverables, group allocation and submission instructions. Keep
      shared task content in one source with course-specific additions.
- [x] Make the public website explain the app for independent learners, with
      Binder and local installation as public entry points. Move Marburg access,
      organisation and ILIAS guidance into a clearly labelled course section.
      The university Hub remains at `lserver.chemie.uni-marburg.de`, accessible
      only from the university network.
- [x] Rename the GitHub repository and Python distribution/package to
      `photoswitchlab`; update imports, commands, static asset paths, lockfile,
      repository links and Git remotes. Existing `ACHPRAK_*` environment variables,
      HTTP/progress identifiers and installed Hub paths are retained for
      deployment compatibility. Binder uses the `photoswitchlab/` route and
      `PHOTOSWITCHLAB_BINDER_ROOT`.
- [x] Refresh the local protocol template's printed website URL and branding
      when revising the Marburg materials; its generator already uses the new
      website URL. Render and inspect the DOCX before publishing that update.
