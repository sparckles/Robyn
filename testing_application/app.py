from robyn import Robyn, jsonify
import complex_code

app = Robyn(__file__)

@app.get("/")
async def h(request):
    ans = 2
    ans = complex_code.square(2)
    return ans



app.add_response_header("content-type", "application/json; charset=UTF-8")
app.start()
