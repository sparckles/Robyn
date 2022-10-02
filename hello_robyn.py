from robyn import Robyn
import os 
from robyn.import_vars import main


app = Robyn(__file__)
main()
port_val = int(os.environ['PORT'])
@app.get("/")
async def h(request):
    return "Hello, world!"

app.start(port=port_val)