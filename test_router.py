from app.db.database import SessionLocal
from app.models import Department, Service
from app.services.complaint_router import route_complaint


db = SessionLocal()

try:
    departments = db.query(Department).all()

    department_data = []

    for department in departments:
        services = (
            db.query(Service)
            .filter(Service.department_id == department.id)
            .all()
        )

        department_data.append({
            "department_id": department.id,
            "department_name": department.name,
            "services": [
                {
                    "service_id": service.id,
                    "service_name": service.name
                }
                for service in services
            ]
        })

    result = route_complaint(
        "There is a large pothole on the road near my house.",
        department_data
    )

    print(result)

finally:
    db.close()