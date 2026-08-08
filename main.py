import sqlite3
import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# --- CONFIGURATION INITIALE & SÉCURITÉ ---
API_KEY_SECRET = "SNIM-GEO-2026-SECURE-KEY"
DB_NAME = "snim_geoconnect.db"

app = FastAPI(
    title="SNIM GeoConnect API",
    description="API Enterprise-Grade pour la collecte géologique et alertes HSE (Offline-First)",
    version="1.0.0"
)

# Activation CORS pour mobile & PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- BASE DE DONNÉES SQLITE ---
def init_sqlite_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Table des relevés géologiques
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS geological_logs (
            id TEXT PRIMARY KEY,
            site TEXT NOT NULL,
            rock_type TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            notes TEXT,
            hse_alert INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            synced_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_sqlite_db()

# --- SÉCURISATION VIA CLE API ---
def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP "401_UNAUTHORIZED",
            detail="Clé API SNIM invalide ou manquante."
        )
    return x_api_key

# --- SCHÉMAS PYDANTIC ---
class GeoLogRecord(BaseModel):
    id: str = Field(..., description="UUID unique généré sur le mobile")
    site: str = Field("Zouérate - Mine à ciel ouvert", description="Site d'extraction")
    rock_type: str = Field(..., description="Ex: BIF, Hématite, Magnetite, Quartz")
    latitude: float
    longitude: float
    notes: Optional[str] = ""
    hse_alert: bool = Field(False, description="Urgence Sécurité / Glissement de terrain")
    created_at: str

class SyncResponse(BaseModel):
    status: str
    processed_count: int
    synced_ids: List[str]

# --- ENDPOINTS API ---

@app.get("/api/health", tags=["Système"])
def health_check():
    return {"status": "ONLINE", "system": "SNIM GeoConnect Engine", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/sync", response_model=SyncResponse, tags=["Synchronisation Terrain"])
def sync_geological_data(records: List[GeoLogRecord], api_key: str = Depends(verify_api_key)):
    """
    Ingestion Batch & Synchronisation Offline-First
    Reçoit les relevés enregistrés hors-ligne sur les téléphones.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    synced_ids = []
    
    now_str = datetime.utcnow().isoformat()

    for item in records:
        cursor.execute("""
            INSERT OR REPLACE INTO geological_logs 
            (id, site, rock_type, latitude, longitude, notes, hse_alert, created_at, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.id,
            item.site,
            item.rock_type,
            item.latitude,
            item.longitude,
            item.notes,
            1 if item.hse_alert else 0,
            item.created_at,
            now_str
        ))
        synced_ids.append(item.id)

    conn.commit()
    conn.close()

    return {
        "status": "SUCCESS",
        "processed_count": len(synced_ids),
        "synced_ids": synced_ids
    }

@app.get("/api/logs", response_model=List[GeoLogRecord], tags=["Consultation Données"])
def get_all_logs(api_key: str = Depends(verify_api_key)):
    """
    Récupère l'ensemble des relevés géologiques centralisés.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, site, rock_type, latitude, longitude, notes, hse_alert, created_at FROM geological_logs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append(GeoLogRecord(
            id=r[0],
            site=r[1],
            rock_type=r[2],
            latitude=r[3],
            longitude=r[4],
            notes=r[5],
            hse_alert=bool(r[6]),
            created_at=r[7]
        ))
    return result

# Service de l'application PWA Frontend
@app.get("/", response_class=FileResponse, tags=["Interface Mobile"])
def read_pwa_app():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
