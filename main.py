from fastapi import FastAPI, Query, Path, Body, Cookie, Response, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import Annotated, Literal
from ast import literal_eval
from datetime import datetime, time, timedelta
from uuid import UUID


app = FastAPI()

class Item(BaseModel):
    id: Annotated[int, Field(title="ID validation title", description="The ID of the item", ge=0, le=1e6)]
    # use annotated and query to add documentation and validation to the name field. 
    # This will show up in the API docs and also enforce the validation rules when the endpoint is called.
    # Note that the default value is None. If any default value is used, the field becomes optional
    name: Annotated[str | None, Field(min_length=3, max_length=50, pattern="name_")] = None
    # this field is required because it has no default value, and it must be a string between 1 and 100 characters long.
    # None is allowed as a value, but requires user to explicitly set it to None if they don't want to provide a value. 
    # This is different from the name field, which is optional and defaults to None if not provided.
    favorite_animal: Annotated[str | None, Field(min_length=1, max_length=100, examples=["cat"])]
    # this was an attempt to have a query parameter that is a list of strings e.g.
    # https://fastapi.tiangolo.com/tutorial/query-params-str-validations/#query-parameter-list-multiple-values
    # but it does not work because these models are part of the body of the request, not query parameters
    cool_colors: Annotated[list[str] | None, Field()] = None


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




# use a Pydantic model to define the query parameters for an endpoint.
# This allows you to group related query parameters together and also provides validation and documentation for those parameters.
class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


@app.get("/filter-params/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query



class ItemUpdate(BaseModel):
    name: Annotated[str | None, Field(min_length=3, max_length=50, pattern="name_")] = None
    favorite_animal: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    cool_colors: list[str] | None = None


# using Body(embed=True) to indicate that the item parameter should be treated as a single object 
# in the request body, rather than being unpacked into individual fields.
@app.patch("/items/{item_id}/", description="Update an item with a path parameter and a body parameter")
async def update_item(item_id: int, item: Annotated[ItemUpdate, Body(embed=True)]) -> dict[str, str]:
    with open("items.txt", "r") as f:
        lines = f.readlines()

    updated_lines = []
    found = False

    for line in lines:
        parts = line.strip().split(": ", maxsplit=3)
        if len(parts) != 4:
            updated_lines.append(line)
            continue

        stored_id, name, favorite_animal, cool_colors = parts

        if int(stored_id) == item_id:
            found = True
            existing_item = Item(
                id=int(stored_id),
                name=name,
                favorite_animal=favorite_animal,
                cool_colors=list(literal_eval(cool_colors)),
            )

            update_data = item.model_dump(exclude_unset=True)
            updated_item = existing_item.model_copy(update=update_data)

            updated_lines.append(
                f"{updated_item.id}: {updated_item.name}: {updated_item.favorite_animal}: {updated_item.cool_colors}\n"
            )
        else:
            updated_lines.append(line)

    if not found:
        return {"message": f"Item with id {item_id} not found"}

    with open("items.txt", "w") as f:
        f.writelines(updated_lines)

    return {"message": "Item updated", "item": updated_item.model_dump()}
        
    
    


class NestedModelsTesting(BaseModel):
    id: Annotated[int, Field(title="ID validation title", description="The ID of the item", ge=0, le=1e6)]
    links: Annotated[set[HttpUrl], Field(description="A list of URLs related to the item")]
    
@app.post("/nested-models/", description="Test nested models with a list of URLs")
async def test_nested_models(item: NestedModelsTesting) -> dict[str, str]:
    with open("nested_models.txt", "a") as f:
        f.write(f"{item.id}: {item.links}\n")
    return {"message": f"Nested model received with id {item.id} and links {item.links}"}



app.mount("/static", StaticFiles(directory="test_static"), name="static")




# can only use a valid UUID like 550e8400-e29b-41d4-a716-446655440000
# UUID: "128-bit label used for unique identification, typically represented as 32 hexadecimal characters separated by hyphens in an 8-4-4-4-12 format."
@app.put("/test-extra-data-types/{item_id}")
async def test_extra_data_types(
    item_id: UUID,
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }
    


# I first need to set a cookie in the browser or using curl, then I can test the cookie by making a request
# to the test-cookie endpoint with the cookie included in the request headers.
@app.get("/set-cookie/")
async def set_cookie(response: Response):
    response.set_cookie(
        key="ads_id",
        value="12345",
    )
    return {"message": "cookie set"}


# example of a valid cookie value: ads_id=12345; Path=/; HttpOnly
# or the complete request might look like this generally: curl -v -H "Cookie: ads_id=abc123" http://localhost:8000/test-cookie/
# curl -X 'GET' \
#   'http://127.0.0.1:8000/test-cookie/' \
#   -H 'accept: application/json' \
#   -H 'Cookie: ads_id=ads_id%3D12345%3B%20Path%3D/%3B%20HttpOnly%20'
@app.get("/test-cookie/")
async def test_cookie(ads_id: Annotated[str | None, Cookie()] = None):
    return {"ads_id": ads_id}






class CommonHeaders(BaseModel):
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []


@app.get("/test-headers/")
async def test_headers(headers: Annotated[CommonHeaders, Header()]):
    return headers