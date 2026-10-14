# Deploying with JupyterHub

Run one PhotoSwitchLab instance per user on an existing JupyterHub.

## Requirements

- A working JupyterHub with authentication and user spawning.
- x86-64 Linux, separate Unix accounts and writable home directories with
  LocalProcessSpawner or SystemdSpawner. For container spawners, install the app
  in the user image and adapt the paths.
- HTTPS, with the reverse proxy forwarding Host and X-Forwarded-Proto headers
  and supporting WebSocket upgrades.
- Pixi and a Hub compatible with the pinned `jupyterhub-base` **6.0.1**.
  See the [JupyterHub upgrade guide](https://jupyterhub.readthedocs.io/en/stable/howto/upgrading.html).

## Install

Place the checkout at its final location, for example `/opt/photoswitchlab`.
Keep the source and environment administrator-owned; participants need read and
execute access. Install the locked integration environment:

```sh
pixi install --manifest-path /opt/photoswitchlab/pyproject.toml --locked -e web-hub
```

Do not move an installed Pixi environment. The `web-hub` environment contains the
app and standalone proxy; the central Hub stays in its own environment.

## Configure

Copy the [integration fragment](jupyterhub_integration.py) to the Hub's
configuration directory:

```sh
sudo install -m 644 /opt/photoswitchlab/deploy/jupyterhub_integration.py /etc/jupyterhub/photoswitchlab.py
```

Load it at the end of `jupyterhub_config.py`, after existing spawner settings:

```python
load_subconfig("/etc/jupyterhub/photoswitchlab.py")
```

Adapt the paths to your server. The following settings belong in the **central
Hub service's environment**:

| Setting | Purpose |
| --- | --- |
| `PHOTOSWITCHLAB_ENV` | Absolute app environment path; defaults to `/opt/photoswitchlab/.pixi/envs/web-hub`. |
| `PHOTOSWITCHLAB_COURSE=marburg` | Selects the Marburg branding and course guide. Omit for public branding. |

The fragment launches the app through an authenticated proxy and private Unix
socket. Keep authentication, account permissions and resource controls in your
Hub configuration; check spawn hooks that override the app command.

The course setting adds Marburg's protocol download, required deliverables and
submission instructions to the shared exercises.

## Start and verify

Stop existing user servers and restart the Hub through your service manager.
Check the deployment through its HTTPS endpoint:

- Log in with two accounts and confirm that their results are separate.
- Generate a structure, optimize a minimum structure and calculate a spectrum.
- Check cancellation, page reloads, downloads and logout.

Each instance allows one calculation at a time, with a 600-second job timeout
and one numerical compute thread. Configure CPU and memory limits through your
spawner. Results are temporary: they are cleared when the instance stops or
after 24 hours of inactivity. Export results before stopping a server.

For updates, reinstall the locked environment, review and recopy the integration
fragment, then restart user servers and repeat the checks.

## Local proxy check

To test URL prefixes, sockets, assets and cookies before connecting to the Hub:

```sh
pixi run --locked -e web-hub jupyter-standaloneproxy \
  --no-authentication --address=127.0.0.1 --port=8001 \
  --base-url=/user/test/ --unix-socket=True --timeout=60 -- \
  python -m photoswitchlab.web --unix-socket='{unix_socket}' \
  --cookie-path='{base_url}' --max-jobs=1
```

Open `http://127.0.0.1:8001/user/test/`. This loopback check does not test Hub
authentication or separate user accounts. Keep `--no-authentication` restricted
to loopback.
