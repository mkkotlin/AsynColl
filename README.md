# Collaborative Board API

A Django Rest Framework backend for a collaborative kanban-style board application.

## Features

- **Boards**: Create and manage project boards.
- **Lists**: Group tasks into lists within a specific board.
- **Cards**: Tasks that belong to a list, with customizable positions and descriptions.
- **Card Movement**: Easily move cards between different lists or reorder them within the same list.
- **Optimized Queries**: Advanced query filtering and `prefetch_related` built into the API to avoid N+1 query problems.

## Models

- **Board**: Has a `name` and belongs to an `owner` (User).
- **List**: Has a `name` and belongs to a `board` (Foreign Key).
- **Card**: Has a `title`, `description`, `position` (integer for ordering), and belongs to a `list` (Foreign Key). Cards can also be `assigned_to` a User.

## API Endpoints

The core resources are registered under `/api/`:

### Boards
- `GET /api/boards/` - List all boards
- `POST /api/boards/` - Create a board
- `GET /api/boards/{id}/` - Retrieve board details
- `PUT/PATCH /api/boards/{id}/` - Update a board
- `DELETE /api/boards/{id}/` - Delete a board

### Lists
- `GET /api/lists/` - List all lists
- `GET /api/lists/?board={id}` - Filter lists by a specific board
- `POST /api/lists/` - Create a list
- `GET /api/lists/{id}/` - Retrieve list details
- `PUT/PATCH /api/lists/{id}/` - Update a list
- `DELETE /api/lists/{id}/` - Delete a list

### Cards
- `GET /api/cards/` - List all cards
- `GET /api/cards/?list={id}` - Filter cards by a specific list
- `GET /api/cards/?board={id}` - Filter cards across an entire board
- `POST /api/cards/` - Create a new card
- `GET /api/cards/{id}/` - Retrieve card details
- `PUT/PATCH /api/cards/{id}/` - Update a card (including moving lists or changing `position`)
- `DELETE /api/cards/{id}/` - Delete a card

## Error Handling

The API includes robust validation and error handling:
- Trying to filter by a non-integer ID will return a `400 Bad Request` with a helpful message.
- Trying to filter by an ID that doesn't exist in the database will return a `404 Not Found`.

## Local Development

1. Activate your virtual environment (`AsynBackEnv/Scripts/activate` on Windows).
2. Install requirements: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Start the server: `python manage.py runserver`
