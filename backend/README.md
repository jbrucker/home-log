## Backend for REST Service

The backend contains code for a REST Service that performs application logic and supplies/receives data to/from the front-end.


## Run a Local Test Server

```
. ./bin/activate
uvicorn app.main:app --reload
```
Or invoke the `runserver.sh` script.

- starts a server listening at <http://localhost:8000>
- access OpenAPI documentation at `/docs` (<http://localhost:8000/docs>)
- or use a REST tool to access endpoints

### Test Accounts

When using the REST API (e.g. `http://localhost:8000/docs`), the **login** name is the **email address** not the username.

| username | email            | password | id (maybe) |
|----------|------------------|----------|------------|
| Jim      |jim@hackers.com   | Hackme2  | 1          |
| Harry    |harry@hackers.com | Hackme2  | 2          |
| Sally    |sally@hackers.com | Hackme2  | 3          |
| admin    |admin@localhost.com | MakeMyDay | 7       |
| Barrack  |obama@whitehouse.gov| ?         | 8       |


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
The "terminal.integrated.env.linux" setting is needed on my machine to avoid Python package not found errors for anything the `app` package (even though it has a `__init__.py` file).
without setting `PYTHONPATH` I was getting module not found errors for `app`, even though it has a `__init__.py` file.

---

### How to Run

### Prerequisite: Start Database Server

This app normally uses Postgresql. To start the server in a container, at the top level directory enter:
```bash
docker compose up -d db
# verify it is running. Output should show "homelog-db-1" process.
docker compose ps
```

(Optional, 1 time) Initialize the database with Alembic:
```bash
alembic upgrade head
```

### Start the REST API server

1. Start FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
   
2. Access the docs:
   - OpenAPI: `http://localhost:8000/docs`
   - Redoc: `http://localhost:8000/redoc`

3. Get a user (assuming database contains some user data):
   ```
   curl http://localhost:8000/users/1
   ```
   should display JSON for user with id 1.


---


## Mypy

`pip install mypy` installed 3 packages:
- `mypy-1.17.0` 
- `mypy_extensions-1.1.0` 
- `pathspec-0.12.1`

