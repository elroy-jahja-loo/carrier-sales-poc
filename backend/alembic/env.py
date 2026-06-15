from __future__ import annotations

from logging.config import fileConfig

from alembic import context as alembic_context  # type: ignore[attr-defined]
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.database import Base, get_sqlalchemy_database_url
from app import models  # noqa: F401


config = alembic_context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", get_sqlalchemy_database_url(settings.database_url))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    alembic_context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with alembic_context.begin_transaction():
        alembic_context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        alembic_context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with alembic_context.begin_transaction():
            alembic_context.run_migrations()


if alembic_context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
