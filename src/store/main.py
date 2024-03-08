from fastapi import FastAPI
from store.resources import router


def get_app():
    app = FastAPI()

    app.include_router(router)

    return app


app = get_app()