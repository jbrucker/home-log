from fastapi import FastAPI, Depends, HTTPException, create_engine, Session, sessionmaker

# values from other experiments
from app.schemas.schemas import UserOut
from experiments.core import init_engine 

engine = init_engine()  # from core

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

app = FastAPI()

# Dependency injection
@app.post("/users/", response_model=UserOut)

if __name__ == '__main__':
    pass