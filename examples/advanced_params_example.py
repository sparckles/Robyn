"""
Example demonstrating advanced parameter parsing with Query, Path, Header, and Pydantic models.

This showcases modern parameter parsing patterns while maintaining 
Robyn's performance and simplicity.

Usage:
    python examples/advanced_params_example.py
    
    Then visit:
    - http://localhost:8080/query?name=John&age=30&active=true
    - http://localhost:8080/path/user123/score/95.5
    - http://localhost:8080/header (with X-Token header)
    - POST to http://localhost:8080/user with JSON body
"""

from typing import Optional, List
from pydantic import BaseModel

from robyn import Robyn, Query, Path, Header, Form


app = Robyn(__file__)


# ===== Query Parameter Examples =====

@app.get("/query")
def query_example(
    name: str = Query(..., description="User name"),
    age: int = Query(25, description="User age with default"),
    active: bool = Query(True, description="Whether user is active"), 
    tags: Optional[List[str]] = Query(None, description="Optional list of tags")
):
    """Example with typed query parameters."""
    return {
        "name": name,
        "age": age,
        "active": active,
        "tags": tags,
        "message": f"Hello {name}, you are {age} years old and {'active' if active else 'inactive'}"
    }


@app.get("/query/alias")
def query_alias_example(user_name: str = Query(..., alias="username")):
    """Example with query parameter alias."""
    return {"message": f"Hello {user_name} (from username parameter)"}


# ===== Path Parameter Examples =====

@app.get("/path/:user_id/:score")
def path_example(
    user_id: int = Path(..., description="User ID"),
    score: float = Path(..., description="User score")
):
    """Example with typed path parameters."""
    return {
        "user_id": user_id,
        "score": score,
        "grade": "A" if score >= 90 else "B" if score >= 80 else "C"
    }


# ===== Header Parameter Examples =====

@app.get("/header")
def header_example(
    x_token: Optional[str] = Header(None, description="API token"),
    user_agent: Optional[str] = Header(None, description="User agent")
):
    """Example with header parameters."""
    return {
        "authenticated": x_token is not None,
        "token": x_token,
        "user_agent": user_agent
    }


@app.get("/header/custom")
def header_custom_example(
    api_key: str = Header(..., alias="X-API-Key"),
    request_id: Optional[str] = Header(None, alias="X-Request-ID")
):
    """Example with custom header names."""
    return {
        "api_key": api_key,
        "request_id": request_id
    }


# ===== Pydantic Model Examples =====

class User(BaseModel):
    name: str
    email: str
    age: int
    active: bool = True
    tags: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: int
    user: User
    created: bool = True


@app.post("/user")
def create_user(user: User) -> dict:
    """Example with Pydantic model for request body validation."""
    return {
        "received": user.dict(),
        "processed": {
            "name_upper": user.name.upper(),
            "is_adult": user.age >= 18,
            "tag_count": len(user.tags) if user.tags else 0
        }
    }


# ===== Mixed Parameter Examples =====

@app.get("/mixed/:item_id")
def mixed_example(
    item_id: int = Path(..., description="Item ID"),
    limit: int = Query(10, description="Results limit"),
    include_deleted: bool = Query(False),
    x_token: Optional[str] = Header(None)
):
    """Example combining path, query, and header parameters."""
    return {
        "item_id": item_id,
        "limit": limit,
        "include_deleted": include_deleted,
        "authenticated": x_token is not None,
        "query": f"SELECT * FROM items WHERE id={item_id} LIMIT {limit}"
    }


@app.post("/mixed/:user_id")
def mixed_with_body(
    user: User,
    user_id: int = Path(...),
    notify: bool = Query(True),
    x_source: Optional[str] = Header(None, alias="X-Source")
):
    """Example with path, query, header, and body parameters."""
    return {
        "user_id": user_id,
        "user": user.dict(),
        "notify": notify,
        "source": x_source,
        "action": f"Updated user {user_id} with data for {user.name}"
    }


# ===== Backward Compatibility Examples =====

@app.get("/legacy/request")
def legacy_request(request):
    """Still works with original Robyn request object."""
    return {
        "method": request.method,
        "path": request.url.path,
        "headers": dict(request.headers)
    }


@app.get("/legacy/split/:id")  
def legacy_split_params(path_params, query_params):
    """Still works with original parameter splitting."""
    return {
        "id": path_params.get("id"),
        "query": query_params.to_dict()
    }


# ===== Root Route =====

@app.get("/")
def index():
    """Main index with API documentation."""
    return {
        "message": "Advanced Parameter Parsing Example",
        "endpoints": {
            "query": "GET /query?name=John&age=30&active=true&tags=python&tags=web",
            "query_alias": "GET /query/alias?username=John",
            "path": "GET /path/123/95.5", 
            "header": "GET /header (with X-Token header)",
            "header_custom": "GET /header/custom (with X-API-Key header)",
            "user": "POST /user (with User JSON body)",
            "mixed": "GET /mixed/42?limit=20&include_deleted=true (with X-Token header)",
            "mixed_body": "POST /mixed/123?notify=false (with User JSON body and X-Source header)",
            "legacy": "GET /legacy/request and GET /legacy/split/123?test=value"
        },
        "examples": {
            "user_json": {
                "name": "John Doe",
                "email": "john@example.com", 
                "age": 30,
                "active": True,
                "tags": ["python", "web", "api"]
            }
        }
    }


if __name__ == "__main__":
    print("Starting Advanced Parameter Parsing Example Server...")
    print("Visit http://localhost:8080 for API documentation")
    print("Try different endpoints to see parameter parsing in action!")
    
    app.start(host="127.0.0.1", port=8080)