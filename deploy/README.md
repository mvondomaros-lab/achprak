# Deploying with JupyterHub

Run the central JupyterHub in its own administrator-managed environment, separate
from the AChPrak checkout. The Hub owns authentication, accounts, its database and
cookie secret, HTTPS routing, the central HTTP proxy and spawner resource limits.
For a new Hub, follow the [JupyterHub installation
guide](https://jupyterhub.readthedocs.io/en/stable/tutorial/quickstart.html) and
establish working login and user spawning before integrating AChPrak.

AChPrak provides two deployment environments:

| Environment | Purpose |
| --- | --- |
| `web` | Application and chemistry dependencies for standalone local use. |
| `web-hub` | Application plus the authenticated standalone application proxy. |

`web-hub` includes `jupyterhub-base`, the Python package required by the
standalone proxy. It does not include `configurable-http-proxy` or a central Hub
service. A **proxy** forwards browser requests to another process. The central
proxy routes requests to each user's server; the standalone application proxy
launches and forwards requests to AChPrak. It checks Hub authorization before
forwarding requests to a private Unix socket. A **Unix socket** is a local
communication endpoint represented by a filesystem path. Its private directory
limits access to the owning user. In this setup, AChPrak does not expose an
unauthenticated network port.

## Requirements

A Hub **spawner** starts and stops a user's application process. These
instructions target x86-64 Linux and a LocalProcessSpawner or SystemdSpawner that
launches each user under a separate Unix account. Accounts need writable home
directories. Container or Kubernetes spawners need the application installed
inside their user image and paths adapted there.

Use HTTPS for the public Hub endpoint and a Pixi version that supports the
repository's lockfile. The paths `/opt/achprak` and `/etc/jupyterhub` below are
examples; adapt them to your installation.

## Install the application

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
Hub and integration package versions as recommended by the [JupyterHub upgrade
guide](https://jupyterhub.readthedocs.io/en/stable/howto/upgrading.html). For
another Hub version, adjust that pin and regenerate the lockfile with `pixi lock`,
then install and verify before switching. Do not upgrade the central Hub
implicitly as part of an application update.

## Configure the Hub

The [integration fragment](jupyterhub_integration.py) configures the per-user
application launch. Copy it to an administrator-controlled configuration directory
and load it from your Hub configuration:

```sh
sudo install -m 644 /opt/achprak/deploy/jupyterhub_integration.py /etc/jupyterhub/achprak.py
sudo vim /etc/jupyterhub/jupyterhub_config.py
```

Use your actual Hub configuration path. At the end of that file, after existing
spawner settings, add:

```python
load_subconfig("/etc/jupyterhub/achprak.py")
```

The fragment sets the application command, launch arguments, default URL, startup
timeouts and environment variables (settings inherited by each process). Other
existing spawner environment variables are retained; PATH is set to the
application environment followed by standard system directories. Authentication,
user permissions, spawner selection, resource limits and central Hub settings
remain controlled by your site configuration. Check any spawn hooks or profiles
that also set the application command.

The fragment sets `PYTHONNOUSERSITE=1` for the proxy, application and its workers.
This prevents packages in a participant's personal Python site directory (such as
`~/.local/lib/python3.12/site-packages`) from overriding the locked environment.

By default it uses `/opt/achprak/.pixi/envs/web-hub`. For another install
location, set `ACHPRAK_ENV` to the absolute environment path in the **central Hub
service's** environment, or edit the default in your copied fragment. The proxy
and Python paths must point into AChPrak's environment. Review and copy fragment
updates explicitly when updating the application.

The fragment enables Secure cookies. Configure your HTTPS reverse proxy to forward
the Host and X-Forwarded-Proto headers and support WebSocket upgrades. Application
URLs and cookies follow the Hub's full user prefix, including any configured Hub
base URL. Each user's process also separates browser sessions.

## Start and verify

During a maintenance window, stop running user servers through the Hub and restart
the Hub using your service manager. New user servers will launch AChPrak.

Verify the deployment through its public HTTPS endpoint:

- Log in with two different accounts and start both application instances.
- Generate structures, optimize a minimum and calculate a spectrum.
- Check cancellation, page reloads and result downloads.
- Confirm that the accounts see separate results.

The local proxy check below verifies paths and sockets only; it does not replace
these authenticated deployment checks.

## Capacity and lifecycle

Each user gets one concurrent calculation by default (`--max-jobs=1` in the
configuration), a 600-second wall-clock limit per calculation, and one native
compute thread. Additional browser sessions queue within the instance. Set class
size and per-user limits according to available memory; MOPAC calculations can use
considerably more memory than geometry generation. LocalProcessSpawner runs
processes under separate Unix user IDs (UIDs), but does not enforce memory or
processor (CPU) limits. Use your spawner's resource controls, such as
SystemdSpawner limits, when you need enforced CPU and memory limits.

Cancellation and timeouts kill the calculation's process group, including its
MOPAC subprocess. Results survive a page reload in the same browser session, but
are held in memory and are cleared after 24 hours without activity or when the
instance stops. Students should download the results needed for their lab reports.
The app retains up to 100 structures and the last 12 calculation records per
session, with the last 24,000 bytes of each log held in memory. Worker scratch
files (including MOPAC output and Python temporary files) stay inside the private
job directory. The server removes that directory after completion, failure,
cancellation or timeout; session expiry and clean shutdown also remove pending
jobs. MOPAC files are additionally removed immediately after spectrum parsing,
including when parsing or calculation fails.

An uncatchable server termination (SIGKILL, a host crash or power loss) cannot run
cleanup and may leave an `achprak-web-*` directory in the system temporary
directory. Use the host's temporary-directory cleanup policy for those remnants;
do not remove directories belonging to a running instance. Older versions may also
have left `/tmp/pymopac_*` directories outside the app's job directories.

## Local proxy verification

From the application checkout, test the standalone proxy on loopback without Hub
authentication or root privileges:

```sh
pixi run -e web-hub jupyter-standaloneproxy \
  --no-authentication --address=127.0.0.1 --port=8001 \
  --base-url=/user/test/ --unix-socket=True --timeout=60 -- \
  python -m achprak.web --unix-socket='{unix_socket}' \
  --cookie-path='{base_url}' --max-jobs=1
```

Open `http://127.0.0.1:8001/user/test/`. This checks URL prefixes, private
sockets, assets and cookies. It does **not** test Hub authentication or starting
processes as different Unix users. Never use `--no-authentication` on an
externally accessible server.

References:

- [JupyterHub authentication](https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html)
- [Standalone app proxy](https://jupyter-server-proxy.readthedocs.io/en/latest/standalone.html)
- [Private Unix sockets](https://jupyter-server-proxy.readthedocs.io/en/latest/server-process.html)
