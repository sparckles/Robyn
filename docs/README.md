<img alt="Robyn Logo" src="https://user-images.githubusercontent.com/29942790/140995889-5d91dcff-3aa7-4cfb-8a90-2cddf1337dca.png" width="250" />

# Robyn

[![Twitter](https://badgen.net/badge/icon/twitter?icon=twitter&label)](https://twitter.com/robyn_oss)
[![Gitter](https://badges.gitter.im/robyn_/community.svg)](https://gitter.im/robyn_/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![Downloads](https://static.pepy.tech/personalized-badge/robyn?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads)](https://pepy.tech/project/robyn)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub tag](https://img.shields.io/github/tag/sansyrox/robyn?include_prereleases=&sort=semver&color=black)](https://github.com/sansyrox/robyn/releases/)
[![License](https://img.shields.io/badge/License-BSD_2.0-black)](#license)
[![Discord](https://img.shields.io/discord/999782964143603713?label=discord&logo=discord&logoColor=white&style=for-the-badge&color=blue)](https://discord.gg/qKF5sSnC)

[![view - Documentation](https://img.shields.io/badge/view-Documentation-blue?style=for-the-badge)](https://sansyrox.github.io/robyn/#/)

Robyn is an async Python backend server with a runtime written in Rust, btw.

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

```python
from robyn import Robyn

app = Robyn(__file__)


@app.get("/")
async def h(request):
    return "Hello, world!"

app.start(port=8080)
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
- Hot Reloading
- Community First and truly FOSS!

## 🗒️ Contributor Guidelines

Feel free to open an issue for any clarification or for any suggestions.

If you're feeling curious. You can take a look at a more detailed architecture [here](https://github.com/sansyrox/robyn/blob/main/docs/architecture.md).

## ⚙️ To Develop Locally

1. Install the development dependencies: `pip install -r dev-requirements.txt`

1. Install the pre-commit git hooks: `pre-commit install`

1. Add more routes in the `integration_tests/base_routes.py` file(if you like).

1. Run `maturin develop` or `maturin develop --cargo-extra-args="--features=io-uring"` (if you want to run the experimental version).

1. Run `python3 integration_tests/base_routes.py`

## 🏃 To Run

```
python3 app.py -h

usage: app.py [-h] [--processes PROCESSES] [--workers WORKERS] [--dev DEV]

Robyn, a fast async web framework with a rust runtime.

optional arguments:
  -h, --help            show this help message and exit
  --processes PROCESSES : allows you to choose the number of parallel processes
  --workers WORKERS : allows you to choose the number of workers
  --dev DEV : this flag gives the option to enable hot reloading or not and also sets the default log level to debug
  --log-level LEVEL : this flag allows you to set the log level
```

## ✨ Contributors/Supporters

To contribute to Robyn, make sure to first go through the [CONTRIBUTING.md](./CONTRIBUTING.md).

Thanks to all the contributors of the project. Robyn will not be what it is without all your support :heart:.

<a href="https://github.com/sansyrox/robyn/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=sansyrox/robyn" />
</a>

Special thanks to the [PyO3](https://pyo3.rs/v0.13.2/) community and [Andrew from PyO3-asyncio](https://github.com/awestlake87/pyo3-asyncio) for their amazing libraries and their support for my queries. 💖

## ✨ Sponsors

These sponsors help us make the magic happen!

[![DigitalOcean Referral Badge](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%201.svg)](https://www.digitalocean.com/?refcode=3f2b9fd4968d&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)
[![Appwrite Logo](https://avatars.githubusercontent.com/u/25003669?s=105&v=1)](https://github.com/appwrite)

- [Shivay Lamba](https://github.com/shivaylamba)
