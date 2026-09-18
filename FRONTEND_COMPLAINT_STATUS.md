# OZOCO Complaint Status API

Base URL: `http://localhost:8000`

All requests require:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Citizen complaint notes

Officer and admin notes are returned to the citizen in the `officer_note` field.
The citizen can read notes on their own complaints through either endpoint:

```http
GET /complaints/my
GET /complaints/{complaint_id}
```

Example response fields:

```json
{
  "id": 123,
  "status": "resolved",
  "officer_note": "Resolution reviewed by administration."
}
```

The citizen can only access complaints that belong to their own account.

## Officer status update

```http
PATCH /complaints/{complaint_id}/status
```

Required role: `officer`

Officers may set only:

- `under_review`
- `in_progress`

Example:

```json
{
  "status": "in_progress",
  "officer_note": "Work has started on this complaint."
}
```

`officer_note` is required for `in_progress`. Officers cannot set `resolved` or `closed`.

## Admin status update

```http
PATCH /complaints/admin/{complaint_id}/status
```

Required role: `admin`

Admins may set:

- `under_review`
- `in_progress`
- `resolved`
- `closed`

Resolve:

```json
{
  "status": "resolved",
  "officer_note": "Resolution reviewed by administration."
}
```

Final close:

```json
{
  "status": "closed"
}
```

A complaint must already be `resolved` before it can be `closed`. Only admins can resolve or close complaints. A closed complaint cannot be updated.

## Errors

- `200`: status updated successfully
- `400`: invalid status, missing note, closing before resolution, or updating a closed complaint
- `401`: missing, invalid, or expired token
- `403`: insufficient role permissions
- `404`: complaint not found
