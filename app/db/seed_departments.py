from app.db.database import SessionLocal
from app.models import Department, Service


departments = {
    "Sanitation & Waste Management": [
        "Garbage Collection",
        "Waste Dumping",
        "Public Bin Maintenance",
    ],
    "Roads & Street Infrastructure": [
        "Pothole",
        "Road Damage",
        "Footpath Damage",
    ],
    "Water Supply": [
        "Water Leakage",
        "No Water Supply",
        "Pipeline Damage",
    ],
    "Electricity & Street Lighting": [
        "Streetlight Not Working",
        "Electrical Infrastructure Damage",
    ],
    "Drainage & Sewerage": [
        "Blocked Drain",
        "Sewage Overflow",
        "Drainage Damage",
    ],
    "Public Health": [
        "Mosquito Infestation",
        "Unhygienic Public Area",
        "Public Health Hazard",
    ],
    "Parks & Public Spaces": [
        "Park Maintenance",
        "Damaged Park Equipment",
        "Public Space Damage",
    ],
    "Traffic & Transport": [
        "Traffic Signal Issue",
        "Road Signage Issue",
        "Public Transport Issue",
    ],
}


def seed_departments():
    db = SessionLocal()

    try:
        for department_name, service_names in departments.items():

            department = (
                db.query(Department)
                .filter(Department.name == department_name)
                .first()
            )

            if department is None:
                department = Department(name=department_name)
                db.add(department)
                db.flush()

            for service_name in service_names:
                existing_service = (
                    db.query(Service)
                    .filter(
                        Service.name == service_name,
                        Service.department_id == department.id
                    )
                    .first()
                )

                if existing_service is None:
                    db.add(
                        Service(
                            name=service_name,
                            department_id=department.id
                        )
                    )

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_departments()
    print("Departments and services seeded successfully.")