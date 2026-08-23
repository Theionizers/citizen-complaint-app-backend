from app.db.database import SessionLocal
from app.models import Role, User
from app.core.security import hash_password


def seed_users():
    db = SessionLocal()

    try:
        officer_role = (
            db.query(Role)
            .filter(Role.name == "officer")
            .first()
        )

        admin_role = (
            db.query(Role)
            .filter(Role.name == "admin")
            .first()
        )

        if officer_role is None or admin_role is None:
            print("Required roles do not exist. Run seed.py first.")
            return

        existing_officer = (
            db.query(User)
            .filter(User.email == "officer@ozoco.com")
            .first()
        )

        if existing_officer is None:
            officer = User(
                name="Test Officer",
                email="officer@ozoco.com",
                password_hash=hash_password("Officer@123"),
                role_id=officer_role.id
            )

            db.add(officer)

        existing_admin = (
            db.query(User)
            .filter(User.email == "admin@ozoco.com")
            .first()
        )

        if existing_admin is None:
            admin = User(
                name="Test Admin",
                email="admin@ozoco.com",
                password_hash=hash_password("Admin@123"),
                role_id=admin_role.id
            )

            db.add(admin)

        db.commit()

        print("Test users seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_users()