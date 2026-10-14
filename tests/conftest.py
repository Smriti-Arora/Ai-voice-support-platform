import os
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text, bindparam

project_root = Path(__file__).resolve().parent.parent
test_env_file = project_root / ".env.test"
test_config = dotenv_values(test_env_file)
test_database_url = test_config.get("DATABASE_URL", "")

if not test_database_url:
    raise RuntimeError("DATABASE_URL is missing from .env.test")

if not test_database_url.endswith("/ai_voice_support_test"):
    raise RuntimeError("Tests must use the ai_voice_support_test database.")

os.environ["DATABASE_URL"] = test_database_url


@pytest.fixture(autouse=True)
def cleanup_test_data():
    engine = create_engine(test_database_url)

    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar()

        if database_name != "ai_voice_support_test":
            engine.dispose()
            raise RuntimeError("Refusing to clean a non-test database")

        existing_ticket_ids = set(
            connection.execute(
                text("SELECT id FROM support_tickets")
            ).scalars().all()
        )

        existing_user_ids = set(
            connection.execute(
                text("SELECT id FROM users")
            ).scalars().all()
        )

    try:
        yield
    finally:
        with engine.begin() as connection:
            if existing_ticket_ids:
                connection.execute(
                    text(
                        "DELETE FROM support_tickets "
                        "WHERE id NOT IN :ids"
                    ).bindparams(bindparam("ids", expanding=True)),
                    {"ids": list(existing_ticket_ids)},
                )
            else:
                connection.execute(text("DELETE FROM support_tickets"))

            if existing_user_ids:
                connection.execute(
                    text(
                        "DELETE FROM users WHERE id NOT IN :ids"
                    ).bindparams(bindparam("ids", expanding=True)),
                    {"ids": list(existing_user_ids)},
                )
            else:
                connection.execute(text("DELETE FROM users"))

        engine.dispose()
