from __future__ import annotations
import httpx
from app.config import settings


async def send_telegram(text: str) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={"chat_id": settings.telegram_chat_id, "text": text, "parse_mode": "Markdown"},
            )
    except Exception:
        pass


async def send_order_notification(order) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    delivery_labels = {"courier": "Курьер", "pickup": "Самовывоз", "post": "Почта"}
    delivery = delivery_labels.get(str(order.delivery_method.value if hasattr(order.delivery_method, 'value') else order.delivery_method), str(order.delivery_method))

    def _item_line(item: dict) -> str:
        sku = item.get("sku")
        sku_str = f" `{sku}`" if sku else ""
        return (
            f"  • {item['brand']} {item['product_name']}{sku_str}\n"
            f"    {item['size']} · {item['color']} · ×{item['quantity']} — {item['unit_price'] * item['quantity']:,} ₽"
        )

    items_text = "\n".join(_item_line(item) for item in order.items)

    text = (
        f"🛍 *Новый заказ {order.id}*\n\n"
        f"👤 {order.recipient_name}\n"
        f"📞 {order.phone}\n"
        f"📧 {order.email}\n\n"
        f"🚚 Доставка: {delivery}\n"
        f"📍 {order.city}, {order.street}, д. {order.building}"
        + (f", кв. {order.apartment}" if order.apartment else "") + "\n\n"
        f"*Состав заказа:*\n{items_text}\n\n"
        + (f"🏷 Промокод: {order.promo_code} (-{order.promo_discount:,} ₽)\n" if order.promo_code else "")
        + f"💰 *Итого: {order.total:,} ₽*"
    )

    await send_telegram(text)
