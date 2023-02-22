## Getting Started.

We will go through the process of creating a "Hello, World!" app.

### Step 1: Creating a virtualenv

To ensure that there are isolated dependencies, we will use virtual environments.

```
python3 -m venv venv
```

### Step 2: Activate the virtualenv and install Robyn

#### Activating the virtualenv

```
source venv/bin/activate
```

#### Installing Robyn

```
pip install robyn
```

### Step 3: Creating the App.

- Create a file called `app.py`.

- In your favorite editor, open `app.py` and write the following.

```python
from robyn import Robyn

app = Robyn(__file__)


@app.get("/")
async def h(request):  # request is an optional parameter
    return "Hello, world!"

app.start(port=8080, url="0.0.0.0") # url is optional, defaults to 127.0.0.1
```

Let us try to decipher the usage line by line.

> `from robyn import Robyn`

This statement just imports the Robyn structure from the robyn package.

> `app = Robyn(__file__)`

Here, we are creating the app object. We require the `__file__` object to mount the directory for hot reloading.

### Step 4. Running the service

You can just use the command

```
python3 app.py
```

if you want to run the production version, and

```
python3 app.py --dev=true
```

if you want to enable hot reloading or the development version.
