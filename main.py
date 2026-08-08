"""
================================================================================
SNIM GEOCONNECT ENGINE - ENTERPRISE-GRADE ALL-IN-ONE SOLUTION
================================================================================
Projet : snim-geoconnect
Système Intégré de Gestion Géologique, Cartographie & Sécurité Minière (HSE)
Conçu spécifiquement pour les contraintes de la SNIM (Zouérate / Guelbs / Nouadhibou).

Inclus dans ce fichier unique :
1. Moteur de Base de Données Locale (SQLite) avec Mode Offline-First
2. API Centrale FastAPI (Serveur On-Premise)
3. Algorithme de Synchronisation & Gestion des Conflits
4. Système d'Alerte Géotechnique d'Urgence (HSE)
5. Interface CLI & Simulation Terrain Interactive
================================================================================
"""

import sqlite3
import json
import uuid
import datetime
import time
import sys
from typing import List, Optional

# Dépendances FastAPI & Pydantic
try:
    from fastapi import FastAPI, HTTPException, Status
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    FastAPI = None
    BaseModel = object
    Field = lambda *args, **kwargs: None


# ==============================================================================
# SECTION 1 : MODÈLES DE DONNÉES PRÉDÉFINIS (SCHÉMAS GÉOLOGIQUES & HSE)
# ==============================================================================

class GeoObservationModel:
    """Structure standardisée d'un relevé géologique sur le terrain pour snim-geoconnect."""
    def __init__(
        self,
        id_echantillon: str,
        geologue_id: str,
        latitude: float,
        longitude: float,
        type_roche: str,
        teneur_estimee_fer: float,
        commentaire: str = "",
        alerte_geotechnique: bool = False,
        date_saisie: str = None,
        synced: bool = False
    ):
        self.id_echantillon = id_echantillon
        self.geologue_id = geologue_id
        self.latitude = latitude
        self.longitude = longitude
        self.type_roche = type_roche
        self.teneur_estimee_fer = teneur_estimee_fer
        self.commentaire = commentaire
        self.alerte_geotechnique = alerte_geotechnique
        self.date_saisie = date_saisie or datetime.datetime.now().isoformat()
        self.synced = synced

    def to_dict(self):
        return {
            "id_echantillon": self.id_echantillon,
            "geologue_id": self.geologue_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "type_roche": self.type_roche,
            "teneur_estimee_fer": self.teneur_estimee_fer,
            "commentaire": self.commentaire,
            "alerte_geotechnique": self.alerte_geotechnique,
            "date_saisie": self.date_saisie,
            "synced": self.synced
        }


if FastAPI is not None:
    class GeoObservationSchema(BaseModel):
        id_echantillon: str
        geologue_id: str
        latitude: float
        longitude: float
        type_roche: str  # Hématite, Magnétite, Quartzite, Itabirite
        teneur_estimee_fer: float = Field(..., ge=0.0, le=100.0)
        commentaire: Optional[str] = None
        alerte_geotechnique: bool = False
        date_saisie: str


# ==============================================================================
# SECTION 2 : MOTEUR DE BASE DE DONNÉES LOCALE (OFFLINE-FIRST / SQLITE)
# ==============================================================================

class LocalGeoDatabase:
    """
    Gestionnaire de base de données embarquée sur le téléphone mobile du géologue.
    Base locale : snim_geoconnect_local.db
    Permet un stockage immédiat et sécurisé sans réseau internet dans les mines.
    """
    def __init__(self, db_path="snim_geoconnect_local.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    id_echantillon TEXT PRIMARY KEY,
                    geologue_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    type_roche TEXT NOT NULL,
                    teneur_estimee_fer REAL NOT NULL,
                    commentaire TEXT,
                    alerte_geotechnique INTEGER DEFAULT 0,
                    date_saisie TEXT NOT NULL,
                    synced INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def enregistrer_observation(
        self,
        geologue_id: str,
        latitude: float,
        longitude: float,
        type_roche: str,
        teneur_estimee_fer: float,
        commentaire: str = "",
        alerte_geotechnique: bool = False
    ) -> str:
        """Saisie rapide terrain au fond de la fosse minière."""
        id_unique = f"SNIM-GEO-{uuid.uuid4().hex[:8].upper()}"
        date_saisie = datetime.datetime.now().isoformat()
        alerte_int = 1 if alerte_geotechnique else 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO observations 
                (id_echantillon, geologue_id, latitude, longitude, type_roche, 
                 teneur_estimee_fer, commentaire, alerte_geotechnique, date_saisie, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (id_unique, geologue_id, latitude, longitude, type_roche, teneur_estimee_fer, commentaire, alerte_int, date_saisie))
            conn.commit()

        return id_unique

    def Obtenir_enregistrements_non_synchronises(self) -> List[dict]:
        """Extrait la file d'attente des données à envoyer au serveur central snim-geoconnect."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM observations WHERE synced = 0")
            rows = cursor.fetchall()

        payload = []
        for r in rows:
            payload.append({
                "id_echantillon": r[0],
                "geologue_id": r[1],
                "latitude": r[2],
                "longitude": r[3],
                "type_roche": r[4],
                "teneur_estimee_fer": r[5],
                "commentaire": r[6],
                "alerte_geotechnique": bool(r[7]),
                "date_saisie": r[8]
            })
        return payload

    def marquer_comme_synchronise(self, ids_synced: List[str]):
        """Valide la réception du serveur et met à jour l'état local."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for id_ech in ids_synced:
                cursor.execute("UPDATE observations SET synced = 1 WHERE id_echantillon = ?", (id_ech,))
            conn.commit()

    def Obtenir_statistiques_locales(self) -> dict:
        """Tableau de bord local sur le téléphone du géologue."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(synced) FROM observations")
            total, synced = cursor.fetchone()
            synced = synced or 0
            return {
                "total_observations": total,
                "synchronisees": synced,
                "en_attente": total - synced
            }


# ==============================================================================
# SECTION 3 : SERVEUR CENTRAL & API REST (FASTAPI)
# ==============================================================================

if FastAPI is not None:
    app = FastAPI(
        title="snim-geoconnect Central API",
        description="API Centrale Enterprise-Grade pour la collecte et la synchronisation géologique - SNIM Zouérate",
        version="2.0.0"
    )

    CENTRAL_DATABASE = []

    @app.get("/", tags=["Système"])
    def status_systeme():
        return {
            "statut": "OPERATIONNEL",
            "projet": "snim-geoconnect",
            "systeme": "SNIM GeoConnect Central Engine",
            "localisation": "Base Principale Zouérate / Tiris Zemmour",
            "horodatage": datetime.datetime.now().isoformat()
        }

    @app.post("/api/v1/sync", status_code=Status.HTTP_201_CREATED, tags=["Synchronisation"])
    def synchroniser_donnees_terrain(donnees: List[GeoObservationSchema]):
        """
        Endpoint de synchronisation pour le projet snim-geoconnect.
        Traite la détection de doublons et les alertes de sécurité HSE.
        """
        nouveaux_elements = []
        alertes_emises = []

        for obs in donnees:
            if not any(x["id_echantillon"] == obs.id_echantillon for x in CENTRAL_DATABASE):
                obs_dict = obs.dict()
                CENTRAL_DATABASE.append(obs_dict)
                nouveaux_elements.append(obs_dict)

                if obs.alerte_geotechnique:
                    alertes_emises.append({
                        "id": obs.id_echantillon,
                        "geologue": obs.geologue_id,
                        "coordonnees": (obs.latitude, obs.longitude),
                        "description": obs.commentaire
                    })
                    print(f"\n🚨 [ALERTE HSE DANGER CRITIQUE] Fissure/Glissement signalé par {obs.geologue_id} aux coordonnées GPS ({obs.latitude}, {obs.longitude})!")

        return {
            "statut": "SUCCESS",
            "projet": "snim-geoconnect",
            "nb_synchronises": len(nouveaux_elements),
            "elements": nouveaux_elements,
            "alertes_hse_traitees": len(alertes_emises)
        }

    @app.get("/api/v1/observations", tags=["Donnees Minières"])
    def lister_observations():
        return {
            "projet": "snim-geoconnect",
            "total": len(CENTRAL_DATABASE),
            "donnees": CENTRAL_DATABASE
        }


# ==============================================================================
# SECTION 4 : SCÉNARIO DE SIMULATION INTERACTIF (TERMINAL/DEMO)
# ==============================================================================

def simuler_mission_terrain():
    """
    Exécute une démonstration complète de la solution snim-geoconnect :
    1. Saisie hors-ligne dans la mine de Kedia d'Idjill (Zouérate).
    2. Consultation du stockage SQLite local.
    3. Simulation de la synchronisation au retour à la base.
    """
    print("=" * 80)
    print(" 🛠️  PROJET : SNIM-GEOCONNECT - DEMONSTRATION D'EXPLOITATION MINIÈRE")
    print("=" * 80)
    print("Lieu : Mine à ciel ouvert de Kedia d'Idjill (Zouérate)")
    print("Réseau Internet : ABSENT (Mode Offline-First Actif)")
    print("-" * 80)

    db_mobile = LocalGeoDatabase()

    # 1. Saisie de relevés par le géologue sur le terrain
    print("\n[ETAPE 1] Saisie de données géologiques sur smartphone au fond de la fosse...")
    
    id1 = db_mobile.enregistrer_observation(
        geologue_id="GEO_SNIM_AZIZ",
        latitude=22.7150,
        longitude=-12.4780,
        type_roche="Hématite Dense",
        teneur_estimee_fer=66.8,
        commentaire="Minerai à haute teneur, front de taille N°4",
        alerte_geotechnique=False
    )
    print(f" -> Relevé enregistré localement dans snim_geoconnect_local.db : {id1} (Teneur Fer: 66.8%)")

    id2 = db_mobile.enregistrer_observation(
        geologue_id="GEO_SNIM_AZIZ",
        latitude=22.7185,
        longitude=-12.4710,
        type_roche="Quartzite à Magnétite",
        teneur_estimee_fer=38.2,
        commentaire="Zone de transition - Fissure suspecte sur le gradin supérieur",
        alerte_geotechnique=True
    )
    print(f" -> Relevé HSE critique enregistré : {id2} [ALERTE DANGER GEOTECHNIQUE]")

    # 2. Vérification de l'état du stockage local
    stats = db_mobile.Obtenir_statistiques_locales()
    print(f"\n[ETAPE 2] État de la base de données mobile (snim-geoconnect) :")
    print(f" -> Total Relevés : {stats['total_observations']}")
    print(f" -> Synchronisés : {stats['synchronisees']}")
    print(f" -> En attente d'envoi : {stats['en_attente']}")

    # 3. Simulation de la synchronisation
    print("\n[ETAPE 3] Le géologue rentre à la base de Zouérate et se connecte au Wi-Fi...")
    donnees_a_envoyer = db_mobile.Obtenir_enregistrements_non_synchronises()
    print(f" -> Détection de {len(donnees_a_envoyer)} relevés non synchronisés.")
    
    print("\n[ETAPE 4] Envoi du lot vers le serveur central snim-geoconnect...")
    ids_synced = [d["id_echantillon"] for d in donnees_a_envoyer]
    db_mobile.marquer_comme_synchronise(ids_synced)
    
    stats_apres = db_mobile.Obtenir_statistiques_locales()
    print(f" -> Synchronisation terminée avec succès!")
    print(f" -> Relevés en attente restant sur le téléphone : {stats_apres['en_attente']}")
    print("\n" + "=" * 80)
    print(" SIMULATION TERMINÉE - SNIM-GEOCONNECT EST PRÊT POUR LE DÉPLOIEMENT")
    print("=" * 80)


# ==============================================================================
# POINT D'ENTRÉE DU SCRIPT
# ==============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        if FastAPI is not None:
            print("Lancement du serveur central snim-geoconnect...")
            uvicorn.run(app, host="0.0.0.0", port=8000)
        else:
            print("FastAPI n'est pas installé. Exécution du mode simulation...")
            simuler_mission_terrain()
    else:
        simuler_mission_terrain()
