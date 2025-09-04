import os
import re
import threading
import time
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


app = FastAPI(title="PMS Chatbot Service", version="1.0.0")


# Configuration via environment variables
SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8085"))
SERVICE_HOSTNAME: str = os.getenv("SERVICE_HOSTNAME", os.getenv("HOSTNAME", "localhost"))
EUREKA_SERVER_URL: Optional[str] = os.getenv(
    "EUREKA_CLIENT_SERVICE_URL_DEFAULTZONE", os.getenv("EUREKA_SERVER_URL")
)
EUREKA_APP_NAME: str = os.getenv("EUREKA_APP_NAME", "chatbot-service")

API_GATEWAY_URL: Optional[str] = os.getenv("API_GATEWAY_URL")
APPOINTMENT_SERVICE_BASE_URL: Optional[str] = os.getenv("APPOINTMENT_SERVICE_BASE_URL")
PATIENT_SERVICE_BASE_URL: Optional[str] = os.getenv("PATIENT_SERVICE_BASE_URL")
DOCTOR_SERVICE_BASE_URL: Optional[str] = os.getenv("DOCTOR_SERVICE_BASE_URL")


def _normalize_base_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    return url.rstrip("/")


API_GATEWAY_URL = _normalize_base_url(API_GATEWAY_URL)
APPOINTMENT_SERVICE_BASE_URL = _normalize_base_url(APPOINTMENT_SERVICE_BASE_URL)
PATIENT_SERVICE_BASE_URL = _normalize_base_url(PATIENT_SERVICE_BASE_URL)
DOCTOR_SERVICE_BASE_URL = _normalize_base_url(DOCTOR_SERVICE_BASE_URL)


def detect_intent(message: str) -> str:
    text = message.strip().lower()
    if any(greet in text for greet in ["hi", "hello", "hey"]):
        return "greeting"
    if re.search(r"\b(book|schedule)\b.*\b(appointment|appt)\b", text):
        return "book_appointment"
    if re.search(r"\b(show|list|my)\b.*\b(appointments|appts)\b", text) or "show my appointments" in text:
        return "fetch_appointments"
    return "unknown"


def resolve_appointment_base_url() -> Optional[str]:
    if APPOINTMENT_SERVICE_BASE_URL:
        return APPOINTMENT_SERVICE_BASE_URL
    if API_GATEWAY_URL:
        return f"{API_GATEWAY_URL}/appointments"
    # Fallback to service DNS name on docker network
    return "http://appointment-service:8083"


def book_appointment_via_api(message: str) -> str:
    base_url = resolve_appointment_base_url()
    try:
        # Naive entity extraction; in real-world replace with proper NLU
        doctor_match = re.search(r"with\s+dr\.?\s+([a-zA-Z]+)", message, re.IGNORECASE)
        date_match = re.search(r"\b(today|tomorrow|\d{4}-\d{2}-\d{2})\b", message, re.IGNORECASE)

        doctor_name = doctor_match.group(1) if doctor_match else None
        date_str = date_match.group(1) if date_match else None

        payload = {
            "doctorName": doctor_name,
            "date": date_str,
        }

        resp = requests.post(f"{base_url}/book", json=payload, timeout=10)
        if resp.status_code >= 400:
            return f"Sorry, I couldn't book the appointment right now (status {resp.status_code})."
        data = resp.json()
        return data.get("message") or "Your appointment request has been submitted."
    except Exception as exc:  # noqa: BLE001
        return f"Sorry, something went wrong while booking the appointment: {exc}"


def fetch_appointments_via_api() -> str:
    base_url = resolve_appointment_base_url()
    try:
        resp = requests.get(f"{base_url}", timeout=10)
        if resp.status_code >= 400:
            return f"Couldn't fetch appointments (status {resp.status_code})."
        data = resp.json()
        # Expect list; format briefly
        if isinstance(data, list) and data:
            lines = []
            for appt in data[:5]:
                doctor = appt.get("doctorName") or appt.get("doctor") or appt.get("doctor_id")
                date = appt.get("date") or appt.get("appointmentDate")
                lines.append(f"- {date} with Dr. {doctor}")
            return "Here are your upcoming appointments:\n" + "\n".join(lines)
        return "You have no upcoming appointments."
    except Exception as exc:  # noqa: BLE001
        return f"Sorry, something went wrong while fetching appointments: {exc}"


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    intent = detect_intent(req.message)
    if intent == "greeting":
        return ChatResponse(response="Hello! How can I help you today?")
    if intent == "book_appointment":
        return ChatResponse(response=book_appointment_via_api(req.message))
    if intent == "fetch_appointments":
        return ChatResponse(response=fetch_appointments_via_api())
    return ChatResponse(response="I'm not sure how to help with that yet.")


# Spring-compatible health endpoints for existing infra
@app.get("/actuator/health")
def health() -> dict:
    return {"status": "UP"}


@app.get("/actuator/info")
def info() -> dict:
    return {"app": EUREKA_APP_NAME, "version": "1.0.0"}


# --- Eureka registration (best-effort) ---
def _eureka_register_instance():
    if not EUREKA_SERVER_URL:
        return
    try:
        instance_id = f"{SERVICE_HOSTNAME}:{EUREKA_APP_NAME}:{SERVICE_PORT}"
        app_name_upper = EUREKA_APP_NAME.upper()
        url = f"{EUREKA_SERVER_URL.rstrip('/')}/apps/{app_name_upper}"
        payload = {
            "instance": {
                "instanceId": instance_id,
                "hostName": SERVICE_HOSTNAME,
                "app": app_name_upper,
                "ipAddr": os.getenv("POD_IP", "127.0.0.1"),
                "status": "UP",
                "port": {"$": SERVICE_PORT, "@enabled": True},
                "securePort": {"$": 443, "@enabled": False},
                "healthCheckUrl": f"http://{SERVICE_HOSTNAME}:{SERVICE_PORT}/actuator/health",
                "statusPageUrl": f"http://{SERVICE_HOSTNAME}:{SERVICE_PORT}/actuator/info",
                "homePageUrl": f"http://{SERVICE_HOSTNAME}:{SERVICE_PORT}/",
                "vipAddress": EUREKA_APP_NAME,
                "dataCenterInfo": {
                    "@class": "com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo",
                    "name": "MyOwn",
                },
            }
        }
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        # Even if it fails, we'll keep trying heartbeats; many Eureka setups accept renewals after first manual add
    except Exception:
        pass


def _eureka_heartbeat_loop():
    if not EUREKA_SERVER_URL:
        return
    instance_id = f"{SERVICE_HOSTNAME}:{EUREKA_APPNAME if False else EUREKA_APP_NAME}:{SERVICE_PORT}"
    app_name_upper = EUREKA_APP_NAME.upper()
    base = EUREKA_SERVER_URL.rstrip("/")
    while True:
        try:
            url = f"{base}/apps/{app_name_upper}/{instance_id}"
            requests.put(url, timeout=5)
        except Exception:
            # Best-effort; ignore errors
            pass
        time.sleep(30)


def _start_eureka_background():
    if not EUREKA_SERVER_URL:
        return
    # Register once and then start heartbeat
    threading.Thread(target=_eureka_register_instance, daemon=True).start()
    threading.Thread(target=_eureka_heartbeat_loop, daemon=True).start()


@app.on_event("startup")
def on_startup() -> None:
    _start_eureka_background()


def create_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("chatbot_service:app", host="0.0.0.0", port=SERVICE_PORT, reload=False)

