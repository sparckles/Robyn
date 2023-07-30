
# the "app" parameter in the constructor refers to a Robyn application
# app.router leads to the router, and from there we can use app.router.get_routes()
# to retrieve the routes the server supports. We can search said list for methods
# to match test requests made by the server's developer

# it's important to understand the following classes, at least right now:
# Route, Request, Response

class TestingClient:
	def __init__(self, app):
		self.app = app

