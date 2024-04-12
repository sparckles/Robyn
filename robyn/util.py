import inspect
from robyn.robyn import FunctionType

def get_function_type(handler):
  # as this is the most likely case, short circuit for it
  is_sync = ( 
        not asyncio.iscoroutinefunction(handler) and 
        not inspect.isgeneratorfunction(handler) and 
        not inpsect.isasyncgenfunction(handler)
      )
  if is_sync:
    return FunctionType.SYNC
  if inspect.iscoroutinefunction(handler): return FunctionType.ASYNC
  if inspect.isasyncgenfunction(handler): return FunctionType.ASYNCGENERATOR
  if inspect.isgeneratorfunction(handler): return FunctionType.SYNCGENERATOR


class FunctionInfoFactory:
    """Used for constructing FunctionInfo and wrapper"""
    def create_route(handler):