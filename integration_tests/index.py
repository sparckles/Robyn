from robyn import Robyn
import logging

app = Robyn(__file__)


@app.get("/")
async def h():
    logging.info("Insert log message here")
    return "For testing purposes only"


app.start()
