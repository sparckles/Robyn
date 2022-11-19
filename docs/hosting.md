## Hosting

The process of hosting a Robyn app on various cloud providers.


### Railway

To deploy an app on Railway is necessary to have a Github account, because the apps are deploying from a Github repository. 

The repository we will be deploy is a simple app that display a "Hello World" message and serve a HTML file.

Directory structure:

```
app folder/
  main.py
  requirements.txt
  index.html

```

Prerequisites:

- Github Account

This is a template of the Robyn app we will be deploy.

main.py
```
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

```
<h1> Hello World, this is Robyn framework! <h1>

```


The Railway documentation says the following about exposion an app:

> The easiest way to get up and running is to have your application listen on 0.0.0.0:$PORT, where PORT is a Railway-provided environment variable. 

So, is necessary to pass `url` as `0.0.0.0` to `app.start()` as argument. 

Too deploy this app on Railway, we need to go to the [Railway page](https://railway.app/) and create an account.

Press the "Login" button and select to login with a Github account.

![image](https://user-images.githubusercontent.com/70811425/202867604-10a09f87-ecb9-4a42-ae90-1359223049bc.png)

Then, we press the "New Project" button and select "Deploy from GitHub repo".

![image](https://user-images.githubusercontent.com/70811425/202867653-7477cb10-2b2c-47ae-986a-b584f463cd13.png)


And we select the repo to deploy.

Now, we click on our project's card.

Select "Variables" and press the "New Variable" button to set the environments variables.

![image](https://user-images.githubusercontent.com/70811425/202869462-8cb9c052-4083-4696-9bb3-9fe7a7637c35.png)

Then, we go to Setting and click on "Generate Domain".

We would see the domain generate bellow "Domains".

![image](https://user-images.githubusercontent.com/70811425/202869664-31687da8-0194-45f0-a460-470c41ea2ef6.png)


We can go to <domain>/hello and confirm that the message "Hello World" is displayed.
