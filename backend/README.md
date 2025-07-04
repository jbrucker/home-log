## Backend for REST Service

The backend contains code for a REST Service that performs application logic and supplies/receives data to/from the front-end.


Test:
```
uvicorn app.main:app --reload
```
- use a REST tool to access `/user/` endpoints.
- access OpenAPI documentation

Test Accounts

| username | email            | password |
|----------|------------------|----------|
| Jim      |jim@hackers.com   | hackme2  |
| Harry    |harry@hackers.com | hackme2  | 
| Sally    |sally@hackers.com | hackme2  |

## VS Code Configuration

On my Linux machine I added this to `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/env/bin/python",
    "python.terminal.activateEnvInCurrentTerminal": true,
    "terminal.integrated.env.linux": { "PYTHONPATH": "${workspaceFolder}" }
    // Don't show __pycache__ or .pytest_cache folders in Explorer view
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true
    }
}
```

without setting `PYTHONPATH` I was getting module not found errors for `app`, even though it has a `__init__.py` file.

---

### How to Run

1. (Optional) Initialize the database with Alembic:
   ```bash
   alembic upgrade head
   ```

2. Start FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Get a user (assuming database has some seed data):
   ```
   curl http://localhost:8000/users/1
   ```
   should display JSON for user with id 1.
   
3. Access docs:
   - OpenAPI: `http://localhost:8000/docs`
   - Redoc: `http://localhost:8000/redoc`
