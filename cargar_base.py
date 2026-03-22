import os
from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai

# Cargar las variables del .env (asegurate de tener GEMINI_API_KEY y PINECONE_API_KEY ahí)
load_dotenv()

print("Iniciando carga de la base de datos...")

# Inicializar clientes
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("chatbot-inmobiliaria")
ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Este es tu "Catálogo". El día de mañana esto podría venir de un Excel o tu base SQL
propiedades = [
    # ── Proyectos inmobiliarios ───────────────────────────────────────────────
    {
        "id": "proyecto-brigos-palermo",
        "tipo": "desarrollo_en_pozo",
        "texto": "Brigos Palermo: Exclusivo proyecto en pozo en el corazón de Palermo. Departamentos de 2 y 3 ambientes con amenities de lujo (pileta, gimnasio, SUM). Ideal para inversores jóvenes o alquiler temporario. Entrega estimada: Diciembre 2027. Financiación hasta en 36 cuotas en pesos."
    },
    {
        "id": "proyecto-brigos-recoleta",
        "tipo": "desarrollo_en_pozo",
        "texto": "Brigos Recoleta: Emprendimiento premium orientado a familias y público exigente. Unidades de 4 ambientes con dependencia y balcones aterrazados. Seguridad 24hs y terminaciones de primera calidad europea. Entrega estimada: Marzo 2028. Se aceptan propiedades en parte de pago."
    },
    {
        "id": "proyecto-casa-huidobro",
        "tipo": "desarrollo_en_pozo",
        "texto": "Casa Huidobro: Un concepto diferente. Edificio boutique de pocas unidades tipo loft en Belgrano. Pensado para un público moderno que busca diseño y privacidad en una calle arbolada y tranquila. Unidades apto profesional. Últimas 2 unidades disponibles."
    },

    # ── Beltran Briones — perfil personal ────────────────────────────────────
    {
        "id": "info-beltran-perfil",
        "tipo": "informacion_personal",
        "texto": (
            "Beltrán Briones: Desarrollador inmobiliario y empresario de Buenos Aires. "
            "Cofundador de Grupo Briones, una de las desarrolladoras más importantes de CABA. "
            "Tiene más de 15 años de experiencia en el sector inmobiliario. "
            "Vive en el barrio de Recoleta. "
            "Es fanático de River Plate y en su tiempo libre le encanta jugar al tenis. "
            "Su filosofía de vida es el esfuerzo y la innovación constante. "
            "Realizó supervisión internacional de obras en proyectos residenciales premium en Buenos Aires y en Estados Unidos. "
            "Hizo 113 rounds en Call of Duty Black Ops 1 Zombies (dato curioso que comparte con sus seguidores). "
            "Recomienda el barrio de Saavedra como zona de oportunidad para invertir."
        )
    },

    # ── Grupo Briones — empresa ───────────────────────────────────────────────
    {
        "id": "info-grupo-briones",
        "tipo": "informacion_empresa",
        "texto": (
            "Grupo Briones: Empresa desarrolladora inmobiliaria premium de Buenos Aires, cofundada por Beltrán Briones. "
            "Trayectoria y números: más de 12 edificios entregados, 898 departamentos finalizados y más de 1 millón de metros cuadrados desarrollados. "
            "Se especializa en proyectos residenciales de alta gama en los barrios más exclusivos de Buenos Aires: Palermo, Recoleta y Belgrano. "
            "Proyectos actuales en construcción: Brigos Palermo, Brigos Recoleta y Casa Huidobro. "
            "Filosofía: la excelencia constructiva transforma no solo edificios, sino comunidades enteras. "
            "Contacto general: WhatsApp +54 911 2468 2070 | contacto@grupobriones.com.ar. "
            "Terrenos: terrenos@grupobriones.com.ar. "
            "Proveedores: proveedores@grupobriones.com.ar. "
            "Calidad: calidad@grupobriones.com.ar."
        )
    },

    # ── El Club del Ladrillo — podcast ────────────────────────────────────────
    {
        "id": "info-podcast-club-ladrillo",
        "tipo": "informacion_general",
        "texto": (
            "El Club del Ladrillo: Podcast inmobiliario cofundado por Beltrán Briones. "
            "Es el podcast en español más escuchado sobre real estate e inversiones inmobiliarias. "
            "Aborda temas como inversión en propiedades, desarrollo inmobiliario, mercado de Buenos Aires, finanzas personales y estrategias de venta. "
            "Disponible en Spotify y las principales plataformas de podcasts. "
            "Es una herramienta de educación financiera e inmobiliaria, ideal para inversores, emprendedores y profesionales del sector."
        )
    },

    # ── El Método Briones — libro ─────────────────────────────────────────────
    {
        "id": "info-beltran-libro",
        "tipo": "informacion_general",
        "texto": (
            "El Método Briones: Beltrán Briones es el autor del best seller 'El Método Briones: Cómo promocionar y vender cualquier cosa'. "
            "Es el modelo definitivo para dueños de negocio y emprendedores que quieren hacer crecer su posicionamiento y convertirlo en resultados concretos. "
            "Estadísticas del libro: #1 en ventas de su categoría, más de 5.000 lectores, calificación 4.9 estrellas. "
            "Es una lectura obligada para entender la filosofía de trabajo de Grupo Briones. "
            "Se puede adquirir a través de Mercado Libre con envío a todo el país."
        )
    },

    # ── Trayectoria y medios ──────────────────────────────────────────────────
    {
        "id": "info-beltran-trayectoria",
        "tipo": "informacion_trayectoria",
        "texto": (
            "Beltrán Briones — Trayectoria profesional y medios: "
            "Speaker y conferencista en los principales eventos del sector inmobiliario argentino. "
            "Participó en: Summit 2026 (conferencia de liderazgo de Grupo Set), Expo Real Estate CABA (más de 1.200 asistentes) y FNS Forum en San Juan (Foro Nacional de Sustentabilidad e Inversiones). "
            "Docente invitado en universidades de primer nivel: UBA, UADE, UCA y Universidad de San Andrés. "
            "Presencia en medios: mencionado en Forbes Argentina ('El fenómeno que impulsa la inversión inmobiliaria en CABA') "
            "y en Infobae ('De las redes a la obra: cómo Briones revolucionó el Real Estate'). "
            "Activo en redes sociales: Instagram, YouTube, LinkedIn, TikTok y Spotify."
        )
    },

    # ── Metodología de desarrollo ─────────────────────────────────────────────
    {
        "id": "info-metodologia-desarrollo",
        "tipo": "informacion_proceso",
        "texto": (
            "Metodología de desarrollo de Grupo Briones — 5 etapas: "
            "1) Adquisición de terrenos: selección estratégica en barrios premium con análisis de ubicación y potencial. "
            "2) Diseño arquitectónico: colaboración con estudios líderes de arquitectura para crear espacios excepcionales. "
            "3) Construcción: supervisión rigurosa con materiales premium y controles de calidad estrictos en cada etapa de la obra. "
            "4) Comercialización: asesoramiento personalizado desde la preventa hasta la entrega, con financiación en cuotas en pesos. "
            "5) Entrega final: traspaso de la unidad con garantía post-entrega. "
            "En algunos proyectos se aceptan propiedades como parte de pago."
        )
    },

    # ── Propuesta Villa 31 ────────────────────────────────────────────────────
    {
        "id": "info-propuesta-villa31",
        "tipo": "informacion_propuesta",
        "texto": (
            "Propuesta de Beltrán Briones para erradicar la Villa 31: "
            "Beltrán Briones, como desarrollador inmobiliario e influencer, propone erradicar la Villa 31 "
            "mediante un acuerdo público-privado sin que el Estado deba invertir dinero directamente. "
            "Los puntos clave de su plan son: "
            "1) Construcción de viviendas gratis: empresas desarrolladoras privadas construirían 10.000 viviendas "
            "dignas con título de propiedad en una zona de menor densidad poblacional, como el sur de la Ciudad de Buenos Aires. "
            "2) Canje de tierras: a cambio, el Gobierno de la Ciudad entregaría los terrenos actuales de la Villa 31 "
            "(ubicados en una zona de alto valor entre Retiro, Recoleta y Palermo) a los desarrolladores para nuevos proyectos inmobiliarios. "
            "3) Financiamiento íntegramente privado: la alta rentabilidad de las tierras de la villa compensa el costo de las nuevas viviendas. "
            "4) Beneficios para la Ciudad: eliminaría una zona asociada a la precariedad, y el Estado ahorraría en subsidios "
            "de servicios públicos que hoy no se cobran en el asentamiento. "
            "5) Postura ante el desalojo: quienes no tengan escritura o título de propiedad deberían aceptar la nueva vivienda "
            "ofrecida o enfrentar el desalojo por ocupar terrenos estatales."
        )
    },

    # ── Filosofía de inversión ────────────────────────────────────────────────
    {
        "id": "info-filosofia-inversion",
        "tipo": "informacion_inversion",
        "texto": (
            "Filosofía de inversión según Beltrán Briones: "
            "El real estate es la mejor reserva de valor a largo plazo. "
            "Los proyectos en pozo (preventa) ofrecen los mejores precios de entrada y el mayor potencial de revalorización. "
            "Beltrán recomienda el barrio de Saavedra como zona de oportunidad para inversores que buscan precio de entrada accesible con gran proyección. "
            "Los departamentos de Grupo Briones son ideales para alquiler temporario, uso propio o inversión a largo plazo. "
            "Financiación disponible en cuotas en pesos para facilitar el acceso a la inversión inmobiliaria. "
            "La clave del éxito: comprar en pozo en barrios con alta demanda, como Palermo y Recoleta."
        )
    },
]

print("Generando vectores y subiendo a Pinecone (esto puede tardar unos segundos)...")

for prop in propiedades:
    # 1. Generar el vector con Gemini
    response = ai.models.embed_content(
        model='gemini-embedding-001',
        contents=prop["texto"]
    )
    vector = response.embeddings[0].values
    
    # 2. Subir a Pinecone
    index.upsert(
        vectors=[
            {
                "id": prop["id"],
                "values": vector,
                "metadata": {
                    "tipo": prop["tipo"],
                    "texto_original": prop["texto"] # Este es el texto que va a leer el chatbot
                }
            }
        ]
    )
    print(f"✅ Subido con éxito: {prop['id']}")

print("¡Listo! Tu base de datos Pinecone ya tiene información.")