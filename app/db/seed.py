from app.db.database import SessionLocal
from app.models import Role


def seed_roles():
    db = SessionLocal()

    try:
        roles = ["citizen", "officer", "admin"]

        for role_name in roles:
            existing_role = (
                db.query(Role)
                .filter(Role.name == role_name)
                .first()
            )

            if existing_role is None:
                db.add(Role(name=role_name))

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()
    print("Roles seeded successfully.")