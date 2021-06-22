# Robyn

[![Gitter](https://badges.gitter.im/robyn_/community.svg)](https://gitter.im/robyn_/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

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

app = Robyn()

@app.get("/")
async def h():
    return "Hello, world!"

app.start()

```

## Contributor Guidelines

Feel free to open an issue for any clarification or for any suggestions.

If you're feeling curious. You can take a look at a more detailed architecture [here](https://github.com/sansyrox/robyn/blob/main/docs/architecture.md).

## To Run Locally

1. Add more routes in the test.py file(if you like). It only supports only get requests at the moment

2. Run `maturin develop`

3. Run `python3 test.py`

4. To measure the performance: `./server_test.sh`

## Contributors/Supporters

Special thanks to the [ PyO3 ](https://pyo3.rs/v0.13.2/) community and [ Andrew from PyO3-asyncio ](awestlake87/pyo3-asyncio) for their amazing libraries and their support for my queries. 💖
