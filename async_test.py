
class App:
    @staticmethod
    async def mount_asgi(scope, receive, send):
        assert scope['type'] == 'http'

        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'text/plain'],
            ],
        })

        await send({
            'type': 'http.response.body',
            'body': b'Hello, world!',
        })



app = App()
