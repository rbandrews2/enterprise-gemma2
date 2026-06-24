import os
import re
import time
import requests
import google.auth
import google.auth.transport.requests
import json
import uuid
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.cloud import storage
from datetime import datetime, timedelta
from vertexai.preview.vision_models import ImageGenerationModel
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Literal, List

VERTEX_ENDPOINT_URL = os.getenv("VERTEX_ENDPOINT_URL")
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "cloud_run_iam").lower()
ALLOWED_EMAIL_DOMAIN = os.getenv("ALLOWED_EMAIL_DOMAIN", "workzoneos.org").lower()

app = FastAPI(title="Superior Gemma Assistant API", version="3.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _email_from_iap_header(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    email = value.split(":", 1)[-1].strip().lower()
    return email or None


def verified_user(request: Request) -> Optional[str]:
    if AUTH_PROVIDER != "iap":
        return None

    email = _email_from_iap_header(request.headers.get("x-goog-authenticated-user-email"))
    if not email or not email.endswith(f"@{ALLOWED_EMAIL_DOMAIN}"):
        raise HTTPException(status_code=403, detail="Verified workzoneos.org access required")

    return email


@app.middleware("http")
async def verified_user_middleware(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)

    try:
        email = verified_user(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    request.state.verified_user_email = email
    return await call_next(request)

class StreetViewVisualRequest(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heading: Optional[int] = 0
    pitch: Optional[int] = 0
    fov: Optional[int] = 90
    work_zone_type: Optional[str] = "shoulder closure"
    work_type: Optional[str] = "road work"
    overlay_title: Optional[str] = "Draft Work Zone Visual"
    notes: Optional[str] = None



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


class EmailPackageRequest(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    project_name: str
    package_summary: str
    sender_name: Optional[str] = "Superior Consultation"

class CompletePackageV13Request(BaseModel):
    location: LocationInput
    work: WorkDetails
    site_conditions: Optional[SiteConditions] = None
    user_notes: Optional[str] = None
    streetview_heading: Optional[int] = 0
    streetview_pitch: Optional[int] = 0
    streetview_fov: Optional[int] = 90

class DeliverPackageRequest(BaseModel):
    customer_name: Optional[str] = "Customer"
    customer_email: Optional[str] = None
    customer_company: Optional[str] = None
    package_request: CompletePackageV13Request


GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def fetch_streetview_image(req: StreetViewVisualRequest) -> str:
    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_MAPS_API_KEY is not configured.")

    if req.latitude is not None and req.longitude is not None:
        location = f"{req.latitude},{req.longitude}"
    elif req.address:
        location = req.address
    else:
        raise HTTPException(status_code=400, detail="Provide address or latitude/longitude.")

    response = requests.get(
        "https://maps.googleapis.com/maps/api/streetview",
        params={
            "size": "1280x720",
            "location": location,
            "heading": req.heading,
            "pitch": req.pitch,
            "fov": req.fov,
            "key": GOOGLE_MAPS_API_KEY,
        },
        timeout=60,
    )

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    if "image" not in response.headers.get("Content-Type", ""):
        raise HTTPException(status_code=500, detail=response.text[:500])

    filename = f"/tmp/streetview-base-{uuid.uuid4().hex}.png"
    with open(filename, "wb") as f:
        f.write(response.content)

    return filename

def compliance_to_streetview_request(req: CompletePackageV13Request) -> StreetViewVisualRequest:
    address_parts = []

    if req.location.address:
        address_parts.append(req.location.address)

    if req.location.state:
        address_parts.append(req.location.state)

    if req.location.zip_code:
        address_parts.append(req.location.zip_code)

    address = ", ".join(address_parts) if address_parts else None

    return StreetViewVisualRequest(
        address=address,
        latitude=req.location.latitude,
        longitude=req.location.longitude,
        heading=req.streetview_heading,
        pitch=req.streetview_pitch,
        fov=req.streetview_fov,
        work_zone_type=req.work.work_zone_type,
        work_type=req.work.work_type,
        overlay_title=f"Draft {req.work.work_zone_type.title()} Visual",
        notes=req.user_notes
    )

def read_json_from_gcs(blob_name: str) -> dict:
    client = storage.Client()
    bucket = client.bucket(PACKAGE_BUCKET)
    blob = bucket.blob(blob_name)

    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {blob_name}")

    return json.loads(blob.download_as_text())


def list_package_manifests(limit: int = 25) -> list:
    client = storage.Client()
    bucket = client.bucket(PACKAGE_BUCKET)

    results = []

    for blob in bucket.list_blobs(prefix="packages/"):
        if blob.name.endswith("manifest-with-assets.json"):
            try:
                data = json.loads(blob.download_as_text())
                results.append({
                    "package_id": data.get("package_id"),
                    "created_at": data.get("created_at"),
                    "status": data.get("status"),
                    "assets": data.get("assets", {}),
                    "human_review_required": data.get("human_review_required", True),
                })
            except Exception:
                continue

    results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return results[:limit]


def draw_workzone_overlay(image_path: str, req: StreetViewVisualRequest) -> str:

    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
        font_label = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 18)
    except Exception:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.rectangle([0, 0, width, 90], fill=(0, 0, 0))
    draw.text((30, 22), req.overlay_title, fill=(255, 255, 255), font=font_title)

    draw.rectangle([530, 330, 960, 520], outline=(255, 210, 0), width=6)
    draw.text((550, 350), "WORK AREA", fill=(255, 255, 0), font=font_label)

    draw.rectangle([90, 170, 430, 250], outline=(255, 165, 0), width=5)
    draw.text((110, 195), "ADVANCE WARNING SIGN", fill=(255, 165, 0), font=font_small)

    draw.ellipse([350, 430, 430, 510], outline=(0, 255, 255), width=6)
    draw.text((260, 520), "FLAGGER LOCATION", fill=(0, 255, 255), font=font_small)

    for i in range(8):
        x = 480 + i * 60
        y = 570 - i * 14
        draw.polygon([(x, y), (x + 18, y + 38), (x - 18, y + 38)], fill=(255, 100, 0), outline=(255, 255, 255))

    draw.text((470, 650), "CHANNELIZING DEVICES / CONES", fill=(255, 140, 0), font=font_small)

    draw.text((30, height - 65), f"{req.work_zone_type} | {req.work_type}", fill=(255, 255, 255), font=font_small)
    draw.text((30, height - 35), "Draft visual aid only. Final TTC/MOT setup requires qualified review.", fill=(255, 255, 255), font=font_small)

    output_path = f"/tmp/streetview-overlay-{uuid.uuid4().hex}.png"
    image.save(output_path)
    return output_path


def generate_signed_url(destination_blob: str, minutes: int = 60) -> str:
    client = storage.Client()
    bucket = client.bucket(PACKAGE_BUCKET)
    blob = bucket.blob(destination_blob)

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    service_account_email = os.getenv("SERVICE_ACCOUNT_EMAIL") or getattr(
        credentials,
        "service_account_email",
        None
    )

    if not service_account_email:
        raise HTTPException(status_code=500, detail="SERVICE_ACCOUNT_EMAIL is not configured")

    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=minutes),
        method="GET",
        service_account_email=service_account_email,
        access_token=credentials.token
    )


def build_package_pdf(package_text: str, package_id: str) -> str:
    filename = f"/tmp/compliance-package-{package_id}.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Superior Consultation - Draft Work Zone Compliance Package")

    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(50, y, f"Package ID: {package_id}")

    y -= 30
    c.setFont("Helvetica", 10)

    wrapped_lines = []

    for raw_line in package_text.splitlines():
        line = raw_line.strip()

        if not line:
            wrapped_lines.append("")
            continue

        while len(line) > 95:
            wrapped_lines.append(line[:95])
            line = line[95:]

        wrapped_lines.append(line)

    for line in wrapped_lines:
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

        c.drawString(50, y, line[:110])
        y -= 14

    c.save()

    return filename


def save_json_temp(data: dict) -> str:
    filename = f"/tmp/package-{uuid.uuid4().hex}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    return filename


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



def generate_vertex_image(prompt: str) -> str:
    try:
        import vertexai

        vertexai.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "enterprise-gemma2"),
            location=os.getenv("VERTEX_IMAGE_REGION", "us-central1")
        )

        model = ImageGenerationModel.from_pretrained(
            os.getenv("VERTEX_IMAGE_MODEL", "imagen-4.0-generate-001")
        )

        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )

        filename = f"/tmp/work-zone-visual-{uuid.uuid4().hex}.png"
        image = images[0]

        # Method 1: SDK native save
        try:
            image.save(location=filename)
            return filename
        except Exception:
            pass

        # Method 2: direct bytes fallback
        image_bytes = getattr(image, "_image_bytes", None) or getattr(image, "image_bytes", None)

        if image_bytes:
            with open(filename, "wb") as f:
                f.write(image_bytes)
            return filename

        raise Exception("Imagen returned an image object but no saveable bytes were found.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


PACKAGE_BUCKET = os.getenv("PACKAGE_BUCKET", "gemma_think")

def upload_file_to_gcs(local_path: str, destination_blob: str) -> str:
    client = storage.Client()
    bucket = client.bucket(PACKAGE_BUCKET)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(local_path)

    return f"gs://{PACKAGE_BUCKET}/{destination_blob}"


def upload_json_to_gcs(data: dict, destination_blob: str) -> str:
    client = storage.Client()
    bucket = client.bucket(PACKAGE_BUCKET)
    blob = bucket.blob(destination_blob)
    blob.upload_from_string(
        json.dumps(data, indent=2),
        content_type="application/json"
    )

    return f"gs://{PACKAGE_BUCKET}/{destination_blob}"

@app.post("/complete-package-saved")
def complete_package_saved(req: CompliancePackageRequest):
    package_id = uuid.uuid4().hex
    created_at = datetime.utcnow().isoformat()

    package_json_result = compliance_package_json(req)
    image_prompt_result = package_image_prompt(req)

    email_result = email_draft(
        EmailPackageRequest(
            customer_name="Customer",
            project_name=f"{req.work.work_zone_type} Package",
            package_summary="Draft compliance package with checklists, forms, and visual aids."
        )
    )

    image_path = generate_vertex_image(
        f"""
Professional work-zone visual aid.

{image_prompt_result.get("text", "")}
"""
    )

    manifest = {
        "package_id": package_id,
        "created_at": created_at,
        "status": "success",
        "input": req.model_dump(),
        "package": package_json_result,
        "image_prompt": image_prompt_result,
        "email_draft": email_result,
        "human_review_required": True,
        "notice": "Draft planning aid only. Final setup must be reviewed by qualified personnel before field deployment."
    }

    base_path = f"packages/{package_id}"

    json_uri = upload_json_to_gcs(
        manifest,
        f"{base_path}/manifest.json"
    )

    image_uri = upload_file_to_gcs(
        image_path,
        f"{base_path}/work-zone-visual-aid.png"
    )

    manifest["assets"] = {
        "manifest_json": json_uri,
        "image_png": image_uri
    }

    upload_json_to_gcs(
        manifest,
        f"{base_path}/manifest-with-assets.json"
    )

    return manifest


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api")
def api_status(request: Request):
    return {
        "service": "Superior Gemma Assistant API",
        "status": "online",
        "auth_provider": AUTH_PROVIDER,
        "verified_user": getattr(request.state, "verified_user_email", None),
        "routes": [
            "/health",
            "/chat",
            "/work-zone-plan",
            "/document",
            "/compliance-package",
            "/image-prompt",
            "/email-draft",
            "/compliance-package-json",
            "/package-pdf",
            "/package-manifest",
            "/package-image-prompt",
            "/generate-package-image",
            "/complete-package",
            "/complete-package-saved",
            "/complete-package-saved-v11",
            "/streetview-visual",
            "/complete-package-saved-v13"
        ]
    }


@app.get("/api/session")
def session(request: Request):
    return {
        "auth_provider": AUTH_PROVIDER,
        "allowed_domain": ALLOWED_EMAIL_DOMAIN,
        "verified_user": getattr(request.state, "verified_user_email", None),
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




@app.post("/image-prompt")
def image_prompt(req: CompliancePackageRequest):
    prompt = f"""
Instruction:
Create a detailed image-generation prompt for a work-zone visual aid.

Rules:
- This image is for customer explanation only.
- Include road type, work zone type, speed, time of day, and visible annotations.
- Include traffic control icons such as signs, cones, flagger locations, arrow board, buffer area, and work area.
- Do not claim exact DOT compliance distances unless verified by a qualified reviewer.
- Output only the image prompt.

Location:
{req.location.model_dump()}

Work details:
{req.work.model_dump()}

Site conditions:
{req.site_conditions.model_dump() if req.site_conditions else {}}

User notes:
{req.user_notes or "None"}

Image Prompt:
"""
    return call_model(prompt, max_tokens=350, temperature=0.1)


@app.post("/email-draft")
def email_draft(req: EmailPackageRequest):
    prompt = f"""
Instruction:
Create a professional customer email for sending a draft work-zone compliance package.

Rules:
- Keep it concise.
- Mention attached package materials.
- Mention that all field setups require final review by qualified personnel.
- Do not overpromise legal compliance.
- Professional B2B tone.

Customer name:
{req.customer_name or "Customer"}

Project name:
{req.project_name}

Package summary:
{req.package_summary}

Sender:
{req.sender_name}

Email:
"""
    return call_model(prompt, max_tokens=320, temperature=0.1)


@app.post("/compliance-package-json")
def compliance_package_json(req: CompliancePackageRequest):
    prompt = f"""
Instruction:
Create a structured JSON compliance package draft for a Virginia road crew.

Return valid JSON only. No markdown. No explanation outside JSON.

Use this exact top-level schema:
{{
  "job_summary": {{
    "location": "",
    "work_type": "",
    "work_zone_type": "",
    "road_type": "",
    "speed_limit": "",
    "time_of_day": "",
    "risk_level": "",
    "missing_information": []
  }},
  "forms_to_consider": [],
  "liability_and_safety_forms": [],
  "foreman_checklist": [],
  "crew_lead_checklist": [],
  "equipment_checklist": [],
  "setup_sequence": [],
  "inspection_and_closeout": [],
  "regulatory_review_items": [],
  "diagram_spec": {{
    "diagram_type": "",
    "base_visual": "",
    "overlays": [],
    "notes": []
  }},
  "image_generation_prompt": "",
  "email_summary": "",
  "human_review_notice": ""
}}

Rules:
- Do not invent exact legal citations.
- Flag items requiring supervisor, engineer, VDOT, or DOT review.
- Every checklist item must be unique.
- The image_generation_prompt must describe an annotated visual aid with signs, cones, flaggers, buffer, work area, and notations.
- The human_review_notice must state this is a draft planning aid requiring qualified review.

Location:
{req.location.model_dump()}

Work details:
{req.work.model_dump()}

Site conditions:
{req.site_conditions.model_dump() if req.site_conditions else {}}

User notes:
{req.user_notes or "None"}

JSON:
"""
    return call_model(prompt, max_tokens=750, temperature=0.1)

@app.post("/package-pdf")
def package_pdf(req: CompliancePackageRequest):
    package_result = compliance_package_json(req)
    text = package_result.get("text", "")

    filename = f"/tmp/compliance-package-{uuid.uuid4().hex}.pdf"

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Superior Consultation - Draft Work Zone Compliance Package")

    y -= 35
    c.setFont("Helvetica", 10)

    wrapped_lines = []
    for line in text.splitlines():
        while len(line) > 95:
            wrapped_lines.append(line[:95])
            line = line[95:]
        wrapped_lines.append(line)

    for line in wrapped_lines:
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

        c.drawString(50, y, line[:110])
        y -= 14

    c.save()

    return FileResponse(
        filename,
        media_type="application/pdf",
        filename="superior-compliance-package.pdf"
    )

@app.post("/package-manifest")
def package_manifest(req: CompliancePackageRequest):
    prompt = f"""
Instruction:
Create a customer-ready work-zone compliance package manifest.

Return clean JSON only. No markdown.

Schema:
{{
  "package_title": "",
  "customer_summary": "",
  "included_documents": [],
  "recommended_attachments": [],
  "image_assets": {{
    "customer_visual_prompt": "",
    "field_diagram_prompt": "",
    "overlay_labels": [],
    "map_overlay_notes": []
  }},
  "email_subject": "",
  "email_body": "",
  "human_review_notice": ""
}}

Rules:
- Package is a draft planning aid.
- Include PDF, checklists, forms, visual aid, diagram notes, and review notice.
- Use business-professional language.
- Do not invent exact legal citations.
- Mention that final setup must be reviewed by qualified personnel.

Location:
{req.location.model_dump()}

Work:
{req.work.model_dump()}

Site conditions:
{req.site_conditions.model_dump() if req.site_conditions else {}}

User notes:
{req.user_notes or "None"}

JSON:
"""
    return call_model(prompt, max_tokens=650, temperature=0.1)


@app.post("/package-image-prompt")
def package_image_prompt(req: CompliancePackageRequest):
    prompt = f"""
Instruction:
Create two image generation prompts for a work-zone compliance package.

Return clean JSON only. No markdown.

Schema:
{{
  "customer_visual_prompt": "",
  "technical_diagram_prompt": "",
  "overlay_items": [
    {{
      "label": "",
      "icon": "",
      "placement": "",
      "purpose": ""
    }}
  ],
  "safety_disclaimer": ""
}}

Rules:
- The customer_visual_prompt should create a professional illustrated/satellite-style work area image.
- The technical_diagram_prompt should describe a top-down annotated work-zone diagram.
- Include labels for advance warning signs, cones/channelizing devices, flagger location, buffer area, work area, shoulder/lane closure, arrow board if applicable, and portable rumble strip if appropriate.
- Do not give exact spacing unless verified by official project documents.
- Make clear that the visual is a draft planning aid.

Location:
{req.location.model_dump()}

Work:
{req.work.model_dump()}

Site conditions:
{req.site_conditions.model_dump() if req.site_conditions else {}}

User notes:
{req.user_notes or "None"}

JSON:
"""
    return call_model(prompt, max_tokens=700, temperature=0.1)



@app.post("/generate-package-image")
def generate_package_image(req: CompliancePackageRequest):
    prompt_result = package_image_prompt(req)
    image_prompt_text = prompt_result.get("text", "")

    final_prompt = f"""
Create a professional customer-facing work-zone visual aid.

Style:
- clean technical illustration
- top-down road work layout
- clear traffic control symbols
- readable labels
- no photorealistic people closeups
- no gore, crash, emergency scene, or unsafe behavior

Required annotations:
- advance warning sign placement
- channelizing devices / cones
- work area
- buffer area
- flagger location if applicable
- shoulder or lane closure area
- portable rumble strip location if applicable
- arrow board if applicable

Prompt details:
{image_prompt_text}
"""

    image_path = generate_vertex_image(final_prompt)

    return FileResponse(
        image_path,
        media_type="image/png",
        filename="work-zone-visual-aid.png"
    )




@app.post("/complete-package")
def complete_package(req: CompliancePackageRequest):

    # STEP 1 — Structured package JSON
    package_json_result = compliance_package_json(req)

    # STEP 2 — Image prompt package
    image_prompt_result = package_image_prompt(req)

    # STEP 3 — Email draft
    email_result = email_draft(
        EmailPackageRequest(
            customer_name="Customer",
            project_name=f"{req.work.work_zone_type} Package",
            package_summary="Draft compliance package with checklists, forms, and visual aids."
        )
    )

    # STEP 4 — Generate image
    image_prompt_text = image_prompt_result.get("text", "")

    image_path = generate_vertex_image(
        f"""
Professional work-zone visual aid.

{image_prompt_text}
"""
    )

    # STEP 5 — Save package JSON locally
    json_path = save_json_temp(package_json_result)

    # STEP 6 — Build manifest response
    return {
        "status": "success",
        "generated_at": datetime.utcnow().isoformat(),

        "package": package_json_result,
        "email_draft": email_result,

        "assets": {
            "json_file": json_path,
            "image_file": image_path
        },

        "human_review_required": True,

        "notice": (
            "This package is a draft planning aid requiring review "
            "by qualified DOT/work-zone personnel before deployment."
        )
    }




@app.post("/complete-package-saved-v11")
def complete_package_saved_v11(req: CompliancePackageRequest):
    package_id = uuid.uuid4().hex
    created_at = datetime.utcnow().isoformat()

    package_json_result = compliance_package_json(req)
    image_prompt_result = package_image_prompt(req)

    email_result = email_draft(
        EmailPackageRequest(
            customer_name="Customer",
            project_name=f"{req.work.work_zone_type} Package",
            package_summary="Draft compliance package with checklists, forms, visual aid, and PDF."
        )
    )

    image_path = generate_vertex_image(
        f"""
Professional work-zone visual aid.

{image_prompt_result.get("text", "")}
"""
    )

    package_text = package_json_result.get("text", "")
    pdf_path = build_package_pdf(package_text, package_id)

    base_path = f"packages/{package_id}"

    manifest = {
        "package_id": package_id,
        "created_at": created_at,
        "status": "success",
        "input": req.model_dump(),
        "package": package_json_result,
        "image_prompt": image_prompt_result,
        "email_draft": email_result,
        "human_review_required": True,
        "notice": "Draft planning aid only. Final setup must be reviewed by qualified personnel before field deployment."
    }

    manifest_blob = f"{base_path}/manifest.json"
    manifest_assets_blob = f"{base_path}/manifest-with-assets.json"
    image_blob = f"{base_path}/work-zone-visual-aid.png"
    pdf_blob = f"{base_path}/superior-compliance-package.pdf"

    manifest_uri = upload_json_to_gcs(manifest, manifest_blob)
    image_uri = upload_file_to_gcs(image_path, image_blob)
    pdf_uri = upload_file_to_gcs(pdf_path, pdf_blob)

    signed_image_url = generate_signed_url(image_blob, minutes=120)
    signed_pdf_url = generate_signed_url(pdf_blob, minutes=120)
    signed_manifest_url = generate_signed_url(manifest_assets_blob, minutes=120)

    manifest["assets"] = {
        "manifest_json": manifest_uri,
        "image_png": image_uri,
        "pdf": pdf_uri,
        "signed_image_url": signed_image_url,
        "signed_pdf_url": signed_pdf_url,
        "signed_manifest_url": signed_manifest_url
    }

    final_manifest_uri = upload_json_to_gcs(manifest, manifest_assets_blob)

    manifest["assets"]["manifest_with_assets_json"] = final_manifest_uri

    return manifest


@app.post("/streetview-visual")
def streetview_visual(req: StreetViewVisualRequest):
    package_id = uuid.uuid4().hex
    base_path = f"packages/{package_id}"

    base_image = fetch_streetview_image(req)
    overlay_image = draw_workzone_overlay(base_image, req)

    image_blob = f"{base_path}/streetview-work-zone-overlay.png"
    image_uri = upload_file_to_gcs(overlay_image, image_blob)
    signed_image_url = generate_signed_url(image_blob, minutes=120)

    manifest = {
        "package_id": package_id,
        "type": "streetview_visual",
        "input": req.model_dump(),
        "assets": {
            "streetview_overlay_png": image_uri,
            "signed_image_url": signed_image_url
        },
        "human_review_required": True,
        "notice": "Draft Street View visual aid only. Final setup must be reviewed by qualified personnel."
    }

    upload_json_to_gcs(manifest, f"{base_path}/streetview-visual-manifest.json")

    return manifest

@app.post("/complete-package-saved-v13")
def complete_package_saved_v13(req: CompletePackageV13Request):
    package_id = uuid.uuid4().hex
    created_at = datetime.utcnow().isoformat()
    base_path = f"packages/{package_id}"

    compliance_req = CompliancePackageRequest(
        location=req.location,
        work=req.work,
        site_conditions=req.site_conditions,
        user_notes=req.user_notes,
        requested_outputs=[
            "forms",
            "checklists",
            "regulatory_summary",
            "diagram_spec",
            "ai_visual",
            "streetview_overlay",
            "pdf",
            "email_draft"
        ]
    )

    package_json_result = compliance_package_json(compliance_req)
    image_prompt_result = package_image_prompt(compliance_req)

    email_result = email_draft(
        EmailPackageRequest(
            customer_name="Customer",
            project_name=f"{req.work.work_zone_type} Package",
            package_summary="Draft compliance package with PDF, AI visual, Street View overlay, checklists, forms, and signed download links."
        )
    )

    ai_image_path = generate_vertex_image(
        f"""
Professional work-zone visual aid.

{image_prompt_result.get("text", "")}
"""
    )

    street_req = compliance_to_streetview_request(req)
    streetview_base = fetch_streetview_image(street_req)
    streetview_overlay_path = draw_workzone_overlay(streetview_base, street_req)

    package_text = package_json_result.get("text", "")
    pdf_path = build_package_pdf(package_text, package_id)

    manifest = {
        "package_id": package_id,
        "created_at": created_at,
        "status": "success",
        "input": req.model_dump(),
        "package": package_json_result,
        "image_prompt": image_prompt_result,
        "email_draft": email_result,
        "human_review_required": True,
        "notice": "Draft planning aid only. Final setup must be reviewed by qualified personnel before field deployment."
    }

    manifest_blob = f"{base_path}/manifest.json"
    manifest_assets_blob = f"{base_path}/manifest-with-assets.json"
    ai_image_blob = f"{base_path}/ai-work-zone-visual-aid.png"
    streetview_blob = f"{base_path}/streetview-work-zone-overlay.png"
    pdf_blob = f"{base_path}/superior-compliance-package.pdf"

    manifest_uri = upload_json_to_gcs(manifest, manifest_blob)
    ai_image_uri = upload_file_to_gcs(ai_image_path, ai_image_blob)
    streetview_uri = upload_file_to_gcs(streetview_overlay_path, streetview_blob)
    pdf_uri = upload_file_to_gcs(pdf_path, pdf_blob)

    manifest["assets"] = {
        "manifest_json": manifest_uri,
        "ai_image_png": ai_image_uri,
        "streetview_overlay_png": streetview_uri,
        "pdf": pdf_uri,
        "signed_ai_image_url": generate_signed_url(ai_image_blob, minutes=120),
        "signed_streetview_overlay_url": generate_signed_url(streetview_blob, minutes=120),
        "signed_pdf_url": generate_signed_url(pdf_blob, minutes=120)
    }

    final_manifest_uri = upload_json_to_gcs(manifest, manifest_assets_blob)
    manifest["assets"]["manifest_with_assets_json"] = final_manifest_uri
    manifest["assets"]["signed_manifest_url"] = generate_signed_url(manifest_assets_blob, minutes=120)

    return manifest


@app.post("/deliver-package")
def deliver_package(req: DeliverPackageRequest):
    generated = complete_package_saved_v13(req.package_request)

    package_id = generated.get("package_id")
    assets = generated.get("assets", {})

    subject = f"Draft Work Zone Compliance Package - {req.package_request.work.work_zone_type.title()}"

    body = f"""
Hello {req.customer_name or "Customer"},

Your draft work-zone compliance package has been generated.

Package ID: {package_id}

Download links:
PDF Package:
{assets.get("signed_pdf_url")}

AI Work-Zone Visual:
{assets.get("signed_ai_image_url")}

Street View Overlay:
{assets.get("signed_streetview_overlay_url")}

Manifest:
{assets.get("signed_manifest_url")}

Important: This package is a draft planning aid. Final field setup must be reviewed by qualified personnel before deployment.

Thank you,
Superior Consultation
""".strip()

    delivery_record = {
        "package_id": package_id,
        "customer": {
            "name": req.customer_name,
            "email": req.customer_email,
            "company": req.customer_company,
        },
        "email_delivery": {
            "provider": "gmail_api",
            "mode": "draft_first",
            "recipient": req.customer_email,
            "subject": subject,
            "body": body,
            "attachments_mode": "signed_links_now_attachments_later",
            "attachments": {
                "signed_pdf_url": assets.get("signed_pdf_url"),
                "signed_ai_image_url": assets.get("signed_ai_image_url"),
                "signed_streetview_overlay_url": assets.get("signed_streetview_overlay_url"),
                "signed_manifest_url": assets.get("signed_manifest_url"),
            },
            "status": "preview_ready",
        },
        "package": generated,
        "human_review_required": True,
    }

    upload_json_to_gcs(
        delivery_record,
        f"deliveries/{package_id}/delivery.json"
    )

    return {
        "status": "ready_for_delivery",
        "package_id": package_id,
        "customer": delivery_record["customer"],
        "email_delivery": delivery_record["email_delivery"],
        "assets": assets,
        "delivery_record_uri": f"gs://{PACKAGE_BUCKET}/deliveries/{package_id}/delivery.json",
        "human_review_required": True,
    }


@app.get("/packages/{package_id}")
def get_package(package_id: str):
    return read_json_from_gcs(f"packages/{package_id}/manifest-with-assets.json")


@app.get("/packages")
def list_packages(limit: int = 25):
    return {
        "count": min(limit, 25),
        "packages": list_package_manifests(limit=min(limit, 25))
    }


@app.get("/deliveries/{package_id}")
def get_delivery(package_id: str):
    return read_json_from_gcs(f"deliveries/{package_id}/delivery.json")


@app.post("/package-email-preview")
def package_email_preview(req: DeliverPackageRequest):
    subject = f"Draft Work Zone Compliance Package - {req.package_request.work.work_zone_type.title()}"

    body = f"""
Hello {req.customer_name or "Customer"},

A draft work-zone compliance package is ready to be generated for your project.

Project type: {req.package_request.work.work_zone_type}
Work type: {req.package_request.work.work_type}
Location: {req.package_request.location.address or "Location provided by coordinates"}

The completed package will include:
- PDF compliance package
- AI-generated work-zone visual
- Real Street View overlay visual
- Package manifest
- Human review notice

Important: Final field setup must be reviewed by qualified personnel before deployment.

Thank you,
Superior Consultation
""".strip()

    return {
        "provider": "gmail_api",
        "mode": "draft_first",
        "recipient": req.customer_email,
        "subject": subject,
        "body": body,
        "status": "preview_ready"
    }
