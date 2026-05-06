from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str | None = None

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/custom/{item_id}", description="This is a custom function description")
async def custom_func_name(item_id: str):
    return {"message": f"This is a custom function name for item {item_id}"}


@app.post("/items", description="Create an item")
async def create_item(item: Item):
    # write to a file in this project folder and create file if it doesn't exist
    with open("items.txt", "a") as f:
        f.write(f"{item.id}: {item.name}\n")
    return {"message": f"Item created with id {item.id} and name {item.name}"}


@app.get("/items", description="Get all items")
async def get_items(limit: int = 10, reverse: bool = False):
    items = []
    with open("items.txt", "r") as f:
        if reverse:
            lines = f.readlines()
            for line in reversed(lines):
                id, name = line.strip().split(": ")
                items.append(Item(id=int(id), name=name))
                if len(items) >= limit:
                    break
        else:
            for line in f:
                id, name = line.strip().split(": ")
                items.append(Item(id=int(id), name=name))
                if len(items) >= limit:
                    break
    return items