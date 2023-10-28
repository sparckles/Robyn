from pymongo import MongoClient
from robyn import Robyn

app = Robyn(__file__)
db = MongoClient("URL HERE")

users = db.users  # define a collection


@app.get("/")
def index():
    return "Hello World!"


# create a route
@app.get("/users")
async def get_users():
    all_users = await users.find().to_list(length=None)
    return {"users": all_users}


# create a route to add a new user
@app.post("/users")
async def add_user(request):
    user_data = await request.json()
    result = await users.insert_one(user_data)
    return {"success": True, "inserted_id": str(result.inserted_id)}


# create a route to fetch a single user by ID
@app.get("/users/{user_id}")
async def get_user(request):
    user_id = request.path_params["user_id"]
    user = await users.find_one({"_id": user_id})
    if user:
        return user
    else:
        return {"error": "User not found"}, 404


if __name__ == "__main__":
    app.start(host="0.0.0.0", port=8080)
