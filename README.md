# Dommoda Backend API

FastAPI backend for the Dommoda fashion e-commerce platform.

## Stack

| Technology | Purpose |
|---|---|
| Python 3.12+ | Runtime |
| FastAPI 0.115 | Async REST API |
| SQLAlchemy 2.0 (async) | ORM |
| SQLite + aiosqlite | Database (zero-setup) |
| Alembic | Schema migrations |
| Pydantic v2 | Validation & schemas |

---

## Quick Start

### 1. Create and activate a virtual environment

```bash
cd C:\Users\User\Desktop\dommoda-backend

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Seed the database

```bash
python seed.py
```

This creates `dommoda.db` and populates it with:
- 24 products from the frontend `products.json`
- 4 categories from the frontend `categories.json`
- 2 promo codes: `DOMMODA10` (10% off), `FIRST500` (500 flat discount)

### 4. Start the development server

```bash
uvicorn main:app --reload
```

The API is now running at **http://127.0.0.1:8000**

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

---

## API Endpoints

### Products

| Method | Path | Description |
|---|---|---|
| GET | `/api/products` | List products (filters: `category`, `subcategory`, `sort`, `page`, `limit`) |
| GET | `/api/products/featured` | Top 4 products for homepage |
| GET | `/api/products/{id}` | Single product detail |

**Query parameters for `GET /api/products`:**

| Param | Type | Default | Values |
|---|---|---|---|
| `category` | string | — | `women`, `men`, `kids`, `sport` |
| `subcategory` | string | — | e.g. `dresses`, `jeans`, `shoes` |
| `sort` | string | `popular` | `popular`, `price_asc`, `price_desc`, `new` |
| `page` | int | `1` | >= 1 |
| `limit` | int | `24` | 1–100 |

### Categories

| Method | Path | Description |
|---|---|---|
| GET | `/api/categories` | All categories with subcategories |

### Cart

| Method | Path | Description |
|---|---|---|
| POST | `/api/cart/validate` | Validate cart items before checkout |

### Orders

| Method | Path | Description |
|---|---|---|
| POST | `/api/orders` | Create a new order |
| GET | `/api/orders/{id}` | Get order status |

### Promo Codes

| Method | Path | Description |
|---|---|---|
| POST | `/api/promo/validate` | Validate a promo code |

---

## Migrations (Alembic)

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after changing models
alembic revision --autogenerate -m "describe_your_change"

# Roll back one step
alembic downgrade -1
```

---

## Project Structure

```
dommoda-backend/
├── main.py                  # FastAPI app factory + lifespan
├── requirements.txt
├── seed.py                  # Database seeder
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
└── app/
    ├── config.py            # Settings (pydantic-settings, reads .env)
    ├── database.py          # Async engine, session factory, Base
    ├── models/
    │   ├── product.py
    │   ├── category.py
    │   ├── order.py
    │   └── promo.py
    ├── schemas/
    │   ├── product.py
    │   ├── category.py
    │   ├── order.py
    │   └── promo.py
    └── routers/
        ├── products.py
        ├── categories.py
        ├── cart.py
        ├── orders.py
        └── promo.py
```

---

## Environment Variables

Copy `.env.example` to `.env` to override defaults:

```
DATABASE_URL=sqlite+aiosqlite:///./dommoda.db
CORS_ORIGINS=["http://localhost:3000"]
DEBUG=false
```

---

## Connecting the Frontend

The frontend at `http://localhost:3000` is already configured in CORS.

To switch the frontend from mock data to the real API, update
`src/lib/api.ts` to call `http://localhost:8000/api/...` instead of
reading from the local JSON files.
