# citizen-complaint-app-backend

## Citizen chatbot

The public `POST /chatbot/chat` endpoint answers questions only about making
complaints in Janamaan and the platform's citizen-facing features. It uses the
existing `OPENAI_API_KEY` setting from `.env` and is limited to 10 requests per
minute per client IP.

Request:

```json
{
	"message": "How can I add a photo to my complaint?",
	"history": []
}
```

`history` is optional and may contain up to 10 `{ "role": "user" | "assistant",
"content": "..." }` turns. Each message is limited to 2,000 characters. The
response is `{ "reply": "..." }`. The chatbot provides guidance only: citizens
must sign in to the Janamaan app to file or track their own complaints.

## Admin complaint export

`GET /complaints/admin/export` downloads a fresh `.xlsx` workbook of all current
complaints. It requires an admin access token. The Admin Panel's “Export to
Excel” button should call this endpoint with the token in the `Authorization`
header and download the response as a file. Since the workbook is generated
from the database at download time, newly submitted complaints are included
without a separate export job.

The workbook includes the requested complaint, citizen, routing, assignment,
status, and officer-note columns. The application does not currently collect
mobile numbers, admin verification records, final-resolution timestamps, or
remarks; those columns are included but left blank (verification is marked
“Not recorded”) until those fields are added to the complaint/account workflow.
