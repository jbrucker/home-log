"""Simple example to test the order in which middleware is invoked.

According to the FastAPI and Starlette documentation, each middleware
wraps the previous request, so the invocation order should be:

For Request:  in **reverse order** they are added in code.
For Response:  in **same order** they are added in code.

To use:  run the app using Python.
         use a browser or curl to visit http://localhost:8000/
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.middleware("http")
async def A(request, call_next):
    print("A: before")
    response = await call_next(request)
    print("A: after")
    return response

@app.middleware("http")
async def B(request, call_next):
    print("B: before")
    response = await call_next(request)
    print("B: after")
    return response

@app.middleware("http")
async def C(request, call_next):
    print("C: before")
    response = await call_next(request)
    print("C: after")
    return response

@app.get("/")
async def root():
    print("route handler for /")
    return {"msg": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

