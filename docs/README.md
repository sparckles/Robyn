# Robyn

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

## Contributor Guidelines

Feel free to open an issue for any clarification or for any suggestions.

To read about the detailed architecture, you can read [here](https://sansyrox.github.io/robyn/#/architecture).

## Testing on Python

1. Activate a virtual environment
2. Install maturin: `pip3 install maturin`
3. Create a Debug build: `maturin develop`
4. Test it out: `python3`
5. `import robyn`
6. `dir(robyn)`

## To Run

### Without hot reloading
`python3 app.py`

### With hot reloading(still beta)
`python3 app.py --dev=true`


## Contributors/Supporters

Special thanks to the [ PyO3 ](https://pyo3.rs/v0.13.2/) community and [ Andrew from PyO3-asyncio ](awestlake87/pyo3-asyncio) for their amazing libraries and their support for my queries. 💖
