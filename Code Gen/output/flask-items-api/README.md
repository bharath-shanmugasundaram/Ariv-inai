# Flask Items API

A simple Flask REST API with health check and items management endpoints.

## Features

- Health check endpoint (`/health`)
- Items management (`/items`)
  - GET: Retrieve all items
  - POST: Create a new item
  - GET /items/{id}: Retrieve a specific item
  - PUT /items/{id}: Update an item
  - DELETE /items/{id}: Delete an item

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. The API will be available at `http://localhost:5000`

## Usage Examples

### Health Check
```bash
curl http://localhost:5000/health
```

### Get All Items
```bash
curl http://localhost:5000/items
```

### Create a New Item
```bash
curl -X POST http://localhost:5000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "New Item", "description": "A new item"}'
```

### Update an Item
```bash
curl -X PUT http://localhost:5000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Item", "description": "Updated description"}'
```

### Delete an Item
```bash
curl -X DELETE http://localhost:5000/items/1
```
