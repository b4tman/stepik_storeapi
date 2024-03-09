from fastapi import FastAPI
from store.routes.items import router as router_items
from store.routes.cart import router as router_cart
from store.routes.order import router as router_order


def get_app():
    """Создание приложения"""

    app = FastAPI(title="API магазина")
    app.include_router(router_items)
    app.include_router(router_cart)
    app.include_router(router_order)
    return app


app = get_app()
