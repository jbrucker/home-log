## Backend for REST Service

The backend contains code for a REST Service that performs application logic and supplies/receives data to/from the front-end.


Test:
```
uvicorn app.main:app --reload
```
- use a REST tool to access `/user/` endpoints.
- access OpenAPI documentation

## VS Code Configuration

On my Linux machine I added this to `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/env/bin/python",
    "python.terminal.activateEnvInCurrentTerminal": true,
    "terminal.integrated.env.linux": { "PYTHONPATH": "${workspaceFolder}" }
}
```

without setting `PYTHONPATH` I was getting module not found errors for `app`, even though it has a `__init__.py` file.
