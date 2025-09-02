# Minimal, reproducible Binder build using pixi
FROM debian:stable-slim

# System basics
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates git python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:${PATH}"

# Copy repo and install deps via pixi
WORKDIR /repo
COPY . .
RUN pixi install

# Jupyter comes from your pixi project; if not, ensure it's in your pixi deps
EXPOSE 8888
CMD ["python3","-m","notebook","--ip=0.0.0.0","--no-browser","--NotebookApp.token="]

