class WS:
    """This is the python wrapper for the web socket that will be used here.
    """
    def __init__(self, robyn_object, endpoint) -> None:
        self.robyn_object = robyn_object
        robyn_object.web_socket_endpoint = endpoint

    def on(self, type):
        def inner(handler):
            print("Hwllo world", type, handler)
            if type not in ["connect", "close", "message"]:
                raise Exception("Wrong Socket Route")
            else:
               self.robyn_object.web_socket_handler(handler=handler, type=type) 

        return inner
