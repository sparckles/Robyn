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

![image](https://user-images.githubusercontent.com/70811425/202870632-4d3f46dc-1aa9-4603-9b0f-344ed87ec9d0.png)

And we select the repo we want to deploy. And click "Deploy Now".
![image](https://user-images.githubusercontent.com/70811425/202870837-16884fef-8900-4ab3-9794-0fb53c3ffd2e.png)

![image](https://user-images.githubusercontent.com/70811425/202871003-f79a1cef-9a5f-4166-be4f-527c60ec6c79.png)

Now, we click on our project's card.

Select "Variables" and press the "New Variable" button to set the environments variables.

![image](https://user-images.githubusercontent.com/70811425/202870681-5c069475-a5d1-4069-8582-c5b549d27aad.png)

Then, we go to Setting and click on "Generate Domain".

We would see the domain generate bellow "Domains".

![image](https://user-images.githubusercontent.com/70811425/202870735-6b955752-c5a6-48d5-acbc-1a4ea6fd7574.png)


We can go to <domain>/hello and confirm that the message "Hello World" is displayed.  
