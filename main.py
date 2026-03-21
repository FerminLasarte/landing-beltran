"""
Briones Chatbot — Backend
FastAPI + Google Gemini (SDK: google-genai ≥ 1.0)

Run:  uvicorn main:app --reload --port 8000
"""

import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("briones.chat")

# ── CORS ──────────────────────────────────────────────────────────────────────
# Lee orígenes desde FRONTEND_URL (CSV). Si no está definida, usa puertos
# de desarrollo local habituales.
# Producción → .env: FRONTEND_URL=https://grupobriones.com.ar,https://www.grupobriones.com.ar

_DEV_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:4200",
    "http://localhost:5173",
    "http://localhost:5500",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5173",
]

_raw_frontend_url = os.getenv("FRONTEND_URL", "").strip()
if _raw_frontend_url:
    ALLOWED_ORIGINS: List[str] = [o.strip() for o in _raw_frontend_url.split(",") if o.strip()]
    logger.info("CORS — orígenes desde FRONTEND_URL: %s", ALLOWED_ORIGINS)
else:
    ALLOWED_ORIGINS = _DEV_ORIGINS
    logger.warning("CORS — FRONTEND_URL no definida. Usando orígenes de desarrollo local.")

# ── Rate Limiting ─────────────────────────────────────────────────────────────
# 10 peticiones por minuto por IP en /api/chat.
# Nota: store en memoria (un solo proceso). En producción con múltiples workers
# agregá: storage_uri="redis://localhost:6379"

limiter = Limiter(key_func=get_remote_address, default_limits=[])

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Briones Chatbot API",
    description="Asistente virtual de Beltrán Briones impulsado por Google Gemini",
    version="2.1.0",
)

app.state.limiter = limiter


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning("Rate limit — IP: %s | path: %s", request.client.host, request.url.path)
    return JSONResponse(
        status_code=429,
        content={"detail": "Demasiadas consultas. Por favor esperá un momento antes de continuar."},
        headers={"Retry-After": "60"},
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ── Gemini client (nuevo SDK: google-genai) ───────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY no encontrada. Creá un archivo .env con tu clave. "
        "Obtené una gratis en https://aistudio.google.com/app/apikey"
    )

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
Eres el asistente virtual premium de Beltrán Briones, un reconocido desarrollador
inmobiliario de Buenos Aires (Grupo Briones). Tu tono es profesional, elegante,
persuasivo y conciso. Respondés siempre en español rioplatense (vos, usted formal
cuando sea apropiado). Mantenés respuestas cortas y directas (máximo 3-4 líneas
por respuesta, salvo que el usuario pida más detalle).

INFORMACIÓN QUE MANEJÁS:
1. Proyectos en pozo (en construcción): Brigos Palermo, Brigos Recoleta y
   Casa Huidobro. Para consultas de inversión, derivar al WhatsApp comercial.
2. El Libro: Beltrán es autor del best seller "El Método Briones: Cómo
   promocionar y vender cualquier cosa", disponible en Mercado Libre.
3. Experiencia: Entregó 12 edificios y 898 departamentos en Buenos Aires.
   Es speaker internacional (Expo Real Estate 1200+ personas, Summit 2025
   Grupo Set, FNS Forum San Juan). +1M seguidores en redes sociales.
4. Contacto comercial: WhatsApp +54 911 2468 2070,
   Email: contacto@grupobriones.com.ar

REGLA ABSOLUTA: Nunca inventes información, precios, rendimientos ni datos
no mencionados arriba. Si no sabés algo, derivá amablemente al contacto de
WhatsApp con un mensaje como: "Para eso te recomiendo contactar directamente
al equipo comercial por WhatsApp: +54 911 2468 2070".
""".strip()

_GEMINI_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    temperature=0.7,
    max_output_tokens=512,
)

# ── Schemas ───────────────────────────────────────────────────────────────────


class HistoryItem(BaseModel):
    role: str = Field(..., pattern="^(user|model)$")
    text: str = Field(..., max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: Optional[List[HistoryItem]] = Field(default=[], max_length=20)


class ChatResponse(BaseModel):
    response: str


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Briones Chatbot API", "version": "2.1.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit("10/minute")
async def chat(request: Request, body: ChatRequest):
    """
    Recibe un mensaje del usuario junto con el historial y retorna
    la respuesta de Gemini.
    - Historial: últimos 20 mensajes (10 intercambios).
    - Rate limit: 10 peticiones/min por IP.
    """
    logger.info(
        "Chat — IP: %s | msg_len: %d | history: %d msgs",
        request.client.host,
        len(body.message),
        len(body.history),
    )

    try:
        # Convertir historial al formato que espera el nuevo SDK
        raw_history = body.history[-20:] if body.history else []
        gemini_history: List[types.ContentDict] = [
            {"role": item.role, "parts": [{"text": item.text}]}
            for item in raw_history
        ]

        # Crear sesión de chat con historial y system instruction
        chat_session = gemini_client.chats.create(
            model=GEMINI_MODEL,
            config=_GEMINI_CONFIG,
            history=gemini_history,
        )

        response = chat_session.send_message(body.message)

        return ChatResponse(response=response.text)

    except genai_errors.ClientError as exc:
        # Contenido bloqueado por políticas de seguridad de Gemini
        logger.warning("ClientError Gemini — IP: %s | %s", request.client.host, exc)
        raise HTTPException(
            status_code=400,
            detail="El mensaje fue bloqueado por políticas de contenido.",
        )
    except genai_errors.ServerError as exc:
        logger.error("ServerError Gemini — %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="El servicio de IA no está disponible en este momento. Intentá de nuevo en unos segundos.",
        )
    except Exception as exc:
        # Error genérico — logueamos detalle real, al cliente mensaje genérico
        logger.error("Error inesperado en /api/chat: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Hubo un inconveniente interno. Por favor intentá de nuevo.",
        )
