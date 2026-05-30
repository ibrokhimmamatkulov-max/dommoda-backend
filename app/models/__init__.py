"""SQLAlchemy ORM models.

Import all models here so that Alembic's env.py can discover them via
``app.database.Base.metadata`` without chasing individual module imports.
"""

from app.models.category import Category
from app.models.order import Order, OrderStatus, DeliveryMethod
from app.models.product import Product
from app.models.promo import PromoCode
from app.models.setting import SiteSetting
from app.models.analytics import AnalyticsEvent
from app.models.user import User

__all__ = [
    "Category",
    "Order",
    "OrderStatus",
    "DeliveryMethod",
    "Product",
    "PromoCode",
    "SiteSetting",
]
