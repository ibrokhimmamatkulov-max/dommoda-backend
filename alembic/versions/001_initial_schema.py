"""initial_schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- categories ---
    op.create_table(
        "categories",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("icon", sa.String(100), nullable=False),
        sa.Column("subcategories_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_categories_id", "categories", ["id"])

    # --- products ---
    op.create_table(
        "products",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("brand", sa.String(200), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subcategory", sa.String(50), nullable=False),
        sa.Column("price", sa.Integer, nullable=False),
        sa.Column("price_original", sa.Integer, nullable=True),
        sa.Column("discount_percent", sa.Integer, nullable=True),
        sa.Column("images_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("sizes_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("colors_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("rating", sa.Float, nullable=False, server_default="0"),
        sa.Column("review_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("in_stock", sa.Boolean, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index(
        "ix_products_category_subcategory", "products", ["category", "subcategory"]
    )
    op.create_index("ix_products_in_stock", "products", ["in_stock"])
    op.create_index("ix_products_review_count", "products", ["review_count"])

    # --- orders ---
    op.create_table(
        "orders",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("delivery_method", sa.String(20), nullable=False),
        sa.Column("recipient_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("city", sa.String(200), nullable=False),
        sa.Column("street", sa.String(300), nullable=False),
        sa.Column("building", sa.String(50), nullable=False),
        sa.Column("apartment", sa.String(50), nullable=True),
        sa.Column("zip_code", sa.String(20), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("subtotal", sa.Integer, nullable=False),
        sa.Column("promo_discount", sa.Integer, nullable=False, server_default="0"),
        sa.Column("promo_code", sa.String(50), nullable=True),
        sa.Column("total", sa.Integer, nullable=False),
        sa.Column("items_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    # --- promo_codes ---
    op.create_table(
        "promo_codes",
        sa.Column("code", sa.String(50), primary_key=True),
        sa.Column("discount_percent", sa.Integer, nullable=True),
        sa.Column("discount_amount", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("promo_codes")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_products_review_count", table_name="products")
    op.drop_index("ix_products_in_stock", table_name="products")
    op.drop_index("ix_products_category_subcategory", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_id", table_name="categories")
    op.drop_table("categories")
