"""Database seed script — idempotent, safe to run on every deploy."""
from __future__ import annotations
import asyncio

PRODUCTS: list[dict] = [
  {"id":"prod-001","brand":"ZARA","name":"Платье миди с цветочным принтом","category":"women","subcategory":"dresses","price":4990,"priceOriginal":7990,"discountPercent":38,"images":["https://placehold.co/400x533/eeeeee/5e5e5e?text=ZARA+1","https://placehold.co/400x533/e8e8e8/5e5e5e?text=ZARA+2","https://placehold.co/400x533/f3f3f3/5e5e5e?text=ZARA+3","https://placehold.co/400x533/dadada/5e5e5e?text=ZARA+4"],"sizes":[{"label":"XS","available":True},{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True},{"label":"XXL","available":False}],"colors":[{"label":"Чёрный","hex":"#000000"},{"label":"Белый","hex":"#FFFFFF"},{"label":"Бежевый","hex":"#E5DCC4"},{"label":"Синий","hex":"#0A192F"}],"rating":4.2,"reviewCount":128,"description":"Элегантное платье миди с нежным цветочным принтом.","inStock":True},
  {"id":"prod-002","brand":"MANGO","name":"Платье миди с драпировкой","category":"women","subcategory":"dresses","price":4990,"priceOriginal":7990,"discountPercent":38,"images":["https://placehold.co/400x533/eeeeee/5e5e5e?text=MANGO+1","https://placehold.co/400x533/e8e8e8/5e5e5e?text=MANGO+2"],"sizes":[{"label":"XS","available":True},{"label":"S","available":True},{"label":"M","available":False},{"label":"L","available":True},{"label":"XL","available":False}],"colors":[{"label":"Бежевый","hex":"#C4A882"},{"label":"Чёрный","hex":"#000000"}],"rating":4.5,"reviewCount":87,"description":"Изысканное платье с мягкой драпировкой по талии.","inStock":True},
  {"id":"prod-003","brand":"ZARA","name":"Блузка из хлопка с объёмными рукавами","category":"women","subcategory":"blouses","price":3599,"images":["https://placehold.co/400x533/f3f3f3/5e5e5e?text=ZARA+Blouse"],"sizes":[{"label":"XS","available":True},{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True}],"colors":[{"label":"Белый","hex":"#FFFFFF"},{"label":"Голубой","hex":"#A8C8E8"}],"rating":4.0,"reviewCount":44,"description":"Лёгкая хлопковая блузка с романтичными объёмными рукавами.","inStock":True},
  {"id":"prod-004","brand":"LEVI'S","name":"Джинсы прямого кроя 501","category":"women","subcategory":"jeans","price":8990,"priceOriginal":11290,"discountPercent":20,"images":["https://placehold.co/400x533/eeeeee/5e5e5e?text=LEVIS+501","https://placehold.co/400x533/e8e8e8/5e5e5e?text=LEVIS+501+2"],"sizes":[{"label":"XS","available":False},{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True}],"colors":[{"label":"Синий","hex":"#3B5998"},{"label":"Чёрный","hex":"#000000"}],"rating":4.7,"reviewCount":312,"description":"Культовые джинсы прямого кроя с высокой посадкой.","inStock":True},
  {"id":"prod-005","brand":"MASSIMO DUTTI","name":"Кожаная куртка-косуха","category":"women","subcategory":"jackets","price":24990,"images":["https://placehold.co/400x533/1a1c1c/ffffff?text=MASSIMO+DUTTI"],"sizes":[{"label":"XS","available":True},{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":False},{"label":"XL","available":False}],"colors":[{"label":"Чёрный","hex":"#000000"},{"label":"Коричневый","hex":"#5C3A1E"}],"rating":4.8,"reviewCount":56,"description":"Классическая кожаная косуха из натуральной кожи.","inStock":True},
  {"id":"prod-006","brand":"VAGABOND","name":"Кожаные туфли-лодочки","category":"women","subcategory":"shoes","price":7640,"priceOriginal":8990,"discountPercent":15,"images":["https://placehold.co/400x533/f3f3f3/5e5e5e?text=VAGABOND"],"sizes":[{"label":"36","available":True},{"label":"37","available":True},{"label":"38","available":True},{"label":"39","available":False},{"label":"40","available":True}],"colors":[{"label":"Чёрный","hex":"#000000"},{"label":"Бежевый","hex":"#C9B18A"}],"rating":4.3,"reviewCount":91,"description":"Элегантные туфли-лодочки из натуральной кожи на каблуке 7 см.","inStock":True},
  {"id":"prod-007","brand":"H&M","name":"Льняное платье макси","category":"women","subcategory":"dresses","price":3299,"images":["https://placehold.co/400x533/e8e8e8/5e5e5e?text=H%26M+Linen"],"sizes":[{"label":"XS","available":True},{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True},{"label":"XXL","available":True}],"colors":[{"label":"Натуральный","hex":"#D4C5A9"},{"label":"Белый","hex":"#FFFFFF"},{"label":"Оливковый","hex":"#6B7C45"}],"rating":3.9,"reviewCount":203,"description":"Воздушное платье макси из 100% льна.","inStock":True},
  {"id":"prod-008","brand":"TOMMY HILFIGER","name":"Рубашка в полоску","category":"men","subcategory":"shirts","price":5490,"priceOriginal":7290,"discountPercent":25,"images":["https://placehold.co/400x533/eeeeee/5e5e5e?text=TOMMY+H"],"sizes":[{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True},{"label":"XXL","available":False}],"colors":[{"label":"Синий/Белый","hex":"#1E3A8A"},{"label":"Красный/Белый","hex":"#B91C1C"}],"rating":4.4,"reviewCount":167,"description":"Классическая рубашка в полоску из хлопкового поплина.","inStock":True},
  {"id":"prod-009","brand":"LEVI'S","name":"Джинсы 512 Slim Taper","category":"men","subcategory":"jeans","price":9990,"images":["https://placehold.co/400x533/3B5998/ffffff?text=LEVIS+512"],"sizes":[{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True}],"colors":[{"label":"Тёмно-синий","hex":"#1E2D5A"},{"label":"Серый","hex":"#6B6B6B"}],"rating":4.6,"reviewCount":289,"description":"Современные джинсы зауженного кроя с конической брючиной.","inStock":True},
  {"id":"prod-010","brand":"POLO RALPH LAUREN","name":"Поло из хлопка","category":"men","subcategory":"polo","price":6990,"priceOriginal":9990,"discountPercent":30,"images":["https://placehold.co/400x533/f3f3f3/5e5e5e?text=POLO+RL"],"sizes":[{"label":"S","available":False},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True},{"label":"XXL","available":True}],"colors":[{"label":"Белый","hex":"#FFFFFF"},{"label":"Тёмно-синий","hex":"#0A1628"},{"label":"Красный","hex":"#C41E3A"}],"rating":4.5,"reviewCount":134,"description":"Классическое поло из плотного хлопкового пике.","inStock":True},
  {"id":"prod-011","brand":"NIKE","name":"Кроссовки Air Max 270","category":"men","subcategory":"shoes","price":11990,"images":["https://placehold.co/400x533/1a1c1c/ffffff?text=NIKE+AM270"],"sizes":[{"label":"40","available":True},{"label":"41","available":True},{"label":"42","available":True},{"label":"43","available":True},{"label":"44","available":False},{"label":"45","available":True}],"colors":[{"label":"Чёрный/Белый","hex":"#000000"},{"label":"Серый","hex":"#808080"}],"rating":4.7,"reviewCount":445,"description":"Инновационные кроссовки с крупной воздушной подушкой Max Air.","inStock":True},
  {"id":"prod-012","brand":"ZARA KIDS","name":"Джинсовый комбинезон","category":"kids","subcategory":"overalls","price":2490,"priceOriginal":3490,"discountPercent":29,"images":["https://placehold.co/400x533/A8C8E8/1a1c1c?text=ZARA+KIDS"],"sizes":[{"label":"86","available":True},{"label":"92","available":True},{"label":"98","available":True},{"label":"104","available":True},{"label":"110","available":False}],"colors":[{"label":"Синий","hex":"#4A90D9"}],"rating":4.3,"reviewCount":67,"description":"Удобный джинсовый комбинезон для активных детей.","inStock":True},
  {"id":"prod-013","brand":"H&M KIDS","name":"Платье в горошек","category":"kids","subcategory":"dresses","price":1599,"images":["https://placehold.co/400x533/FFD6E0/1a1c1c?text=HM+KIDS"],"sizes":[{"label":"86","available":True},{"label":"92","available":True},{"label":"98","available":True},{"label":"104","available":True},{"label":"110","available":True},{"label":"116","available":False}],"colors":[{"label":"Розовый","hex":"#FFB6C1"},{"label":"Красный","hex":"#CC0000"}],"rating":4.1,"reviewCount":43,"description":"Яркое платье в горошек из мягкого хлопка.","inStock":True},
  {"id":"prod-014","brand":"ADIDAS KIDS","name":"Спортивный костюм","category":"kids","subcategory":"sport","price":3990,"priceOriginal":5490,"discountPercent":27,"images":["https://placehold.co/400x533/000000/ffffff?text=ADIDAS+KIDS"],"sizes":[{"label":"92","available":True},{"label":"98","available":True},{"label":"104","available":True},{"label":"110","available":True},{"label":"116","available":True}],"colors":[{"label":"Чёрный","hex":"#000000"},{"label":"Тёмно-синий","hex":"#003087"}],"rating":4.4,"reviewCount":89,"description":"Удобный спортивный костюм Adidas для детей.","inStock":True},
  {"id":"prod-015","brand":"ADIDAS","name":"Леггинсы для тренировок Techfit","category":"sport","subcategory":"leggings","price":3490,"priceOriginal":4990,"discountPercent":30,"images":["https://placehold.co/400x533/1a1c1c/ffffff?text=ADIDAS+Techfit"],"sizes":[{"label":"XS","available":True},{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":False}],"colors":[{"label":"Чёрный","hex":"#000000"},{"label":"Серый","hex":"#808080"}],"rating":4.6,"reviewCount":234,"description":"Компрессионные леггинсы для интенсивных тренировок.","inStock":True},
  {"id":"prod-016","brand":"NIKE","name":"Футболка Dri-FIT","category":"sport","subcategory":"tshirts","price":2990,"images":["https://placehold.co/400x533/eeeeee/5e5e5e?text=NIKE+DRI-FIT"],"sizes":[{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True},{"label":"XXL","available":True}],"colors":[{"label":"Белый","hex":"#FFFFFF"},{"label":"Чёрный","hex":"#000000"},{"label":"Серый","hex":"#808080"}],"rating":4.5,"reviewCount":178,"description":"Функциональная футболка с технологией Dri-FIT.","inStock":True},
  {"id":"prod-017","brand":"UNDER ARMOUR","name":"Спортивная куртка Storm","category":"sport","subcategory":"jackets","price":8990,"priceOriginal":12990,"discountPercent":31,"images":["https://placehold.co/400x533/1a1c1c/ffffff?text=UA+STORM"],"sizes":[{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":False},{"label":"XXL","available":False}],"colors":[{"label":"Чёрный","hex":"#000000"},{"label":"Тёмно-серый","hex":"#3C3C3C"}],"rating":4.7,"reviewCount":98,"description":"Водоотталкивающая спортивная куртка для тренировок на открытом воздухе.","inStock":True},
  {"id":"prod-018","brand":"COS","name":"Широкие брюки из шерсти","category":"women","subcategory":"pants","price":12490,"images":["https://placehold.co/400x533/e8e8e8/5e5e5e?text=COS+Pants"],"sizes":[{"label":"XS","available":True},{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True}],"colors":[{"label":"Чёрный","hex":"#000000"},{"label":"Бежевый","hex":"#C4B49A"},{"label":"Серый","hex":"#808080"}],"rating":4.4,"reviewCount":62,"description":"Широкие брюки из смесовой шерсти с высокой посадкой.","inStock":True},
  {"id":"prod-019","brand":"ARKET","name":"Льняная рубашка оверсайз","category":"men","subcategory":"shirts","price":7990,"priceOriginal":10990,"discountPercent":27,"images":["https://placehold.co/400x533/f3f3f3/5e5e5e?text=ARKET+Shirt"],"sizes":[{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True},{"label":"XXL","available":True}],"colors":[{"label":"Белый","hex":"#FFFFFF"},{"label":"Голубой","hex":"#87CEEB"},{"label":"Оливковый","hex":"#6B7C45"}],"rating":4.3,"reviewCount":48,"description":"Рубашка оверсайз из 100% льна.","inStock":True},
  {"id":"prod-020","brand":"NEW BALANCE","name":"Кроссовки 574 Classic","category":"sport","subcategory":"shoes","price":8490,"images":["https://placehold.co/400x533/eeeeee/5e5e5e?text=NB+574"],"sizes":[{"label":"38","available":True},{"label":"39","available":True},{"label":"40","available":True},{"label":"41","available":True},{"label":"42","available":True},{"label":"43","available":False},{"label":"44","available":True}],"colors":[{"label":"Серый/Синий","hex":"#808080"},{"label":"Чёрный/Белый","hex":"#000000"}],"rating":4.6,"reviewCount":367,"description":"Культовые кроссовки New Balance 574.","inStock":True},
  {"id":"prod-021","brand":"GAP KIDS","name":"Худи с карманом кенгуру","category":"kids","subcategory":"hoodies","price":2190,"priceOriginal":2990,"discountPercent":27,"images":["https://placehold.co/400x533/eeeeee/5e5e5e?text=GAP+KIDS"],"sizes":[{"label":"92","available":True},{"label":"98","available":True},{"label":"104","available":True},{"label":"110","available":True},{"label":"116","available":True},{"label":"122","available":False}],"colors":[{"label":"Серый","hex":"#A0A0A0"},{"label":"Синий","hex":"#4A90D9"},{"label":"Красный","hex":"#CC0000"}],"rating":4.2,"reviewCount":55,"description":"Тёплое худи из мягкого флиса с удобным карманом-кенгуру.","inStock":True},
  {"id":"prod-022","brand":"SAINT LAURENT","name":"Пиджак Classic","category":"men","subcategory":"jackets","price":124000,"images":["https://placehold.co/400x533/1a1c1c/ffffff?text=YSL+Jacket"],"sizes":[{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":False},{"label":"XL","available":False}],"colors":[{"label":"Чёрный","hex":"#000000"}],"rating":4.9,"reviewCount":12,"description":"Культовый пиджак из тонкой шерсти Saint Laurent Paris.","inStock":True},
  {"id":"prod-023","brand":"ADIDAS","name":"Шорты Essentials","category":"sport","subcategory":"shorts","price":2490,"images":["https://placehold.co/400x533/000000/ffffff?text=ADIDAS+Shorts"],"sizes":[{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":True},{"label":"XXL","available":True}],"colors":[{"label":"Чёрный","hex":"#000000"},{"label":"Серый","hex":"#808080"},{"label":"Тёмно-синий","hex":"#003087"}],"rating":4.3,"reviewCount":156,"description":"Классические шорты Adidas из лёгкого трикотажа.","inStock":True},
  {"id":"prod-024","brand":"CALVIN KLEIN","name":"Кашемировый свитер","category":"women","subcategory":"knitwear","price":14990,"priceOriginal":19990,"discountPercent":25,"images":["https://placehold.co/400x533/e8e8e8/5e5e5e?text=CK+Cashmere"],"sizes":[{"label":"XS","available":True},{"label":"S","available":True},{"label":"M","available":True},{"label":"L","available":True},{"label":"XL","available":False}],"colors":[{"label":"Бежевый","hex":"#C4B49A"},{"label":"Чёрный","hex":"#000000"},{"label":"Белый","hex":"#FFFFFF"}],"rating":4.8,"reviewCount":73,"description":"Мягкий свитер из чистого кашемира с круглым вырезом.","inStock":True},
]

CATEGORIES: list[dict] = [
  {"id":"women","label":"Женщинам","icon":"female","subcategories":[{"id":"dresses","label":"Платья"},{"id":"blouses","label":"Блузки"},{"id":"jeans","label":"Джинсы"},{"id":"jackets","label":"Куртки"},{"id":"shoes","label":"Обувь"},{"id":"pants","label":"Брюки"},{"id":"knitwear","label":"Трикотаж"}]},
  {"id":"men","label":"Мужчинам","icon":"male","subcategories":[{"id":"shirts","label":"Рубашки"},{"id":"jeans","label":"Джинсы"},{"id":"polo","label":"Поло"},{"id":"jackets","label":"Пиджаки"},{"id":"shoes","label":"Кроссовки"}]},
  {"id":"kids","label":"Детям","icon":"child_care","subcategories":[{"id":"dresses","label":"Платья"},{"id":"overalls","label":"Комбинезоны"},{"id":"sport","label":"Спорт"},{"id":"hoodies","label":"Худи"}]},
  {"id":"sport","label":"Спорт","icon":"sports_basketball","subcategories":[{"id":"leggings","label":"Леггинсы"},{"id":"tshirts","label":"Футболки"},{"id":"jackets","label":"Куртки"},{"id":"shoes","label":"Кроссовки"},{"id":"shorts","label":"Шорты"}]},
]


async def seed() -> None:
    from app.database import async_session_factory, engine, Base
    import app.models  # noqa: F401

    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Products
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100)"))
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS price_original INTEGER"))
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS discount_percent INTEGER"))
        # Orders — address + contact fields
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(200)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS email VARCHAR(200)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS city VARCHAR(200)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS street VARCHAR(300)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS building VARCHAR(50)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS apartment VARCHAR(50)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS zip_code VARCHAR(20)"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS comment TEXT"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS promo_discount INTEGER NOT NULL DEFAULT 0"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS promo_code VARCHAR(50)"))

    from app.models.product import Product
    from app.models.category import Category
    from app.models.promo import PromoCode

    async with async_session_factory() as session:
        for cat in CATEGORIES:
            existing = await session.get(Category, cat["id"])
            if existing is None:
                c = Category(id=cat["id"], label=cat["label"], icon=cat["icon"])
                c.subcategories = cat.get("subcategories", [])
                session.add(c)

        for raw in PRODUCTS:
            existing = await session.get(Product, raw["id"])
            if existing is None:
                p = Product(
                    id=raw["id"], brand=raw["brand"], name=raw["name"],
                    category=raw["category"], subcategory=raw["subcategory"],
                    price=raw["price"], price_original=raw.get("priceOriginal"),
                    discount_percent=raw.get("discountPercent"),
                    rating=raw.get("rating", 0.0), review_count=raw.get("reviewCount", 0),
                    description=raw.get("description"), in_stock=raw.get("inStock", True),
                )
                p.images = raw.get("images", [])
                p.sizes = raw.get("sizes", [])
                p.colors = raw.get("colors", [])
                session.add(p)

        for code, pct, amt in [("DOMMODA10", 10, None), ("FIRST500", None, 500)]:
            if await session.get(PromoCode, code) is None:
                session.add(PromoCode(code=code, discount_percent=pct, discount_amount=amt, is_active=True))

        await session.commit()

    print(f"Seed complete: {len(PRODUCTS)} products, {len(CATEGORIES)} categories, 2 promo codes")


if __name__ == "__main__":
    asyncio.run(seed())
