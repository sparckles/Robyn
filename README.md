
<img alt="Robyn Logo" src="https://user-images.githubusercontent.com/29942790/140995889-5d91dcff-3aa7-4cfb-8a90-2cddf1337dca.png" width="250" />

# Robyn

[![Gitter](https://badges.gitter.im/robyn_/community.svg)](https://gitter.im/robyn_/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![Downloads](https://static.pepy.tech/personalized-badge/robyn?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads)](https://pepy.tech/project/robyn)


[Docs](https://sansyrox.github.io/robyn/#/)

Robyn is an async Python backend server with a runtime written in Rust, btw.

Python server running on top of of Rust Async RunTime.

## Installation

You can simply use Pip for installation.

```
pip install robyn
```

## Usage

```python

from robyn import Robyn

app = Robyn(__file__)

@app.get("/")
async def h():
    return "Hello, world!"

app.start(port=5000)

```

## Features
- Under active development!
- Written in Rust, btw xD
- A multithreaded Runtime
- Extensible
- A simple API
- Sync and Async Function Support
- Dynamic URL Routing
- Multi Core Scaling
- WebSockets!
- Hot Reloading (Still experimental)
- Community First and truly FOSS!


## Contributor Guidelines

Feel free to open an issue for any clarification or for any suggestions.

If you're feeling curious. You can take a look at a more detailed architecture [here](https://github.com/sansyrox/robyn/blob/main/docs/architecture.md).

## To Run Locally

1. Add more routes in the `integration_tests/base_routes.py` file(if you like). It only supports only get requests at the moment

2. Run `maturin develop`

3. Run `python3 integration_tests/base_routes.py`

## To Run

```
python3 app.py -h

usage: base_routes.py [-h] [--processes PROCESSES] [--workers WORKERS] [--dev DEV]

Robyn, a fast async web framework with a rust runtime.

optional arguments:
  -h, --help            show this help message and exit
  --processes PROCESSES : allows you to choose the number of parallel processes
  --workers WORKERS : allows you to choose the number of workers
  --dev DEV : this flag gives the option to enable hot reloading or not
```


## Contributors/Supporters

To contribute to Robyn, make sure to first go through the [CONTRIBUTING.md](./CONTRIBUTING.md).

Thanks to all the contributors of the project. Robyn will not be what it is without all your support :heart:.

Special thanks to the [ PyO3 ](https://pyo3.rs/v0.13.2/) community and [ Andrew from PyO3-asyncio ](awestlake87/pyo3-asyncio) for their amazing libraries and their support for my queries. 💖
