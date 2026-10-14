# TODO

## Binder startup performance and launch experience

Follow up after the initial Binder exploration (2026-10-14). The user confirmed
that the public Binder session launches and the application works. This confirms
a live launch, but does not establish that all chemistry workflows fit Binder's
resource limits.

The current configuration installs the locked Pixi `web` environment during
image construction and opens PhotoSwitchLab directly through Jupyter Server Proxy via
`?urlpath=photoswitchlab%2F`. JupyterLab also has a launcher entry for the app. No custom
loading page has been added.

- [ ] Measure image size and timings for a first build and subsequent launches
      of the same commit. Separate build, registry upload, image pull, session
      startup and application startup times.
- [ ] Inspect build caches and downloaded archives retained in the image. Remove
      unnecessary artifacts during the same build step that creates them,
      preserving the installed chemistry environment. Measure the size reduction
      and repeat the live launch check.
- [ ] Use a fixed commit or release link for teaching and launch it before a
      session to populate caches. Avoid rebuilding because of unrelated changes
      to the moving branch.
- [ ] Evaluate image prebuilding in CI if first-launch delays remain excessive.
      Check current Binder support and registry requirements before choosing an
      approach.
- [ ] Consider separating the environment from frequently changing content if
      rebuilds become a recurring problem. Assess whether the extra maintenance
      is justified for an application whose code and environment must remain
      compatible.
- [ ] Review the student launch experience. Explore a German loading page or
      launch wrapper with understandable progress stages, an explanation of
      first-build delays, and retry guidance. Check which parts can be customized
      on public Binder and which require a separate page or an owned BinderHub.
      Keep developer details out of the student flow.
- [ ] Verify representative chemistry calculations, cancellation, exports and
      session isolation on Binder. Record memory use and runtimes, especially
      for transition-structure searches, before claiming support for every
      exercise.
- [ ] Update `binder/README.md` to reflect live validation and any performance or
      launch experience changes.

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

### References

- [Binder startup speed guide](https://mybinder.readthedocs.io/en/latest/howto/speed.html)
- [Startup optimization discussion linked by the guide](https://discourse.jupyter.org/t/how-to-reduce-mybinder-org-repository-startup-time/4956)
- [Binder interface configuration](https://mybinder.readthedocs.io/en/latest/howto/user_interface.html)
- [Binder startup stages and resource limits](https://mybinder.readthedocs.io/en/latest/about/user-guidelines.html)
- [Reported BIDS file-watcher issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/3654)
- [Binder operations guidance for file-watcher limits](https://mybinder-sre.readthedocs.io/en/latest/deployment/k3s.html#increase-some-fs-limits)

## OER content and naming migration

The project name is **PhotoSwitchLab**. The German app and website retain the
title **Molekulare Photoschalter**, subtitle **Computerexperiment**, and optional
local suffix ** · ACh-PR · Marburg**. Public branding is the default; the Marburg
branding can be selected explicitly. The course setting currently selects
branding and the website guide entry point.

- [ ] Separate shared exercises from Marburg's protocol-specific assignments,
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
- [ ] Refresh the local protocol template's printed website URL and branding
      when revising the Marburg materials; its generator already uses the new
      website URL. Render and inspect the DOCX before publishing that update.
