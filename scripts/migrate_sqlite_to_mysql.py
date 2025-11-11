import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

# Ensure project root is on the Python path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from models import (
    db,
    User,
    Customer,
    Service,
    Staff,
    Appointment,
    AppointmentService,
    Transaction,
    LoyaltyHistory,
    Attendance,
    Promotion,
    CampaignStats,
    WhatsAppConversation,
)


def get_sqlite_url() -> str:
    """Build the SQLite connection string."""
    if url := os.environ.get("SQLITE_URL"):
        return url

    base_dir = Path(__file__).resolve().parent.parent
    default_db_path = base_dir / "instance" / "salon.db"
    if not default_db_path.exists():
        default_db_path = base_dir / "salon.db"
    return f"sqlite:///{default_db_path}"


def get_mysql_url() -> str:
    """Read the MySQL connection string, reusing the Flask config."""
    url = os.environ.get("TARGET_DATABASE_URL") or Config.SQLALCHEMY_DATABASE_URI
    if not url or url.startswith("sqlite"):
        raise RuntimeError(
            "TARGET_DATABASE_URL (or DATABASE_URL) must point to your MySQL database."
        )
    return url


def copy_table(source_session, target_connection, model):
    """Copy rows for a single model, preserving primary keys."""
    rows = source_session.execute(select(model)).scalars().all()
    if not rows:
        return 0

    payload = []
    for row in rows:
        data = {}
        for column in model.__table__.columns:
            data[column.name] = getattr(row, column.name)
        payload.append(data)

    target_connection.execute(model.__table__.insert(), payload)
    return len(payload)


def main():
    sqlite_url = get_sqlite_url()
    mysql_url = get_mysql_url()

    print(f"Source (SQLite): {sqlite_url}")
    print(f"Target (MySQL): {mysql_url}")

    source_engine = create_engine(sqlite_url, future=True)
    target_engine = create_engine(mysql_url, future=True)

    # Make sure all tables exist in MySQL.
    db.metadata.create_all(target_engine)

    SourceSession = sessionmaker(bind=source_engine, future=True)
    source_session = SourceSession()

    copied_total = 0
    models_in_order = [
        Customer,
        Staff,
        Service,
        Appointment,
        AppointmentService,
        Transaction,
        LoyaltyHistory,
        Attendance,
        Promotion,
        CampaignStats,
        WhatsAppConversation,
        User,
    ]

    with target_engine.begin() as connection:
        if target_engine.dialect.name == "mysql":
            connection.execute(text("SET FOREIGN_KEY_CHECKS=0;"))

        for model in models_in_order:
            copied = copy_table(source_session, connection, model)
            copied_total += copied
            print(f"{model.__tablename__}: copied {copied} rows")

        if target_engine.dialect.name == "mysql":
            connection.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

    source_session.close()
    source_engine.dispose()
    target_engine.dispose()

    print(f"Completed migration. Total rows copied: {copied_total}")


if __name__ == "__main__":
    main()

