import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="AChPrak web application")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--unix-socket", help="Bind to a private Unix socket instead of TCP"
    )
    parser.add_argument("--max-jobs", type=int, default=2)
    parser.add_argument("--job-timeout", type=int, default=600)
    parser.add_argument(
        "--cookie-path", default=os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/")
    )
    parser.add_argument("--secure-cookie", action="store_true")
    args = parser.parse_args()
    if args.max_jobs < 1 or args.job_timeout < 1:
        parser.error("--max-jobs and --job-timeout must be positive")
    os.environ["MPLBACKEND"] = "Agg"
    import uvicorn
    from .server import create_app

    app = create_app(
        args.max_jobs, args.job_timeout, args.cookie_path, args.secure_cookie
    )
    uvicorn.run(
        app, host=args.host, port=args.port, uds=args.unix_socket, proxy_headers=False
    )


if __name__ == "__main__":
    main()
