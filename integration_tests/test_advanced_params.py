import pytest
import requests
import json
from typing import Optional, List
from pydantic import BaseModel

from robyn import Robyn, Query, Path, Header, Form
from robyn.robyn import Request


def setup_app():
    """Setup test app with advanced parameter routes."""
    app = Robyn(__file__)
    
    # Test Query parameters
    @app.get("/query/basic")
    def query_basic(name: str = Query(..., description="Name parameter")):
        return {"name": name}
    
    @app.get("/query/optional") 
    def query_optional(name: Optional[str] = Query(None, description="Optional name")):
        return {"name": name}
    
    @app.get("/query/default")
    def query_default(name: str = Query("default", description="Name with default")):
        return {"name": name}
    
    @app.get("/query/typed")
    def query_typed(
        name: str = Query(...),
        age: int = Query(...),
        active: bool = Query(True),
        score: Optional[float] = Query(None)
    ):
        return {"name": name, "age": age, "active": active, "score": score}
    
    @app.get("/query/list")
    def query_list(tags: List[str] = Query(...)):
        return {"tags": tags}
    
    @app.get("/query/alias")
    def query_alias(user_name: str = Query(..., alias="username")):
        return {"user_name": user_name}
    
    # Test Path parameters
    @app.get("/path/basic/:name")
    def path_basic(name: str = Path(...)):
        return {"name": name}
    
    @app.get("/path/typed/:user_id/:score")
    def path_typed(user_id: int = Path(...), score: float = Path(...)):
        return {"user_id": user_id, "score": score}
    
    # Test Header parameters
    @app.get("/header/basic")
    def header_basic(x_token: str = Header(...)):
        return {"token": x_token}
    
    @app.get("/header/optional")
    def header_optional(x_token: Optional[str] = Header(None)):
        return {"token": x_token}
    
    @app.get("/header/alias")
    def header_alias(token: str = Header(..., alias="X-API-Key")):
        return {"token": token}
    
    @app.get("/header/underscore")
    def header_underscore(user_agent: str = Header(...)):
        return {"user_agent": user_agent}
    
    # Test Pydantic models
    class User(BaseModel):
        name: str
        email: str
        age: int
        active: bool = True
    
    class UserResponse(BaseModel):
        id: int
        user: User
        created: bool = True
    
    @app.post("/pydantic/user")
    def create_user(user: User) -> dict:
        return {
            "received": user.dict(),
            "name_upper": user.name.upper(),
            "is_adult": user.age >= 18
        }
    
    @app.post("/pydantic/nested")
    def nested_user(user: User, user_id: int = Query(...)) -> dict:
        return {
            "user": user.dict(),
            "user_id": user_id
        }
    
    # Test mixed parameters
    @app.get("/mixed/:item_id")
    def mixed_params(
        item_id: int = Path(...),
        name: str = Query(...),
        x_token: Optional[str] = Header(None),
        limit: int = Query(10)
    ):
        return {
            "item_id": item_id,
            "name": name,
            "token": x_token,
            "limit": limit
        }
    
    # Test backward compatibility - should still work with original Robyn style
    @app.get("/legacy/request")
    def legacy_request(request: Request):
        return {"method": request.method, "path": request.url.path}
    
    @app.get("/legacy/split/:id")
    def legacy_split(path_params, query_params):
        return {
            "id": path_params.get("id"),
            "params": query_params.to_dict()
        }
    
    return app


def test_query_basic():
    """Test basic query parameter parsing."""
    app = setup_app()
    
    # This would be tested with a proper test client
    # For now, we'll test the parameter parsing logic directly
    from robyn.advanced_params import parse_advanced_params, Query
    from robyn.robyn import Request, QueryParams
    
    def test_handler(name: str = Query(...)):
        return {"name": name}
    
    # Mock request
    class MockRequest:
        def __init__(self):
            self.query_params = QueryParams()
            self.query_params._data = {"name": "John"}
            self.path_params = {}
            self.headers = {}
            self.body = b""
    
    request = MockRequest()
    params = parse_advanced_params(test_handler, request)
    
    assert "name" in params
    assert params["name"] == "John"


def test_query_typed():
    """Test typed query parameter parsing."""
    from robyn.advanced_params import parse_advanced_params, Query
    
    def test_handler(
        name: str = Query(...),
        age: int = Query(...),
        active: bool = Query(True)
    ):
        return {"name": name, "age": age, "active": active}
    
    class MockRequest:
        def __init__(self):
            self.query_params = QueryParams()
            self.query_params._data = {"name": "John", "age": "25", "active": "true"}
            self.path_params = {}
            self.headers = {}
            self.body = b""
    
    request = MockRequest()
    params = parse_advanced_params(test_handler, request)
    
    assert params["name"] == "John"
    assert params["age"] == 25
    assert params["active"] == True


def test_query_optional():
    """Test optional query parameter parsing."""
    from robyn.advanced_params import parse_advanced_params, Query
    from typing import Optional
    
    def test_handler(name: Optional[str] = Query(None)):
        return {"name": name}
    
    class MockRequest:
        def __init__(self):
            self.query_params = QueryParams()
            self.query_params._data = {}
            self.path_params = {}
            self.headers = {}
            self.body = b""
    
    request = MockRequest()
    params = parse_advanced_params(test_handler, request)
    
    assert params["name"] is None


def test_path_params():
    """Test path parameter parsing."""
    from robyn.advanced_params import parse_advanced_params, Path
    from robyn.types import PathParams
    
    def test_handler(user_id: int = Path(...)):
        return {"user_id": user_id}
    
    class MockRequest:
        def __init__(self):
            self.query_params = QueryParams()
            self.query_params._data = {}
            self.path_params = PathParams()
            self.path_params._data = {"user_id": "123"}
            self.headers = {}
            self.body = b""
    
    request = MockRequest()
    params = parse_advanced_params(test_handler, request)
    
    assert params["user_id"] == 123


def test_header_params():
    """Test header parameter parsing."""
    from robyn.advanced_params import parse_advanced_params, Header
    from robyn.robyn import Headers
    
    def test_handler(x_token: str = Header(...)):
        return {"token": x_token}
    
    class MockRequest:
        def __init__(self):
            self.query_params = QueryParams()
            self.query_params._data = {}
            self.path_params = {}
            self.headers = Headers({"x-token": "secret123"})
            self.body = b""
    
    request = MockRequest()
    params = parse_advanced_params(test_handler, request)
    
    assert params["x_token"] == "secret123"


def test_pydantic_model():
    """Test Pydantic model parsing."""
    from robyn.advanced_params import parse_advanced_params
    from pydantic import BaseModel
    
    class User(BaseModel):
        name: str
        age: int
        email: str
    
    def test_handler(user: User):
        return {"user": user}
    
    class MockRequest:
        def __init__(self):
            self.query_params = QueryParams()
            self.query_params._data = {}
            self.path_params = {}
            self.headers = {}
            self.body = json.dumps({"name": "John", "age": 30, "email": "john@example.com"})
    
    request = MockRequest()
    params = parse_advanced_params(test_handler, request)
    
    assert "user" in params
    assert isinstance(params["user"], User)
    assert params["user"].name == "John"
    assert params["user"].age == 30
    assert params["user"].email == "john@example.com"


def test_mixed_params():
    """Test mixed parameter types."""
    from robyn.advanced_params import parse_advanced_params, Query, Path, Header
    from robyn.types import PathParams
    from robyn.robyn import Headers
    from typing import Optional
    
    def test_handler(
        item_id: int = Path(...),
        name: str = Query(...),
        x_token: Optional[str] = Header(None),
        limit: int = Query(10)
    ):
        return {
            "item_id": item_id,
            "name": name,
            "token": x_token,
            "limit": limit
        }
    
    class MockRequest:
        def __init__(self):
            self.query_params = QueryParams()
            self.query_params._data = {"name": "test", "limit": "20"}
            self.path_params = PathParams()
            self.path_params._data = {"item_id": "42"}
            self.headers = Headers({"x-token": "bearer123"})
            self.body = b""
    
    request = MockRequest()
    params = parse_advanced_params(test_handler, request)
    
    assert params["item_id"] == 42
    assert params["name"] == "test"
    assert params["x_token"] == "bearer123"
    assert params["limit"] == 20


def test_validation_errors():
    """Test parameter validation errors."""
    from robyn.advanced_params import parse_advanced_params, Query
    
    def test_handler(age: int = Query(...)):
        return {"age": age}
    
    class MockRequest:
        def __init__(self):
            self.query_params = QueryParams()
            self.query_params._data = {"age": "not_a_number"}
            self.path_params = {}
            self.headers = {}
            self.body = b""
    
    request = MockRequest()
    
    with pytest.raises(ValueError):
        parse_advanced_params(test_handler, request)


if __name__ == "__main__":
    # Run basic tests
    test_query_basic()
    test_query_typed()
    test_query_optional()
    test_path_params()
    test_header_params()
    test_pydantic_model()
    test_mixed_params()
    
    print("All advanced parameter tests passed!")