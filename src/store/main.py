import uvicorn
import sys
from fastapi import FastAPI

# Исправление путей, для поиска модулей
if "src" not in sys.path:
    sys.path.insert(0, "src")
if "." not in sys.path:
    sys.path.insert(0, ".")

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

if __name__ == "__main__":
    uvicorn.run("store.main:app", port=8080, reload=True)
