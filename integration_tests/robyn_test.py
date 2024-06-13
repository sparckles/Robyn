from robyn import Robyn, Request, Response

app = Robyn(__name__)

@app.post('/image') # in-progress
async def image_endpoint(request: Request):
    
    print(len(request.files)) # added this for debugging on why it isn't showing the image after post request
    print(type(request.files)) # added this for debugging on why it isn't showing the image after post request
    
    for key in request.files: # added this for debugging on why it isn't showing the image after post request
        print(key)
        
    print(list(request.files.keys())) # added this for debugging on why it isn't showing the image after post request

    try:
        if 'test.png' not in request.files:
            return {"error 1": "No image uploaded"}

        filename = "test.png"
        uploaded_file = request.files[filename]
        print(uploaded_file) # added this for debugging on why it isn't showing the image after post request
        
        with open(filename, 'wb') as f:
            f.write(uploaded_file)
              
        headers = {"Content-Type": "image/jpeg"}
    
        return Response(description=uploaded_file, headers=headers, status_code=200)
    except Exception as e:
        return {"error 2": str(e)}

if __name__ == '__main__':
    app.start(port=8082)
