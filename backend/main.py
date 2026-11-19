from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .db import engine
from .routers import ALL_ROUTERS

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(engine)
    yield


app = FastAPI(title='Service Desk API', version='1.0.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

for router in ALL_ROUTERS:
    app.include_router(router)


@app.get('/api/health')
def health():
    return {'status': 'ok'}
