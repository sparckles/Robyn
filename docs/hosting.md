## Hosting

The process of hosting a Robyn app on various cloud providers.


### Railway

We will be deploying the app on [Railway](https://railway.app/).

A GitHub account is needed as a mandatory pre-requisite.

We will be deploying a sample "Hello World", which will be demonstrating a simple `GET` route and serving an HTML file.

Directory structure:

```
app folder/
  main.py
  requirements.txt
  index.html

```

This is a template of the Robyn app we will be deploy.

We have to write the code in `main.py` instead `app.py`. If there is no `main.py` file the building process will fail. But that is a thing with Railway, you have to have a main.py to start any app.

main.py

```python
from robyn import Robyn, static_file


app = Robyn(__file__)


@app.get("/hello")
async def h(request):
    print(request)
    return "Hello, world!"

@app.get("/")
async def get_page(request):
    return static_file("./index.html")


app.start(url="0.0.0.0", port=PORT)    

```


index.html

```html
<h1> Hello World, this is Robyn framework! <h1>

```

### Exposing Ports
The Railway documentation says the following about exposion an app:

> The easiest way to get up and running is to have your application listen on 0.0.0.0:$PORT, where PORT is a Railway-provided environment variable. 

So, is necessary to pass `url` as `0.0.0.0` to `app.start()` as argument. 

To deploy this app on Railway, we need to create a Railway account. We can do so by going on the [Railway HomePage](https://railway.app/).

Press the "Login" button and select "login with a GitHub account."

![image](https://user-images.githubusercontent.com/70811425/202867604-10a09f87-ecb9-4a42-ae90-1359223049bc.png)

Then, we press the "New Project" button and select "Deploy from GitHub repo".

![image](https://user-images.githubusercontent.com/70811425/202870632-4d3f46dc-1aa9-4603-9b0f-344ed87ec9d0.png)

And we select the repo we want to deploy. And click "Deploy Now".
![image](https://user-images.githubusercontent.com/70811425/202870837-16884fef-8900-4ab3-9794-0fb53c3ffd2e.png)

![image](https://user-images.githubusercontent.com/70811425/202871003-f79a1cef-9a5f-4166-be4f-527c60ec6c79.png)

Now, we click on our project's card.

Select "Variables" and press the "New Variable" button to set the environments variables.

![image](https://user-images.githubusercontent.com/70811425/202870681-5c069475-a5d1-4069-8582-c5b549d27aad.png)

Then, we go to the "Settings" tab and click on "Generate Domain."

We can generate a temporary domain under the "Domains" tab.

![image](https://user-images.githubusercontent.com/70811425/202870735-6b955752-c5a6-48d5-acbc-1a4ea6fd7574.png)


We can go to our domain `<domain>/hello` and confirm that the message "Hello World" is displayed.
