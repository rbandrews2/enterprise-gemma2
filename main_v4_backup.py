import os
import re
import time
import requests
import google.auth
import google.auth.transport.requests

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, List

VERTEX_ENDPOINT_URL = os.getenv("VERTEX_ENDPOINT_URL")

app = FastAPI(title="Superior Gemma Assistant API", version="3.0")

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 220
    temperature: float = 0.1

class WorkZoneRequest(BaseModel):
    job_type: str
    road_type: str
    location: str
    speed_limit: Optional[str] = None
    crew_notes: Optional[str] = None

class DocumentRequest(BaseModel):
    document_type: Literal["checklist", "incident_report", "daily_plan", "crew_message", "compliance_note"]
    topic: str
    details: str
    tone: Optional[str] = "professional"

class LocationInput(BaseModel):
    address: Optional[str] = None
    state: Optional[str] = "VA"
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class WorkDetails(BaseModel):
    work_type: str
    work_zone_type: str
    road_type: str
    speed_limit: Optional[str] = None
    time_of_day: Optional[str] = "day"
    duration: Optional[str] = None
    lane_count: Optional[int] = None
    shoulder_present: Optional[bool] = None
    traffic_volume: Optional[str] = None

class SiteConditions(BaseModel):
    curves: Optional[bool] = None
    hills: Optional[bool] = None
    intersections: Optional[bool] = None
    pedestrians: Optional[bool] = None
    school_zone: Optional[bool] = None
    weather_notes: Optional[str] = None

class CompliancePackageRequest(BaseModel):
    location: LocationInput
    work: WorkDetails
    site_conditions: Optional[SiteConditions] = None
    user_notes: Optional[str] = None
    requested_outputs: Optional[List[str]] = [
        "forms",
        "checklists",
        "regulatory_summary",
        "diagram_spec"
    ]
def get_access_token():
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token

def clean_output(text: str) -> str:
    text = text.replace("<|fim_prefix|>", "").replace("<|fim_suffix|>", "").replace("<|fim_middle|>", "")
    text = re.sub(r"Prompt:\s*", "", text)
    text = re.sub(r"Output:\s*", "", text)

    # Remove repeated identical lines
    lines = []
    seen = set()
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        key = clean.lower()
        if key not in seen:
            seen.add(key)
            lines.append(clean)

    return "\n".join(lines).strip()

def call_model(prompt: str, max_tokens: int = 220, temperature: float = 0.1):
    if not VERTEX_ENDPOINT_URL:
        raise HTTPException(status_code=500, detail="VERTEX_ENDPOINT_URL is not configured")

    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.75,
        "stop": [
            "\n\n\n",
            "<|fim_prefix|>",
            "<|fim_suffix|>",
            "<|fim_middle|>",
            "Repeat",
            "Prompt:"
        ],
    }

    started = time.time()
    response = requests.post(VERTEX_ENDPOINT_URL, headers=headers, json=payload, timeout=120)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    raw = response.json()
    first = raw.get("predictions", [""])[0]

    return {
        "latency_ms": round((time.time() - started) * 1000),
        "text": clean_output(first),
        "raw": raw,
    }

@app.get("/")
def root():
    return {
        "service": "Superior Gemma Assistant API",
        "status": "online",
        "routes": ["/health", "/chat", "/work-zone-plan", "/document"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    prompt = f"""
Instruction:
You are Superior Consultation's AI assistant for road crews, compliance forms, work zones, and deskless workforce operations.

Rules:
- Be concise.
- Avoid repetition.
- Use practical field language.
- Do not provide legal advice.
- If asked for a checklist, use unique bullet points only.

User request:
{req.message}

Answer:
"""
    return call_model(prompt, req.max_tokens, req.temperature)

@app.post("/work-zone-plan")
def work_zone_plan(req: WorkZoneRequest):
    prompt = f"""
Instruction:
Create a practical work-zone setup plan for a road crew.

Rules:
- Use clear sections.
- Include safety setup, traffic control devices, crew positioning, inspection reminders, and closeout.
- Avoid legal claims.
- Do not repeat items.
- Keep it field-ready.

Job type: {req.job_type}
Road type: {req.road_type}
Location: {req.location}
Speed limit: {req.speed_limit or "Not provided"}
Crew notes: {req.crew_notes or "None"}

Work Zone Plan:
"""
    return call_model(prompt, max_tokens=420, temperature=0.1)

@app.post("/document")
def document(req: DocumentRequest):
    prompt = f"""
Instruction:
Create a {req.document_type} for Superior Consultation's road crew/compliance workflow.

Rules:
- Tone: {req.tone}
- Use clear headings.
- Keep it practical.
- No repeated lines.
- No legal advice.
- End cleanly.

Topic: {req.topic}
Details: {req.details}

Document:
"""
    return call_model(prompt, max_tokens=500, temperature=0.1)

@app.post("/compliance-package")
def compliance_package(req: CompliancePackageRequest):
    prompt = f"""
Instruction:
Create a draft Virginia work-zone compliance package for a road crew.

Rules:
- Use practical field language.
- Do not repeat lines.
- Do not invent exact legal citations.
- Flag anything requiring supervisor, engineer, VDOT, or DOT review.
- Include checklist-style outputs.
- Include a structured diagram specification.
- End with a human review notice.

Location:
{req.location.model_dump()}

Work details:
{req.work.model_dump()}

Site conditions:
{req.site_conditions.model_dump() if req.site_conditions else {}}

User notes:
{req.user_notes or "None"}

Return these sections:
1. Job Classification
2. Assumptions and Missing Data
3. DOT / VDOT Compliance Forms to Consider
4. Recommended Liability and Safety Forms
5. Foreman Checklist
6. Crew Lead Checklist
7. Equipment Checklist
8. Setup Sequence
9. Inspection and Closeout
10. Regulation / Policy Review Items
11. Diagram JSON Specification
12. Human Review Notice

Compliance Package:
"""
    return call_model(prompt, max_tokens=900, temperature=0.1)
