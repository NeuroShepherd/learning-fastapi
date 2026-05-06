!#/bin/zsh

# Install FastAPI and its dependencies
uv add "fastapi[standard]"


# Run the app
fastapi dev

# example posting to an endpoint from the command line
# -H indicates the header, -d indicates the data to be sent in the request body
curl -X POST "http://127.0.0.1:8000/items" \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "name": "widget"}'