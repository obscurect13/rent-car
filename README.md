# 🚗 AutoLoc Pro

Plateforme complète de gestion de location de voitures, construite avec **FastAPI**, **Streamlit** et **SQLite**, orchestrée via **Docker Compose**.

---

## Table des matières

1. [Architecture](#architecture)
2. [Prérequis](#prérequis)
3. [Installation & Lancement](#installation--lancement)
4. [Création du SuperAdmin](#création-du-superadmin)
5. [Structure du projet](#structure-du-projet)
6. [Rôles & Accès](#rôles--accès)
7. [Fonctionnalités par rôle](#fonctionnalités-par-rôle)
8. [API — Référence des endpoints](#api--référence-des-endpoints)
9. [Base de données](#base-de-données)
10. [Scripts utilitaires](#scripts-utilitaires)
11. [Variables d'environnement](#variables-denvironnement)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                     │
│                                                     │
│  ┌──────────────────┐     ┌──────────────────────┐  │
│  │   autoloc-api    │     │    autoloc-ui         │  │
│  │   FastAPI        │◄────│    Streamlit          │  │
│  │   :8000          │     │    :8501              │  │
│  └────────┬─────────┘     └──────────────────────┘  │
│           │                                         │
│  ┌────────▼─────────┐                               │
│  │    db_data       │  Volume Docker persistant     │
│  │    rental.db     │  (SQLite)                     │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘
```

- **Backend** : FastAPI + Uvicorn, expose l'API REST sur le port `8000`
- **Frontend** : Streamlit, interface web sur le port `8501`
- **Base de données** : SQLite stockée dans un volume Docker persistant — les données survivent aux redémarrages
- **Auth** : JWT (JSON Web Tokens) avec expiration 24h

---

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré
- Ports `8000` et `8501` libres sur votre machine

---

## Installation & Lancement

```bash
# 1. Cloner ou extraire le projet
cd car/

# 2. Builder et lancer les conteneurs
docker compose up --build -d

# 3. Vérifier que tout tourne
docker compose ps
```

Les deux conteneurs doivent afficher le statut `healthy` / `running`.

- **Interface web** → http://localhost:8501
- **API (docs interactives)** → http://localhost:8000/docs

### Commandes utiles

```bash
# Voir les logs en temps réel
docker compose logs -f

# Logs d'un seul service
docker compose logs backend --tail=50
docker compose logs frontend --tail=50

# Arrêter les conteneurs (données conservées)
docker compose down

# Arrêter ET supprimer les données
docker compose down -v

# Rebuild après modification du code
docker compose up --build -d
```

---

## Création du SuperAdmin

Le compte SuperAdmin doit être créé **une seule fois** après le premier lancement, via un script interactif. Il n'est **pas** accessible via l'interface web.

```bash
# 1. Copier le script dans le conteneur backend
docker compose cp create_superadmin.py backend:/app/create_superadmin.py

# 2. Exécuter le script (interactif)
docker compose exec -it backend python3 create_superadmin.py
```

Le script demandera :
- Nom complet
- Email
- Mot de passe (6 caractères minimum)

> ⚠️ Un seul SuperAdmin est autorisé. Le script refuse la création si un SuperAdmin existe déjà.

---

## Structure du projet

```
car/
├── api/                        # Modules FastAPI
│   ├── auth.py                 # Authentification JWT + gestion des comptes
│   ├── bookings.py             # Réservations (CRUD + confirm/cancel/complete)
│   ├── cars.py                 # Parc automobile (CRUD + statut + disponibilité)
│   ├── customers.py            # Historique clients par CIN ou téléphone
│   ├── database.py             # Connexion SQLite + initialisation des tables
│   ├── exports.py              # Export CSV des réservations
│   ├── inspections.py          # États des lieux
│   ├── insurance.py            # Suivi des assurances
│   ├── models.py               # Schémas Pydantic
│   ├── payments.py             # Paiements
│   ├── stats.py                # Statistiques tableau de bord
│   ├── user_portal.py          # Portail client (catalogue + réservations)
│   └── validators.py           # Validateurs métier
│
├── backend/
│   ├── Dockerfile              # Image backend (python:3.11-slim)
│   └── main.py                 # Application FastAPI + enregistrement des routers
│
├── frontend/
│   ├── Dockerfile              # Image frontend (python:3.11-slim)
│   └── app.py                  # Application Streamlit (toutes les pages)
│
├── ui/
│   ├── __init__.py
│   └── styles.py               # CSS global de l'interface admin
│
├── data/
│   └── manage.py               # Utilitaire de gestion de la base
│
├── docker-compose.yml          # Orchestration des services
├── requirements.txt            # Dépendances complètes (dev local)
├── requirements-backend.txt    # Dépendances backend uniquement
├── requirements-frontend.txt   # Dépendances frontend uniquement
├── create_superadmin.py        # Script de création du SuperAdmin
├── purge_data.py               # Script de purge des voitures/réservations
└── README.md
```

---

## Rôles & Accès

La plateforme implémente une architecture **multi-tenant** avec 3 rôles distincts :

| Rôle | Description | Création | Accès |
|------|-------------|----------|-------|
| `superadmin` | Propriétaire de la plateforme | Script `create_superadmin.py` uniquement | Gestion de tous les comptes |
| `admin` | Société de location | Inscription via l'interface web | Gestion de sa propre flotte uniquement |
| `user` | Client | Inscription via l'interface web | Portail client (catalogue + ses réservations) |

> **Isolation des données** : chaque compte `admin` ne voit que ses propres voitures et réservations. Le champ `owner_id` sur chaque ressource garantit cette séparation au niveau de la base de données.

---

## Fonctionnalités par rôle

### 🛡️ SuperAdmin
- Voir la liste de tous les comptes inscrits (superadmin, admin, user)
- Changer le rôle d'un compte (admin ↔ user)
- Supprimer un compte
- Tableau de bord avec métriques globales (total comptes, admins, clients)

### 🏢 Admin (Société de location)
| Page | Fonctionnalités |
|------|----------------|
| 📊 Tableau de bord | KPIs : voitures, réservations, chiffre d'affaires, retards, paiements |
| ➕ Ajouter une voiture | Formulaire complet avec listes déroulantes (marque → modèle dynamique, couleur, équipements) |
| 📋 Parc automobile | Liste filtrée, calendrier de disponibilité, maintenance, modification, suppression |
| 📅 Nouvelle réservation | Sélection de dates → voitures disponibles → formulaire client → contrat PDF |
| 🗂️ Réservations | Tabs : ⏳ En attente / ✅ Confirmées / 🏁 Terminées / ❌ Annulées — Confirmer/Refuser les demandes clients, mise à jour des paiements, export CSV |
| 👤 Clients | Recherche par CIN ou téléphone, historique complet, solde restant dû |
| ⚠️ Retards | Réservations dont la date de fin est dépassée |

### 👤 Client (User)
| Page | Fonctionnalités |
|------|----------------|
| 🔍 Catalogue | Filtres par dates, catégorie, budget, places — prix estimé pour la période |
| 📋 Mes réservations | Historique avec statuts colorés, annulation des demandes en attente |

---

## API — Référence des endpoints

### Authentification — `/auth`
| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/auth/register` | Non | Créer un compte (admin ou user) |
| POST | `/auth/login` | Non | Connexion → retourne un JWT |
| GET | `/auth/me` | JWT | Infos du compte connecté |
| GET | `/auth/users` | SuperAdmin | Liste tous les comptes |
| PATCH | `/auth/users/{id}/role` | SuperAdmin | Changer le rôle d'un compte |
| DELETE | `/auth/users/{id}` | SuperAdmin | Supprimer un compte |

### Parc automobile — `/cars`
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/cars` | Liste les voitures de l'admin connecté |
| POST | `/cars` | Ajouter une voiture |
| GET | `/cars/search/available` | Voitures disponibles pour une période donnée |
| GET | `/cars/{id}` | Détail d'une voiture |
| PUT | `/cars/{id}` | Modifier une voiture |
| PATCH | `/cars/{id}/status` | Changer le statut (available / maintenance) |
| DELETE | `/cars/{id}` | Supprimer une voiture |

### Réservations — `/bookings`
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/bookings` | Liste les réservations (filtrable par statut) |
| GET | `/bookings/overdue` | Réservations en retard |
| POST | `/bookings` | Créer une réservation (admin) |
| GET | `/bookings/{id}` | Détail d'une réservation |
| PUT | `/bookings/{id}` | Modifier une réservation |
| PATCH | `/bookings/{id}/confirm` | Confirmer une demande client (pending → confirmed) |
| PATCH | `/bookings/{id}/cancel` | Annuler une réservation |
| PATCH | `/bookings/{id}/complete` | Marquer comme terminée |
| PATCH | `/bookings/{id}/payment` | Mettre à jour le paiement |

### Portail client — `/portal`
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/portal/cars` | Catalogue public des voitures disponibles |
| GET | `/portal/cars/{id}` | Détail + créneaux réservés |
| POST | `/portal/bookings` | Soumettre une demande de réservation |
| GET | `/portal/my-bookings` | Mes réservations |
| DELETE | `/portal/my-bookings/{id}` | Annuler une de mes réservations |

### Autres endpoints
| Préfixe | Description |
|---------|-------------|
| `/customers` | Recherche et historique clients par CIN ou téléphone |
| `/stats` | Statistiques du tableau de bord |
| `/export` | Export CSV des réservations |
| `/inspections` | États des lieux |
| `/insurance` | Suivi des assurances |
| `/payments` | Gestion des paiements |
| `/health` | Health check public (utilisé par Docker) |

> 📖 Documentation interactive complète disponible sur **http://localhost:8000/docs**

---

## Base de données

SQLite avec les tables suivantes :

| Table | Description |
|-------|-------------|
| `users` | Comptes (superadmin, admin, user) |
| `cars` | Véhicules — filtrés par `owner_id` |
| `bookings` | Réservations — filtrées par `owner_id` |
| `inspections` | États des lieux liés aux réservations |
| `insurance_tracking` | Suivi des assurances par véhicule |
| `payments` | Paiements associés aux réservations |

Le champ `owner_id` sur `cars` et `bookings` garantit l'isolation des données entre les sociétés.

---

## Scripts utilitaires

### Créer le SuperAdmin
```bash
docker compose cp create_superadmin.py backend:/app/create_superadmin.py
docker compose exec -it backend python3 create_superadmin.py
```

### Purger les voitures et réservations
```bash
docker compose cp purge_data.py backend:/app/purge_data.py
docker compose exec -it backend python3 purge_data.py
```
> Demande confirmation en tapant `CONFIRMER`. Conserve les comptes utilisateurs.

### Vérifier l'état de la base
```bash
docker compose cp check_db.py backend:/app/check_db.py
docker compose exec backend python3 check_db.py
```

---

## Variables d'environnement

| Variable | Service | Valeur par défaut | Description |
|----------|---------|-------------------|-------------|
| `DB_PATH` | Backend | `/app/data/rental.db` | Chemin vers la base SQLite |
| `API_URL` | Frontend | `http://localhost:8000` | URL du backend (réseau interne Docker : `http://backend:8000`) |

---

## Flux de réservation client

```
Client (user)                    Admin (société)
     │                                │
     │  Parcourt le catalogue         │
     │  Choisit une voiture           │
     │  Soumet une demande ──────────►│
     │                                │  Voit la demande dans
     │                                │  l'onglet "⏳ En attente"
     │                                │
     │◄── Statut: "✅ Confirmée" ─────│  Clique "✅ Confirmer"
     │         ou                     │         ou
     │◄── Statut: "❌ Annulée" ───────│  Clique "❌ Refuser"
     │                                │
```

---

*AutoLoc Pro v2.0 — Développé avec FastAPI, Streamlit et Docker*
