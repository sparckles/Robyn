#!/usr/bin/env python3
"""
Quick Start Example: Advanced Parameter Parsing in Robyn

Copy and run this example to see the new features in action!

Usage:
    pip install "pydantic>=2.0.0"
    python quick_start_example.py

Then test with:
    curl "localhost:8080/search?q=python&limit=5&min_price=29.99&in_stock=true"
    curl -X POST localhost:8080/users -H "Content-Type: application/json" -d '{"name":"Alice","email":"alice@example.com","age":30}'
    curl -H "Authorization: Bearer token123" localhost:8080/profile
"""

from typing import Optional, List
from pydantic import BaseModel, field_validator

from robyn import Robyn, Query, Path, Header


# Create the app
app = Robyn(__file__)


# === 1. Query Parameters with Type Conversion ===
@app.get("/search")
def search_products(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Max results"),
    min_price: float = Query(0.0, description="Minimum price"),
    in_stock: bool = Query(True, description="Only in-stock items"),
    categories: List[str] = Query([], description="Categories to filter by"),
):
    """Search products with automatic type conversion."""
    return {
        "search_query": q,
        "limit": limit,
        "min_price": min_price,
        "in_stock": in_stock,
        "categories": categories,
        "type_info": {
            "limit_is_int": isinstance(limit, int),
            "min_price_is_float": isinstance(min_price, float),
            "in_stock_is_bool": isinstance(in_stock, bool),
            "categories_is_list": isinstance(categories, list),
        },
    }


# === 2. Path Parameters ===
@app.get("/users/:user_id/orders/:order_id")
def get_user_order(user_id: int = Path(..., description="User ID"), order_id: int = Path(..., description="Order ID")):
    """Get specific user order with path parameter parsing."""
    return {
        "user_id": user_id,
        "order_id": order_id,
        "user_id_type": type(user_id).__name__,
        "order_id_type": type(order_id).__name__,
        "order_details": f"Order #{order_id} for User #{user_id}",
    }


# === 3. Header Parameters ===
@app.get("/profile")
def get_user_profile(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    user_agent: Optional[str] = Header(None),  # Automatically converts to User-Agent
    api_version: str = Header("v1", alias="X-API-Version"),
):
    """Access user profile with header-based authentication."""
    is_authenticated = authorization is not None
    auth_type = authorization.split(" ")[0] if authorization else None

    return {
        "authenticated": is_authenticated,
        "auth_type": auth_type,
        "user_agent": user_agent,
        "api_version": api_version,
        "profile_data": {"name": "John Doe", "email": "john@example.com"} if is_authenticated else None,
        "message": "Profile loaded" if is_authenticated else "Authentication required",
    }


# === 4. Pydantic Models ===
class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int
    preferences: Optional[List[str]] = None
    active: bool = True

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower()

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if not (13 <= v <= 120):
            raise ValueError("Age must be between 13 and 120")
        return v


@app.post("/users")
def create_user(user: CreateUserRequest):
    """Create user with Pydantic validation and automatic JSON parsing."""
    return {
        "success": True,
        "user_data": user.model_dump(),
        "user_id": 12345,
        "is_adult": user.age >= 18,
        "email_domain": user.email.split("@")[1],
        "welcome_message": f"Welcome {user.name}!",
    }


# === 5. Mixed Parameters (All Types Together) ===
@app.put("/items/:item_id")
def update_item(
    user_data: CreateUserRequest,  # Request body (JSON)
    item_id: int = Path(..., description="Item ID"),  # Path parameter
    notify: bool = Query(True, description="Send notifications"),  # Query parameter
    priority: int = Query(1, description="Priority level"),  # Query parameter
    x_source: Optional[str] = Header(None, alias="X-Source"),  # Header parameter
    x_trace: Optional[str] = Header(None, alias="X-Trace-ID"),  # Header parameter
):
    """Update item combining all parameter types."""
    return {
        "item_id": item_id,
        "updated_by": user_data.name,
        "user_email": user_data.email,
        "notify_users": notify,
        "priority_level": priority,
        "request_source": x_source,
        "trace_id": x_trace,
        "status": "success",
        "message": f"Item {item_id} updated by {user_data.name} with priority {priority}",
    }


# === 6. Optional Parameters ===
@app.get("/products")
def list_products(
    page: int = Query(1, description="Page number"),
    per_page: int = Query(10, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    sort_by: str = Query("name", description="Sort field"),
    sort_desc: bool = Query(False, description="Sort descending"),
):
    """List products with flexible optional filtering."""
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price

    return {
        "page": page,
        "per_page": per_page,
        "total_pages": 10,
        "total_items": 100,
        "filters": filters,
        "sort": {"field": sort_by, "descending": sort_desc},
        "products": [{"id": 1, "name": "Product 1", "price": 29.99}, {"id": 2, "name": "Product 2", "price": 49.99}][:per_page],
    }


# === 7. Backward Compatibility Examples ===
@app.get("/legacy/request")
def old_style_request(request):
    """Traditional Robyn request handling - still works!"""
    return {
        "method": request.method,
        "path": request.url.path,
        "query_string": str(request.query_params),
        "header_count": len(dict(request.headers)),
        "message": "Old-style parameter handling works alongside new features!",
    }


@app.get("/legacy/params/:id")
def old_style_params(path_params, query_params):
    """Traditional parameter extraction - still works!"""
    return {"id": path_params.get("id"), "query_dict": query_params.to_dict(), "message": "Legacy parameter extraction works perfectly!"}


# === Root Route with Documentation ===
@app.get("/")
def api_documentation():
    """API documentation with example URLs."""
    return {
        "title": "Advanced Parameter Parsing Quick Start",
        "description": "Live examples of Robyn's new parameter parsing features",
        "examples": {
            "Search with query params": {
                "url": "/search?q=python&limit=5&min_price=29.99&in_stock=true&categories=books&categories=tech",
                "method": "GET",
                "description": "Shows automatic type conversion for all parameter types",
            },
            "Path parameters": {"url": "/users/123/orders/456", "method": "GET", "description": "Demonstrates typed path parameter extraction"},
            "Header authentication": {
                "url": "/profile",
                "method": "GET",
                "headers": {"Authorization": "Bearer your-token-here"},
                "description": "Shows header parameter parsing with aliases",
            },
            "Create user (JSON)": {
                "url": "/users",
                "method": "POST",
                "body": {"name": "Alice Smith", "email": "alice@example.com", "age": 30, "preferences": ["python", "web-dev"], "active": True},
                "description": "Pydantic model validation with custom validators",
            },
            "Update item (mixed params)": {
                "url": "/items/789?notify=false&priority=3",
                "method": "PUT",
                "headers": {"X-Source": "admin", "X-Trace-ID": "abc123"},
                "body": {"name": "Bob", "email": "bob@example.com", "age": 25},
                "description": "Combines all parameter types in one endpoint",
            },
            "List products (optional params)": {
                "url": "/products?page=2&category=electronics&min_price=50&sort_by=price&sort_desc=true",
                "method": "GET",
                "description": "Flexible filtering with optional parameters",
            },
            "Legacy compatibility": {
                "url": "/legacy/request?test=value",
                "method": "GET",
                "description": "Shows backward compatibility with existing Robyn syntax",
            },
        },
        "curl_examples": [
            'curl "localhost:8080/search?q=laptop&limit=3&min_price=500"',
            "curl localhost:8080/users/123/orders/456",
            'curl -H "Authorization: Bearer token123" localhost:8080/profile',
            'curl -X POST localhost:8080/users -H "Content-Type: application/json" -d \'{"name":"Alice","email":"alice@example.com","age":30}\'',
            'curl -X PUT "localhost:8080/items/789?notify=false" -H "X-Source: curl" -H "Content-Type: application/json" -d \'{"name":"Test","email":"test@example.com","age":25}\'',
            'curl "localhost:8080/products?page=1&category=books&sort_by=price"',
        ],
    }


if __name__ == "__main__":
    print("🚀 Starting Advanced Parameter Parsing Quick Start Server")
    print("=========================================================")
    print("")
    print("✨ Available endpoints:")
    print("  GET  /                     - API documentation")
    print("  GET  /search               - Query parameters with type conversion")
    print("  GET  /users/:id/orders/:id - Path parameters")
    print("  GET  /profile              - Header parameters")
    print("  POST /users                - Pydantic model (JSON body)")
    print("  PUT  /items/:id            - Mixed parameters (all types)")
    print("  GET  /products             - Optional parameters")
    print("  GET  /legacy/*             - Backward compatibility")
    print("")
    print("🧪 Try these curl commands:")
    print('  curl "localhost:8080/search?q=python&limit=5&min_price=29.99"')
    print('  curl -X POST localhost:8080/users -H "Content-Type: application/json" \\')
    print('       -d \'{"name":"Alice","email":"alice@example.com","age":30}\'')
    print('  curl -H "Authorization: Bearer token123" localhost:8080/profile')
    print("")
    print("🌐 Visit http://localhost:8080 in your browser for full documentation")
    print("=========================================================")

    app.start(host="127.0.0.1", port=8080)
