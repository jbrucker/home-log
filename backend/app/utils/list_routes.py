"""List all the routes in app."""

from app.main import app

sorted_routes = sorted(app.routes, key=lambda route: route.path)
for route in sorted_routes:
    methods = ",".join(route.methods or [])
    print(f"{methods:10s} {route.path}")
