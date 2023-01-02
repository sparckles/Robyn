FROM python:3.10-slim

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ca-certificates gcc libc6-dev \
        procps iproute2 iputils-ping vim curl net-tools wget sqlite3; \
    \
    url="https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init"; \
    wget "$url"; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --default-toolchain beta --default-host x86_64-unknown-linux-gnu; \
    rm rustup-init; \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME; \
    rustup --version; \
    cargo --version; \
    rustc --version; \
    curl -o /tmp/requirements.txt https://gist.githubusercontent.com/shaohaiyang/2960abbdc947ebbc6abdd7a77fcfb161/raw/156204c6dfd286ae9659e9e4d7c652284c1455c0/docker-requirements.txt; \
    curl -o /tmp/app.py https://gist.githubusercontent.com/shaohaiyang/2960abbdc947ebbc6abdd7a77fcfb161/raw/0ab0d0aad135055bbcdbad5d84e960bffee24dca/robyn-app.py; \
    pip install -r /tmp/requirements.txt; \
    apt-get clean && rm -rf /var/lib/apt/lists/*;

ENTRYPOINT ["python3"]
CMD ["/tmp/app.py"]
