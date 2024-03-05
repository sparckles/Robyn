from robyn import Robyn, jsonify

app = Robyn(__file__)

@app.get("/")
async def h(request):
    return "Hello, Robyn!"
    
@app.post("/upload")
async def h(request):
    #TODO: Add functionality for downloading files to a folder within working directory
    return jsonify({"message":"File uploaded successfully"})

#app.start(port=8080)
