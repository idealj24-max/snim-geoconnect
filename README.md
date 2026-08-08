# 🛠️ SNIM GeoConnect Engine

> **Solution Mobile Enterprise-Grade de Gestion des Données Géologiques & Sécurité Minière (HSE) en Mode Offline-First.**
> *Conçue sur-mesure pour les sites d'extraction de la SNIM (Zouérate, Guelbs, Nouadhibou).*

---

## 📌 Présentation du Projet

Le système **snim-geoconnect** résout les défis technologiques majeurs rencontrés au fond des mines à ciel ouvert :
* 📶 **Offline-First (Zéro Réseau) :** Enregistrement des données géologiques et coordonnées GPS directement sur mobile sans connexion internet.
* 🔄 **Synchronisation Automatique :** Fusion intelligente et résolution des conflits de données dès le retour du Wi-Fi à la base.
* 🚨 **Alerte Sécurité Géotechnique (HSE) :** Remontée d'urgence instantanée des risques de fissure ou de glissement de terrain.
* 🛡️ **Souveraineté des Données :** Architecture sécurisée déployable sur les serveurs locaux de la SNIM (On-Premise via Docker).

---

## 🏗️ Architecture Technique (Fichier Unique)

Le projet intègre un moteur autonome dans `main.py` comprenant :
1. **Moteur SQLite embarqué** : Stockage local chiffré sur téléphone.
2. **API Centrale FastAPI** : Serveur centralisé de collecte et gestion d'alertes.
3. **Moteur de synchronisation** : Ingestion batch et validation de données.
4. **Scénario de Démonstration** : Simulation complète d'une mission de forage.

---
## 🚀 Utilisation & Test Rapide

### 1. Mode Simulation Terrain (Hors-Ligne)
```bash
python main.py
 ```
### 2. Démarrage du Serveur API Central
 ```bash
python main.py server
```
*L'API interactive sera accessible sur : `http://localhost:8000/docs`*

---

## 💼 Valeur Stratégique pour la SNIM
* **Gain de productivité :** Suppression de la saisie manuelle papier/Excel (~2h gagnées par géologue/jour).
* **Sécurité des opérations :** Alertes HSE anticipées pour protéger les excavatrices et le personnel.
* **Intégrité de la Data :** Zéro perte de rapports de forages stratégiques.

