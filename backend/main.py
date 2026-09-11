from fastapi import FastAPI

from backend.modules.triage.routes import router as triage_router
from backend.modules.review.routes import router as review_router

# Creamos la aplicación principal de la API.
app = FastAPI(title="PRIO", version="0.1.0")

# Conectamos las rutas del módulo de triaje.
app.include_router(triage_router)
app.include_router(review_router)


# Definimos una ruta para comprobar que la API responde.
@app.get("/health")
def health_check():
    return {"status": "ok"}