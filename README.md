# User Authentication API

This is a FastAPI-based authentication API with MySQL database integration. It provides endpoints for user registration and login with JWT token authentication.

## Setup

1. Create a MySQL database named `registration_db`:

```sql
CREATE DATABASE registration_db;
```

2. Install Poetry (if you haven't already):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install the project dependencies using Poetry:

```bash
poetry install
```

4. Update the database connection string in `database.py` with your MySQL credentials:

```python
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://username:password@localhost/registration_db"
```

5. Update the `SECRET_KEY` in `main.py` with a secure secret key.

## Running the Application

Start the server with:

```bash
poetry run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Register a new user

- **POST** `/register`
- Body:

```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123"
}
```

### Login

- **POST** `/token`
- Form data:
  - username: your_username
  - password: your_password
- Returns JWT access token

### Get current user info

- **GET** `/users/me`
- Requires Authorization header with Bearer token

## API Documentation

Once the server is running, you can access:

- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`
