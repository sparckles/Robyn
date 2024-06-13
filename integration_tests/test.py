from robyn import Robyn
from robyn.robyn import Request, Response
import time, threading

app = Robyn(__file__)

count = 0
def Counter():
    global count
    
    while 1:
        count += 1
        time.sleep(0.2)
        print(count,"added 1")
        
@app.get("/")
def Teste():
    global count
    return Response(description=str(count),status_code=200,headers={})

threading.Thread(target=Counter,daemon=True).start()

app.start()
