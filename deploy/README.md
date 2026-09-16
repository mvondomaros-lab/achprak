# Integrating with an existing JupyterHub

Run the central JupyterHub in its own administrator-managed environment, separate
from the AChPrak checkout. The Hub owns authentication, accounts, its database and
cookie secret, HTTPS routing, the central HTTP proxy and spawner resource limits.
Updating AChPrak must not replace that environment or the Hub service command.
For a new Hub, follow the [JupyterHub installation guide](https://jupyterhub.readthedocs.io/en/stable/tutorial/quickstart.html)
and establish working login and user spawning before integrating AChPrak.

AChPrak provides two deployment environments:

| Environment | Purpose |
| --- | --- |
| `web` | Application and chemistry dependencies for standalone local use. |
| `web-hub` | Application plus the authenticated standalone application proxy. |

`web-hub` includes `jupyterhub-base`, the Python package required by the standalone
proxy. It does not include `configurable-http-proxy` or a central Hub service.
Do not start the central Hub with `pixi run -e web-hub jupyterhub`.
The standalone proxy starts AChPrak directly, without a notebook interface. It
checks Hub authorization before forwarding requests to a private Unix socket.
The application has no unprotected TCP port that another Unix user can access.

## Install the application

These instructions target x86-64 Linux and an existing local-process or systemd
spawner that launches each user under a separate Unix identity. Accounts need
writable home directories. Container or Kubernetes spawners need the application
installed inside their user image and paths adapted there.

1. Put the checkout at its final location, for example `/opt/achprak`. Keep the
   source and shared environment administrator-owned. Participants need read and
   execute access, but no write access.
2. As the administrator, install the locked integration environment:

   ```sh
   pixi install --manifest-path /opt/achprak/pyproject.toml --locked -e web-hub
   ```

   Do not relocate an installed Pixi environment.
3. Compare the independently installed Hub's version with:

   ```sh
   /opt/achprak/.pixi/envs/web-hub/bin/jupyterhub --version
   ```

   The integration currently pins `jupyterhub-base` to **6.0.1**. Match the central
   Hub and integration package versions as recommended by the
   [JupyterHub upgrade guide](https://jupyterhub.readthedocs.io/en/stable/howto/upgrading.html).
   For another Hub version, adjust that pin and regenerate the lockfile with
   `pixi lock`, then install and verify before switching. Do not upgrade the
   central Hub implicitly as part of an application update.

   When upgrading an existing Hub from 5 to 6, the database schema must also be
   upgraded. Stop the Hub, back up its database, and run `jupyterhub upgrade-db`
   with the actual site configuration in the independent Hub environment before
   restarting. Follow the [JupyterHub 6 migration guide](https://jupyterhub.readthedocs.io/en/stable/howto/upgrading-v6.html).
   Rolling back a schema upgrade requires the matching database backup as well
   as the old Hub environment; retaining the old checkout alone is insufficient.

## Configure the existing Hub

The file `jupyterhub_integration.py` is an application-launch fragment, not a
complete Hub configuration. Review it, then copy it to an administrator-controlled
configuration directory:

```sh
sudo install -m 644 /opt/achprak/deploy/jupyterhub_integration.py /etc/jupyterhub/achprak.py
sudo vim /etc/jupyterhub/jupyterhub_config.py
```

Use your actual Hub configuration path. At the end of that file, after existing
spawner settings, add:

```python
load_subconfig("/etc/jupyterhub/achprak.py")
```

The fragment sets the application command, launch arguments, default URL,
startup timeouts and compute environment variables. Other existing spawner
environment variables are retained; PATH is set to the application environment
followed by standard system directories. It does not change authentication,
allowed groups, administrator accounts, spawner class, resource limits, Hub bind
URL, database, cookie secret or central proxy configuration. Review existing
spawn hooks or profiles that could override the application command.

By default it uses `/opt/achprak/.pixi/envs/web-hub`. For another install location,
set `ACHPRAK_ENV` to the absolute environment path in the **central Hub service's**
environment, or edit the default in your copied fragment. The proxy and Python
paths must point into AChPrak's environment, not the central Hub's environment.
The copy in `/etc` keeps application updates from silently changing the Hub's
launch configuration; review and copy future fragment updates deliberately.

Keep the existing HTTPS reverse proxy. The fragment enables Secure cookies and
requires HTTPS. Application URLs and cookies follow the Hub's full user prefix,
including a Hub prefix such as `/jhub/`: `/jhub/user/<username>/` works without
changing application URLs. Each user's process also separates browser sessions.

During a maintenance window, stop existing user servers through the Hub and
restart the central Hub using its existing service. This changes the default
user launch from notebooks to AChPrak. Test login with two accounts, structure
generation, minimum optimization, spectra, cancellation and downloads. Confirm
that the accounts see separate results. Local proxy verification below checks
paths and sockets only; it does not replace authenticated Linux deployment tests.

## Migrating from the old AChPrak installation

Older installations may run the central Hub through a symlink into
`achprak/.pixi/envs/lserver`. Keep that checkout and environment intact until the
migration is complete. The new project no longer defines `lserver`.

First install the central Hub independently, initially at the existing Hub
version. Preserve the site configuration, database, cookie secret, authentication
and spawner dependencies. Back up the database and configuration before changing
the service. Switch the Hub runtime and verify the existing login and notebook
launch before installing this integration. Never run two Hubs against the same
database at once.

Then install AChPrak in a separate checkout and apply the launch fragment above.
Keep the old launch configuration and environment for rollback. If the new app
fails, stop its user servers, restore the old launch configuration and restart
the Hub. Once the integration works, the central Hub and new application no
longer need the old checkout; inspect remaining references before removing it.

## Capacity and lifecycle

Each user gets one concurrent calculation by default (`--max-jobs=1` in the
configuration), a 600-second wall-clock limit per calculation, and one native
compute thread. Additional browser sessions queue within the instance. Set class
size and per-user limits according to available memory; MOPAC calculations can
use considerably more memory than geometry generation. LocalProcessSpawner
provides UID isolation, not cgroup memory/CPU limits.
An existing SystemdSpawner can retain its resource limits; size them for the
chemistry workloads. The integration does not select or replace your spawner.

Cancellation and timeouts kill the calculation's process group, including its
MOPAC subprocess. Results survive a page reload in the same browser session, but
are held in memory and are cleared after 24 hours without activity or when the
instance stops. Students should download the results needed for their lab reports.
The app retains up to 100 structures and the last 12 calculation logs per session.
Temporary calculation directories are removed on session expiry and clean shutdown.

Start multiple local instances manually with different ports:

```sh
pixi run -e web web --port 8000
pixi run -e web web --port 8001
```

Ports do not implement authentication. The local mode is for development on a
trusted machine; use authenticated Hub integration on the shared server.

## Local proxy verification

The standalone proxy can be tested without PAM or root, on loopback only:

```sh
pixi run -e web-hub jupyter-standaloneproxy \
  --no-authentication --address=127.0.0.1 --port=8001 \
  --base-url=/jhub/user/test/ --unix-socket=True --timeout=60 -- \
  python -m achprak.web --unix-socket='{unix_socket}' \
  --cookie-path='{base_url}' --max-jobs=1
```

Open `http://127.0.0.1:8001/jhub/user/test/`. This checks URL prefixes, private sockets,
assets and cookies. It does **not** test PAM login or UID switching. Never use
`--no-authentication` on an externally accessible server.

References:

- [JupyterHub PAM authentication](https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html)
- [Standalone app proxy](https://jupyter-server-proxy.readthedocs.io/en/latest/standalone.html)
- [Private Unix sockets](https://jupyter-server-proxy.readthedocs.io/en/latest/server-process.html)
