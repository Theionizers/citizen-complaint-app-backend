import json

from openai import OpenAI

from app.core.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def route_complaint(
    description: str,
    departments: list[dict],
) -> dict:

    prompt = f"""
You are the complaint-routing AI for OZOCO.

Analyze the citizen complaint and select the most appropriate
department and service from the provided options.

Also provide an expected resolution.

Available departments and services:
{json.dumps(departments, indent=2)}

Citizen complaint:
{description}

Return ONLY valid JSON in this exact format:

{{
    "department_id": <integer>,
    "service_id": <integer>,
    "expected_resolution": "<string>",
    "routing_confidence": <number between 0 and 1>
}}

Rules:
- department_id must come from the provided departments.
- service_id must belong to the selected department.
- Do not invent IDs.
- routing_confidence must be between 0 and 1.
- expected_resolution should describe what the responsible authority
  should do to resolve the complaint.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a civic complaint routing system."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content

    if content is None:
        raise ValueError("LLM returned an empty response")

    return json.loads(content)