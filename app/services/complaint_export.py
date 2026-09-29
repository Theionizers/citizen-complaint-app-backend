from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from app.models import Complaint


HEADERS = [
    "Complaint ID",
    "Date & Time",
    "Citizen Name",
    "Mobile Number",
    "Complaint Description",
    "Category",
    "Department",
    "Location",
    "Assigned Officer",
    "Current Status",
    "Officer Action/Resolution",
    "Admin Verification Status",
    "Final Resolution Date",
    "Remarks",
]


def _safe_text(value: str | None) -> str | None:
    if value is not None and value.lstrip().startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def build_complaints_workbook(complaints: list[Complaint]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Complaints"
    worksheet.append(HEADERS)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True)

    for complaint in complaints:
        latitude = complaint.latitude
        longitude = complaint.longitude
        location = (
            f"{latitude}, {longitude}"
            if latitude is not None and longitude is not None
            else None
        )
        citizen = complaint.citizen

        worksheet.append([
            complaint.id,
            complaint.created_at,
            _safe_text(citizen.name if citizen else None),
            None,
            _safe_text(complaint.description),
            _safe_text(complaint.service.name if complaint.service else None),
            _safe_text(complaint.department.name if complaint.department else None),
            location,
            _safe_text(
                complaint.assigned_officer.name
                if complaint.assigned_officer
                else None
            ),
            _safe_text(complaint.status),
            _safe_text(complaint.officer_note),
            "Not recorded",
            None,
            None,
        ])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.column_dimensions["A"].width = 16
    worksheet.column_dimensions["B"].width = 22
    worksheet.column_dimensions["C"].width = 24
    worksheet.column_dimensions["E"].width = 60
    worksheet.column_dimensions["F"].width = 24
    worksheet.column_dimensions["G"].width = 24
    worksheet.column_dimensions["H"].width = 24
    worksheet.column_dimensions["I"].width = 24
    worksheet.column_dimensions["K"].width = 50
    worksheet.column_dimensions["L"].width = 28

    for row in worksheet.iter_rows(min_row=2):
        row[1].number_format = "yyyy-mm-dd hh:mm:ss"
        for cell in (row[4], row[10]):
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()