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

- [ ] Measure image size and timings for a first build and subsequent launches
      of the same commit. Separate build, registry upload, image pull, session
      startup and application startup times.
- [x] Use writable build caches and remove the installer, archive and caches
      in the same image layer, preserving the installed chemistry environment.
      Exclude local environments and outputs from repo2docker's build context.
      Local image size and chemistry imports have been checked; public launch
      validation remains below.
- [x] Pin the teaching launch to a fixed commit, independent of website-only
      changes to `main`. Update `binder/launch.json` when publishing app or
      environment changes. Warm the link before a course; live validation of the
      current pinned commit is pending its publication.
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
- [ ] Verify representative chemistry calculations, cancellation, exports and
      session isolation on Binder. Record memory use and runtimes, especially
      for transition-structure searches, before claiming support for every
      exercise.
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
The build fix is committed as `41b5346`; publication and public launch measurements
are pending SSH authentication. The public API's `launching` stage combines image
pull and server startup, so it cannot isolate those two timings on its own.

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
