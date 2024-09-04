from robyn import Robyn, Request

app: Robyn = Robyn(file_object=__file__)


@app.get("/")
def welcome(r: Request):
    return r


@app.get("/sync/split_request/query_params")
def sync_split_request_basic(query_params):
    return query_params.to_dict()


@app.get("/async/split_request/query_params")
async def async_split_request_basic(query_params):
    return query_params.to_dict()


@app.get("/sync/split_request/headers")
def sync_split_request_headers(headers):
    return headers.get("server")


@app.get("/async/split_request/headers")
async def async_split_request_headers(headers):
    return headers.get("server")


@app.get("/sync/split_request/path_params/:id")
def sync_split_request_path_params(path_params):
    return path_params


@app.get("/async/split_request/path_params/:id")
async def async_split_request_path_params(path_params):
    return path_params


@app.get("/sync/split_request/method")
def sync_split_request_method(method):
    return method


@app.get("/async/split_request/method")
async def async_split_request_method(method):
    return method


@app.post("/sync/split_request/body")
def sync_split_request_body(body):
    return body


@app.post("/async/split_request/body")
async def async_split_request_body(body):
    return body


@app.post("/sync/split_request/combined")
def sync_split_request_combined(body, query_params, method, url, headers):
    return {
        "body": body,
        "query_params": query_params.to_dict(),
        "method": method,
        "url": url.path,
        "headers": headers.get("server"),
    }


@app.post("/async/split_request/combined")
async def async_split_request_combined(body, query_params, method, url, headers):
    return {
        "body": body,
        "query_params": query_params.to_dict(),
        "method": method,
        "url": url.path,
        "headers": headers.get("server"),
    }


if __name__ == "__main__":
    app.start()
