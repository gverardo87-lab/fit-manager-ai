"""
Alembic env.py per nutrition.db — catalogo alimenti CREA/USDA.

Gestisce migrazioni separate dal business DB (crm.db).
Filtra solo le tabelle di nutrition.db per autogenerate.

Uso:
  alembic -c alembic_nutrition.ini upgrade head
  alembic -c alembic_nutrition.ini revision --autogenerate -m "descrizione"
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Root del progetto nel path per importare api.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.models.nutrition  # noqa: F401 — registra modelli nutrition
from sqlmodel import SQLModel
from api.database import NUTRITION_TABLE_NAMES

# Alembic Config object
config = context.config

# Override URL da env se presente
database_url = os.getenv("NUTRITION_DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData per autogenerate — filtrato alle sole tabelle nutrition
target_metadata = SQLModel.metadata


def include_name(name, type_, parent_names):
    """Filtra: includi solo tabelle di nutrition.db."""
    if type_ == "table":
        return name in NUTRITION_TABLE_NAMES
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite: ALTER TABLE via batch
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
