from app.routers.admin import router as admin_router
from app.routers.cart import router as cart_router
from app.routers.categories import router as categories_router
from app.routers.orders import router as orders_router
from app.routers.products import router as products_router
from app.routers.promo import router as promo_router

__all__ = [
    "admin_router",
    "cart_router",
    "categories_router",
    "orders_router",
    "products_router",
    "promo_router",
]
