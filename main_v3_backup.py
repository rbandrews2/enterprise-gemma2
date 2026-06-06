import os
import re
import time
import requests
import google.auth
import google.auth.transport.requests

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal

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
