"""
Briones Chatbot — Backend
FastAPI + Google Gemini 1.5 Flash

Run:  uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Briones Chatbot API",
    description="Asistente virtual de Beltrán Briones impulsado por Google Gemini",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allows requests from the local frontend during development.
# For production, replace allow_origins=["*"] with your domain.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Gemini setup ─────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY no encontrada. "
        "Asegurate de crear un archivo .env con GEMINI_API_KEY=tu_clave"
    )

genai.configure(api_key=GEMINI_API_KEY)

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

gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=genai.GenerationConfig(
        temperature=0.7,
        max_output_tokens=512,
    ),
)

# ── Schemas ───────────────────────────────────────────────────────────────────


class HistoryItem(BaseModel):
    role: str = Field(..., pattern="^(user|model)$")
    text: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: Optional[List[HistoryItem]] = []


class ChatResponse(BaseModel):
    response: str


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Briones Chatbot API"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Recibe un mensaje del usuario junto con el historial de la conversación
    y retorna la respuesta generada por Gemini.

    El historial se limita a los últimos 10 intercambios (20 mensajes)
    para controlar el uso de tokens.
    """
    try:
        # Build history for Gemini (max 20 messages = 10 exchanges)
        raw_history = request.history[-20:] if request.history else []
        gemini_history = [
            {"role": item.role, "parts": [item.text]}
            for item in raw_history
        ]

        chat_session = gemini_model.start_chat(history=gemini_history)
        response = chat_session.send_message(request.message)

        return ChatResponse(response=response.text)

    except genai.types.BlockedPromptException:
        raise HTTPException(
            status_code=400,
            detail="El mensaje fue bloqueado por políticas de contenido.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}",
        )
