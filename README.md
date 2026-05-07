# Learning FastAPI

This repo is composed of code and information I picked up while learning the FastAPI framework. This README will mostly contain shortcuts and broad pieces of information. The `main.py` file is my testing file for adding different types of endpoints, making use of Pydantic for data models, and the `commands.sh` file contains miscellaneous bash/zsh commands I wanted to explore or use.

## FastAPI Default Endpoints

* Default app exposed at http://127.0.0.1:8000/
* OpenAPI conforming auto-documentation available at http://127.0.0.1:8000/docs and http://127.0.0.1:8000/redoc
    - SwaggerUI vs. Redoc?
* Raw JSON API schema at http://127.0.0.1:8000/openapi.json


## Endpoints Writing/Reading to Files

* Exploring use of `filelock` or other Python libraries that allow locking of a file for the period that a process is writing to it.
* Why bother? Would allow the `async` endpoints to actually perform processing like writing to files in an async-await manner
* To read back a list data structure, needed to use ast.literal_eval() to properly evaluate the text as a list structure


## Parameter Types

### Path

* The path of the request, namely the inclusion of some particular value, is the main parameter of the request

```python
@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}
```

So a request to `/items/3` is a path parameter request, for example.

### Query

* Query strings from the URL can be used to make requests too.

```python
@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

And a request to `/items/?skip=10` would therefore be using a query parameter.


### Body

* This expects a particular body format to be delivered/received, namely defining a particular JSON format. This is typically done by using a Pydantic model.

```python
from fastapi import FastAPI
from pydantic import BaseModel

# this is the Pydantic model. this is a basic one, but more advanced validation
# and templating for the API docs can be added here using Field()
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


app = FastAPI()


@app.post("/items/")
async def create_item(item: Item):
    return item
```


### Header