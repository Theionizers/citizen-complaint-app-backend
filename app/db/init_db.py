from app.db.database import engine
from app.db.base import Base

# Import models so SQLAlchemy registers them
from app.models import Role, User, Department, Service


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")