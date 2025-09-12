# Advanced Parameter Parsing

Robyn now supports advanced parameter parsing with type validation for modern web development. This feature provides a more declarative way to handle request parameters while maintaining backward compatibility.

## Features

- **Query Parameters**: `Query(...)` - Type-safe query parameter parsing with validation
- **Path Parameters**: `Path(...)` - Type-safe path parameter parsing with validation
- **Headers**: `Header(...)` - Type-safe header parsing with automatic underscore conversion
- **Request Body**: Pydantic models for JSON body validation and parsing
- **Type Conversion**: Automatic conversion for `str`, `int`, `float`, `bool`, `List[T]`
- **Optional Parameters**: Support for `Optional[T]` with default values
- **Parameter Aliases**: Use different names in code vs HTTP requests
- **Backward Compatibility**: Existing Robyn parameter handling still works

## Quick Start

```python
from typing import Optional, List
from pydantic import BaseModel
from robyn import Robyn, Query, Path, Header

app = Robyn(__file__)

# Query parameters with validation
@app.get("/users")
def get_users(
    limit: int = Query(10, description="Number of users to return"),
    active: bool = Query(True, description="Filter active users"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags")
):
    return {"limit": limit, "active": active, "tags": tags}

# Path parameters with type conversion
@app.get("/users/:user_id/posts/:post_id")  
def get_user_post(
    user_id: int = Path(..., description="User ID"),
    post_id: int = Path(..., description="Post ID")
):
    return {"user_id": user_id, "post_id": post_id}

# Headers with aliases
@app.get("/protected")
def protected_endpoint(
    api_key: str = Header(..., alias="X-API-Key"),
    user_agent: Optional[str] = Header(None)
):
    return {"authenticated": True, "user_agent": user_agent}

# Pydantic models for request body
class User(BaseModel):
    name: str
    email: str
    age: int
    active: bool = True

@app.post("/users")
def create_user(user: User):
    return {"created": user.dict(), "is_adult": user.age >= 18}

# Mixed parameters
@app.put("/users/:user_id")
def update_user(
    user: User,  # Body
    user_id: int = Path(...),  # Path
    notify: bool = Query(True),  # Query
    x_source: Optional[str] = Header(None, alias="X-Source")  # Header
):
    return {
        "user_id": user_id,
        "updated": user.dict(),
        "notify": notify,
        "source": x_source
    }
```

## Parameter Types

### Query Parameters

Use `Query(...)` to define query parameters with validation:

```python
@app.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Results limit"),
    category: Optional[str] = Query(None, alias="cat"),
    tags: List[str] = Query([], description="Filter tags")
):
    return {"query": q, "limit": limit, "category": category, "tags": tags}

# GET /search?q=python&limit=20&cat=web&tags=api&tags=rest
```

### Path Parameters

Use `Path(...)` to define path parameters with validation:

```python
@app.get("/items/:item_id/reviews/:review_id")
def get_review(
    item_id: int = Path(..., description="Item ID"), 
    review_id: int = Path(..., description="Review ID")
):
    return {"item_id": item_id, "review_id": review_id}

# GET /items/123/reviews/456
```

### Header Parameters

Use `Header(...)` to define header parameters:

```python
@app.get("/api/data")
def get_data(
    authorization: str = Header(..., alias="Authorization"),
    content_type: str = Header("application/json", alias="Content-Type"),
    x_request_id: Optional[str] = Header(None)  # Converts x_request_id to X-Request-ID
):
    return {"auth": authorization, "content_type": content_type}
```

### Request Body with Pydantic

Define Pydantic models for automatic JSON validation:

```python
from pydantic import BaseModel, validator

class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int
    tags: Optional[List[str]] = None
    
    @validator('email')
    def validate_email(cls, v):
        assert '@' in v, 'Invalid email'
        return v
    
    @validator('age')
    def validate_age(cls, v):
        assert 0 <= v <= 150, 'Invalid age'
        return v

@app.post("/users")
def create_user(user: CreateUserRequest):
    return {"created": user.dict()}
```

## Type Conversion

Parameters are automatically converted to the specified types:

- `str`: No conversion
- `int`: `int(value)` 
- `float`: `float(value)`
- `bool`: `"true"`, `"1"`, `"yes"`, `"on"` → `True`; others → `False`
- `List[T]`: Multiple values converted to list of type T
- `Optional[T]`: Allows `None` values

## Parameter Options

All parameter types support these options:

- `default`: Default value (use `...` for required)
- `description`: Documentation string
- `alias`: Alternative name for the parameter

### Query-specific Options
```python
tags: List[str] = Query([], description="Tags", alias="tag")
```

### Header-specific Options  
```python
token: str = Header(..., convert_underscores=True)  # user_agent → User-Agent
```

## Backward Compatibility

Existing Robyn parameter handling continues to work:

```python
@app.get("/legacy")
def legacy_handler(request):
    return {"method": request.method}

@app.get("/legacy/:id")
def legacy_params(path_params, query_params):
    return {"id": path_params.get("id"), "query": query_params.to_dict()}
```

## Error Handling

Invalid parameters raise `ValueError` with descriptive messages:

- Missing required parameters: `"Required query parameter 'name' is missing"`
- Type conversion errors: `"Parameter 'age': invalid literal for int()"`
- Pydantic validation errors: `"Invalid request body: field required"`

## Example App

See `examples/advanced_params_example.py` for a complete working example demonstrating all features.

## Migration Guide

To migrate existing routes:

1. **Simple parameters**: Add type annotations and `Query(...)`/`Path(...)`
2. **Request body**: Replace manual JSON parsing with Pydantic models  
3. **Headers**: Replace manual header access with `Header(...)`
4. **Mixed usage**: Combine different parameter types as needed

The advanced parameter parsing automatically falls back to legacy behavior when parameters don't use the new syntax, ensuring full backward compatibility.