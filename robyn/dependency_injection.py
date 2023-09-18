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

    def add_route_dependency(self, route: str, **kwargs: any):
        """ Adds a dependency to a route.
        
        Args:
            route (str): The route to add the dependency to.
            kwargs (dict): The dependencies to add to the route.
        """
        if route not in self._dependency_map:
            self._dependency_map[route] = {}
        self._dependency_map[route].update(**kwargs)

    def add_global_dependency(self, **kwargs: any):
        """ Adds a dependency to all routes.

        Args:
            kwargs (dict): The dependencies to add to all routes.
        """
        for name, element in kwargs.items():
            self._dependency_map["ALL_ROUTES"].update({name: element})

    def get_route_dependencies(self,route: str):
        """ Gets the dependencies for a specific route.

        Args:
            route (str): The route to get the dependencies for.

        Returns:
            dict: The dependencies for the specified route.
        """
        if route in self._dependency_map:
            return self._dependency_map[route]
        else: 
            raise KeyError(f"Route '{route}' not found in dependencies.")



    def get_dependencies(self):
        """ Gets the dependencies for a route.

        Args:
            route (str): The route to get the dependencies for.
        """
        return self._dependency_map["ALL_ROUTES"]
    
    def merge_dependencies(self, target_router):
        """
        Merge dependencies from this DependencyMap into another router's DependencyMap.

        Args:
            target_router: The router with which to merge dependencies.
        
        This method iterates through the dependencies of this DependencyMap and adds any dependencies
        that are not already present in the target router's DependencyMap. 
        """
        for dep_key in self.get_dependencies():
            if dep_key in target_router.dependencies.get_dependencies():
                continue
            target_router.dependencies.get_dependencies()[dep_key] = self.get_dependencies()[dep_key] 
    @property
    def dependency_map(self):
        return self._dependency_map
