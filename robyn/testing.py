
# the "app" parameter in the constructor refers to a Robyn application
# app.router leads to the router, and from there we can use app.router.get_routes()
# to retrieve the routes the server supports. We can search said list for methods
# to match test requests made by the server's developer

# it's important to understand the following classes, at least right now:
# Route, Request, Response

import asyncio
from robyn import Request, Response

def get_route(app, path):
	routes = app.router.get_routes()
	r = None
	for route in routes:
		if route.route == path:
			r = route
			break
	return r

class TestingClient:
	def __init__(self, app):
		self.app = app
	
	def get(self, method_path, arg = None):
		route = get_route(self.app, method_path)
		if route == None:
			return None
		return asyncio.run(route.function.handler(None))
		

