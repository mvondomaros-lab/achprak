# Self-hosting with Unix accounts

The app runs locally without a login. On the shared Linux server, JupyterHub
provides PAM authentication and starts a separate process under each user's UID.
The standalone proxy starts the web app directly: there is no notebook or
JupyterLab interface. It authenticates requests before forwarding them to a
private Unix socket. Other Unix users cannot bypass login by connecting to an
unprotected app TCP port.

## Installation

1. Put this checkout in a shared, administrator-owned directory such as
   `/opt/achprak`. All participants need read and execute access; they should not
   have write access to the source or shared environment.
2. Install Pixi and run `pixi install -e web-hub` in that directory. The environment
   includes Python, MOPAC, tblite, RDKit, Sella, JupyterHub, its HTTP proxy and the
   standalone application proxy. Do not relocate an installed Pixi environment;
   install it at its final path.
3. Create the participant Unix accounts and add them to the Unix group `achprak`.
   Accounts must have a home directory and be allowed by the server's PAM policy.
   To use a different group, set `ACHPRAK_UNIX_GROUP` when starting the Hub.
4. Run JupyterHub as root (LocalProcessSpawner needs permission to switch UID):

   ```sh
   cd /opt/achprak
   sudo /absolute/path/to/pixi run -e web-hub jupyterhub -f deploy/jupyterhub_config.py
   ```

   For a managed service, set its working directory to `/opt/achprak`, preserve
   the participant group setting, and use the absolute Pixi path in `ExecStart`.
   Keep JupyterHub's database and cookie secret in an administrator-only directory
   by setting `c.JupyterHub.db_url` and `c.JupyterHub.cookie_secret_file` in your
   site configuration.
5. Put an HTTPS reverse proxy in front of `127.0.0.1:8000`, forwarding the Host and
   X-Forwarded-Proto headers and supporting WebSocket upgrades. Only the HTTPS
   endpoint should be externally accessible. The bundled configuration enables
   Secure cookies; use HTTPS for this deployment.

JupyterHub routes each participant to `/user/<username>/`. All application asset
and API URLs are relative, and cookies are scoped to this prefix. The proxy's
private socket prevents cross-user direct access. The app keeps separate browser
sessions inside each process as well.

## Capacity and lifecycle

Each user gets one concurrent calculation by default (`--max-jobs=1` in the
configuration), a 600-second wall-clock limit per calculation, and one native
compute thread. Additional browser sessions queue within the instance. Set class
size and per-user limits according to available memory; MOPAC calculations can
use considerably more memory than geometry generation. The included
LocalProcessSpawner configuration provides UID isolation, not cgroup memory/CPU
limits; use a systemd spawner or service-level resource controls if those are
needed for the classroom server.

Cancellation and timeouts kill the calculation's process group, including its
MOPAC subprocess. Results survive a page reload in the same browser session, but
are held in memory and are cleared after 24 hours without activity or when the
instance stops. Students should download the results needed for their protocol.
The app retains up to 100 structures and the last 12 calculation logs per session.
Temporary calculation directories are removed on session expiry and clean shutdown.

Start multiple local instances manually with different ports:

```sh
pixi run -e web web --port 8000
pixi run -e web web --port 8001
```

Ports do not implement authentication. The local mode is for development on a
trusted machine; use the Hub configuration on the shared server.

## Local proxy verification

The standalone proxy can be tested without PAM or root, on loopback only:

```sh
pixi run -e web-hub jupyter-standaloneproxy \
  --no-authentication --address=127.0.0.1 --port=8001 \
  --base-url=/user/test/ --unix-socket=True --timeout=60 -- \
  python -m achprak.web --unix-socket='{unix_socket}' \
  --cookie-path='{base_url}' --max-jobs=1
```

Open `http://127.0.0.1:8001/user/test/`. This checks URL prefixes, private sockets,
assets and cookies. It does **not** test PAM login or UID switching. Never use
`--no-authentication` on an externally accessible server.

References:
- [JupyterHub PAM authentication](https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html)
- [Standalone app proxy](https://jupyter-server-proxy.readthedocs.io/en/latest/standalone.html)
- [Private Unix sockets](https://jupyter-server-proxy.readthedocs.io/en/latest/server-process.html)
