from fastapi import FastAPI, Query, Path
from pydantic import BaseModel
from enum import Enum
from typing import Annotated
from ast import literal_eval

app = FastAPI()

class Item(BaseModel):
    id: Annotated[int, Query(ge=0, le=1e6)]
    # use annotated and query to add documentation and validation to the name field. 
    # This will show up in the API docs and also enforce the validation rules when the endpoint is called.
    # Note that the default value is None. If any default value is used, the field becomes optional
    name: Annotated[str | None, Query(min_length=3, max_length=50, pattern="name_")] = None
    # this field is required because it has no default value, and it must be a string between 1 and 100 characters long.
    # None is allowed as a value, but requires user to explicitly set it to None if they don't want to provide a value. 
    # This is different from the name field, which is optional and defaults to None if not provided.
    favorite_animal: Annotated[str | None, Query(min_length=1, max_length=100)]
    cool_colors: Annotated[list[str] | None, Query()] = None


class FavoriteSport(str, Enum):
    soccer = "soccer"
    basketball = "basketball"
    baseball = "baseball"
    track = "track"

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/custom/{item_id}", description="This is a custom function description")
async def custom_func_name(item_id: str):
    return {"message": f"This is a custom function name for item {item_id}"}


@app.post("/items", description="Create an item")
async def create_item(item: Item) -> dict[str, str]:
    # write to a file in this project folder and create file if it doesn't exist
    with open("items.txt", "a") as f:
        f.write(f"{item.id}: {item.name}: {item.favorite_animal}: {item.cool_colors}\n")
    return {"message": f"Item created with id {item.id} and name {item.name} with favorite animal {item.favorite_animal} and cool colors {item.cool_colors}"}


@app.get("/items", description="Get all items")
async def get_items(limit: int = 10, reverse: bool | None = None) -> list[Item]:
    items = []
    with open("items.txt", "r") as f:
        if reverse:
            lines = f.readlines()
            for line in reversed(lines):
                parts = line.strip().split(": ", maxsplit=3)
                if len(parts) != 4:
                    continue
                id, name, favorite_animal, cool_colors = parts
                cool_colors = literal_eval(cool_colors)
                items.append(Item(id=int(id), name=name, favorite_animal=favorite_animal, cool_colors=list(cool_colors)))
                if len(items) >= limit:
                    break
        else:
            for line in f:
                print(line)
                parts = line.strip().split(": ", maxsplit=3)
                if len(parts) != 4:
                    continue
                id, name, favorite_animal, cool_colors = parts
                cool_colors = literal_eval(cool_colors)
                items.append(Item(id=int(id), name=name, favorite_animal=favorite_animal, cool_colors=list(cool_colors)))
                if len(items) >= limit:
                    break
    return items


@app.get("/items/{item_id}", description="Get an item by id")
async def get_item_by_id(item_id: Annotated[int, Path(ge=0)]) -> list[Item] | dict[str, str]:
    matches = []
    with open("items.txt", "r") as f:
        for line in f:
            parts = line.strip().split(": ", maxsplit=3)
            if len(parts) != 4:
                continue
            id, name, favorite_animal, cool_colors = parts
            cool_colors = literal_eval(cool_colors)
            if int(id) == item_id:
                matches.append(Item(id=int(id), name=name, favorite_animal=favorite_animal, cool_colors=list(cool_colors)))
    if matches:
        return matches
    return {"message": f"Item with id {item_id} not found"}


@app.post("/favorite-sport", description="Set your favorite sport")
async def set_favorite_sport(sport: FavoriteSport) -> dict[str, str]:
    with open("favorite_sport.txt", "w") as f:
        f.write(sport.value)
    return {"message": f"Your favorite sport is {sport.value}"}


# use ** to unpack the item model into a dictionary and combine it with the item_id in the response
# example makes use of path and body parameters in the same endpoint. could also use query parameters if desired
@app.put("/items/{item_id}", 
         description="This overrides the doc string from the function", 
         summary="Text goes next to the endpoint name"
         )
async def update_item(item_id: int, item: Item) -> dict[str, str]:
    """
    Do these doc strings show up in the API docs? Yes they do! As text content under the endpoint description. 
    You can use this to provide more detailed information about the endpoint, its parameters, and its behavior.
    Only appears if you don't provide a description in the decorator, otherwise the description in the decorator takes precedence.
    """
    return {"item_id": item_id, **item.model_dump()}