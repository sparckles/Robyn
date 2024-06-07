<p align="center"><img alt="Robyn Logo" src="https://user-images.githubusercontent.com/29942790/140995889-5d91dcff-3aa7-4cfb-8a90-2cddf1337dca.png" width="250" /><p>

# Robyn

[![Twitter](https://badgen.net/badge/icon/twitter?icon=twitter&label)](https://twitter.com/Robyn_oss)
[![Downloads](https://static.pepy.tech/personalized-badge/Robyn?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads)](https://pepy.tech/project/Robyn)
[![GitHub tag](https://img.shields.io/github/tag/sparckles/Robyn?include_prereleases=&sort=semver&color=black)](https://github.com/sparckles/Robyn/releases/)
[![License](https://img.shields.io/badge/License-BSD_2.0-black)](#license)
![Python](https://img.shields.io/badge/Support-Version%20%E2%89%A5%203.8-brightgreen)

[![view - Documentation](https://img.shields.io/badge/view-Documentation-blue?style=for-the-badge)](https://robyn.tech/documentation)
[![Discord](https://img.shields.io/discord/999782964143603713?label=discord&logo=discord&logoColor=white&style=for-the-badge&color=blue)](https://discord.gg/rkERZ5eNU8)

Robyn is a High-Performance, Community-Driven, and Innovator Friendly Web Framework with a Rust runtime. You can learn more by checking our [community resources](https://robyn.tech/documentation/community-resources)!

<img width="652" alt="image" src="https://github.com/sparckles/Robyn/assets/29942790/4a2bba61-24e7-4ee2-8884-19b40204bfcd">


Source: [TechEmpower Round 22](https://www.techempower.com/benchmarks/#section=data-r22&test=plaintext)

## 📦 Installation

You can simply use Pip for installation.

```
pip install robyn
```

Or, with [conda-forge](https://conda-forge.org/)

```
conda install -c conda-forge robyn
```

## 🤔 Usage

### 🚀 Define your API

To define your API, you can add the following code in an `app.py` file.

```python
from robyn import Robyn

app = Robyn(__file__)

@app.get("/")
async def h(request):
    return "Hello, world!"

app.start(port=8080)
```

### 🏃 Run your code

Simply run the app.py file you created. You will then have access to a server on the `localhost:8080`, that you can request from an other program. Robyn provides several options to customize your web server.

```
$ python3 app.py
```

To see the usage

```
usage: app.py [-h] [--processes PROCESSES] [--workers WORKERS] [--dev] [--log-level LOG_LEVEL]

Robyn, a fast async web framework with a rust runtime.

options:
  -h, --help                show this help message and exit
  --processes PROCESSES     Choose the number of processes. [Default: 1]
  --workers WORKERS         Choose the number of workers. [Default: 1]
  --dev                     Development mode. It restarts the server based on file changes.
  --log-level LOG_LEVEL     Set the log level name
  --create                  Create a new project template.
  --docs                    Open the Robyn documentation.
  --open-browser            Open the browser on successful start.
```

Log level can be `DEBUG`, `INFO`, `WARNING`, or `ERROR`.

When running the app using `--open-browser` a new browser window will open at the app location, e.g:

```
$ python3 app.py --open-browser
```

### 💻 Add more routes

You can add more routes to your API. Check out the routes in [this file](https://github.com/sparckles/Robyn/blob/main/integration_tests/base_routes.py) as examples.

## 🐍 Python Version Support

Robyn is compatible with the following Python versions:

> Python >= 3.8

It is recommended to use the latest version of Python for the best performances.

Please make sure you have the correct version of Python installed before starting to use
this project. You can check your Python version by running the following command in your
terminal:

```bash
python --version
```

## 💡 Features

- Under active development!
- Written in Rust, btw xD
- A multithreaded Runtime
- Extensible
- A simple API
- Sync and Async Function Support
- Dynamic URL Routing
- Multi Core Scaling
- WebSockets!
- Middlewares
- Built in form data handling
- Dependency Injection
- Hot Reloading
- Direct Rust Integration
- Community First and truly FOSS!

## 🗒️ How to contribute

### 🏁 Get started

Please read the [code of conduct](https://github.com/sparckles/Robyn/blob/main/CODE_OF_CONDUCT.md) and go through [CONTRIBUTING.md](https://github.com/sparckles/Robyn/blob/main/CONTRIBUTING.md) before contributing to Robyn.
Feel free to open an issue for any clarifications or suggestions.

If you're feeling curious. You can take a look at a more detailed architecture [here](https://robyn.tech/documentation/architecture).

If you still need help to get started, feel free to reach out on our [community discord](https://discord.gg/rkERZ5eNU8).

### ⚙️ To Develop Locally

- Setup a virtual environment:
```
python3 -m venv .venv
source .venv/bin/activate
```
- Install required packages

```
pip install pre-commit poetry maturin
```
- Install development dependencies
```
poetry install --with dev --with test
```
- Install pre-commit git hooks
```
pre-commit install
```
- Build & install Robyn Rust package
```
maturin develop
```
- Build & install Robyn Rust package (**experimental**)
```
maturin develop --cargo-extra-args="--features=io-uring"
```
- Run!
```
poetry run test_server
```
- Run tests
```
pytest integration_tests
```
- Test (refer to `integration_tests/base_routes.py` for more endpoints)
```
curl http://localhost:8080/sync/str
```

- **tip:** One liners for testing changes!
```
maturin develop && poetry run test_server
maturin develop && pytest integration_tests
```

- Potential errors
  - install `patchelf` with `pip install patchelf` if you face `patchelf` not found issue during `maturin develop` (esp. on Arch Linux)

## ✨ Special thanks

### ✨ Contributors/Supporters

Thanks to all the contributors of the project. Robyn will not be what it is without all your support :heart:.

<a href="https://github.com/sparckles/Robyn/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=sparckles/Robyn" />
</a>

Special thanks to the [PyO3](https://pyo3.rs/v0.13.2/) community and [Andrew from PyO3-asyncio](https://github.com/awestlake87/pyo3-asyncio) for their amazing libraries and their support for my queries. 💖

### ✨ Sponsors

These sponsors help us make the magic happen!

[![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%201.svg)](https://www.digitalocean.com/?refcode=3f2b9fd4968d&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)
[![Appwrite Logo](https://avatars.githubusercontent.com/u/25003669?s=105&v=1)](https://github.com/appwrite)

- [Shivay Lamba](https://github.com/shivaylamba)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=sparckles/Robyn&type=Date)](https://star-history.com/#sparckles/Robyn&Date)
