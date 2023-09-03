""" This is Robyn's dependency injection file.
"""
from robyn.robyn import (
    Response,
    Request,
)


class DependencyMap:
    def __init__(self):
        #'request' and 'response' mappings are needed for when constructing deps_to_pass in router.py
        self._dependency_map = {"ALL_ROUTES": {"request": Request, "response": Response}}

    def add_route_dependency(self, route, **kwargs):
        """ Adds a dependency to a route.
        
        Args:
            route (str): The route to add the dependency to.
            kwargs (dict): The dependencies to add to the route.
        """
        if route not in self._dependency_map:
            self._dependency_map[route] = {}

        self._dependency_map[route].update(**kwargs)

    def add_global_dependency(self, **kwargs):
        """ Adds a dependency to all routes.

        Args:
            kwargs (dict): The dependencies to add to all routes.
        """
        for element in self._dependency_map:
            self._dependency_map[element].update(**kwargs)

    def get_dependencies(self, route=None):
        """ Gets the dependencies for a route.

        Args:
            route (str): The route to get the dependencies for.
        """
        if route:
            if route in self._dependency_map:
                return self._dependency_map[route]
        else:
            return self._dependency_map["ALL_ROUTES"]

    @property
    def dependency_map(self):
        return self._dependency_map
