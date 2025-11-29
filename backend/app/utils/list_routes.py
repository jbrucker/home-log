"""List all the routes in app."""

from app.main import app

for route in app.routes:
    methods = ",".join(route.methods or [])
    print(f"{methods:10s} {route.path}")
