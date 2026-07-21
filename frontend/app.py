import streamlit as st
import requests
from datetime import date, timedelta
import pandas as pd
import html as _html
import calendar

import os as _os
API = _os.environ.get("API_URL", "http://localhost:8000")

# ═══════════════════════════════════════════════════════════════════════════
# AUTH HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def auth_api(method, path, data=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = getattr(requests, method)(
            f"{API}{path}", json=data, headers=headers, timeout=8
        )
        return r
    except Exception as e:
        st.error(f"Erreur connexion API : {e}")
        return None

def is_logged_in():
    return bool(st.session_state.get("token"))

def get_role():
    return st.session_state.get("role", "")

def logout():
    for k in ["token", "role", "full_name", "user_id"]:
        st.session_state.pop(k, None)
    st.rerun()


# ── Données des listes déroulantes ──────────────────────────────────────────

# ── Import styles from ui/styles.py ────────────────────────────────────────
from ui.styles import get_global_styles, get_car_card_styles

MARQUES = [
    "Dacia", "Renault", "Peugeot", "Citroën", "Ford", "Toyota", "Honda",
    "Hyundai", "Kia", "Volkswagen", "BMW", "Mercedes-Benz", "Audi",
    "Seat", "Skoda", "Fiat", "Opel", "Nissan", "Mazda", "Suzuki",
    "Mitsubishi", "Chevrolet", "Jeep", "Land Rover", "Volvo", "Autre"
]

MODELES = {
    "Dacia":         ["Logan", "Sandero", "Duster", "Spring", "Jogger", "Autre"],
    "Renault":       ["Clio", "Megane", "Kadjar", "Captur", "Scenic", "Trafic", "Autre"],
    "Peugeot":       ["208", "308", "2008", "3008", "5008", "Partner", "Autre"],
    "Citroën":       ["C3", "C4", "Berlingo", "C5 Aircross", "Autre"],
    "Ford":          ["Fiesta", "Focus", "Kuga", "EcoSport", "Transit", "Autre"],
    "Toyota":        ["Yaris", "Corolla", "RAV4", "Hilux", "Land Cruiser", "Autre"],
    "Honda":         ["Civic", "CR-V", "HR-V", "Jazz", "Autre"],
    "Hyundai":       ["i10", "i20", "i30", "Tucson", "Santa Fe", "Autre"],
    "Kia":           ["Picanto", "Rio", "Sportage", "Sorento", "Autre"],
    "Volkswagen":    ["Polo", "Golf", "Tiguan", "Passat", "Caddy", "Autre"],
    "BMW":           ["Série 1", "Série 3", "Série 5", "X1", "X3", "X5", "Autre"],
    "Mercedes-Benz": ["Classe A", "Classe C", "Classe E", "GLA", "GLC", "Vito", "Autre"],
    "Audi":          ["A1", "A3", "A4", "Q3", "Q5", "Autre"],
    "Seat":          ["Ibiza", "Leon", "Arona", "Ateca", "Autre"],
    "Skoda":         ["Fabia", "Octavia", "Karoq", "Kodiaq", "Autre"],
    "Fiat":          ["500", "Panda", "Tipo", "Doblo", "Ducato", "Autre"],
    "Opel":          ["Corsa", "Astra", "Mokka", "Crossland", "Autre"],
    "Nissan":        ["Micra", "Juke", "Qashqai", "X-Trail", "Navara", "Autre"],
    "Mazda":         ["Mazda2", "Mazda3", "CX-3", "CX-5", "Autre"],
    "Suzuki":        ["Alto", "Swift", "Vitara", "Jimny", "Autre"],
    "Mitsubishi":    ["Space Star", "ASX", "Outlander", "L200", "Autre"],
    "Chevrolet":     ["Spark", "Aveo", "Trax", "Captiva", "Autre"],
    "Jeep":          ["Renegade", "Compass", "Wrangler", "Cherokee", "Autre"],
    "Land Rover":    ["Defender", "Discovery", "Range Rover", "Freelander", "Autre"],
    "Volvo":         ["V40", "V60", "XC40", "XC60", "XC90", "Autre"],
    "Autre":         ["Autre"],
}

COULEURS = [
    "Blanc", "Blanc nacré", "Noir", "Gris", "Gris métallisé", "Argent",
    "Bleu", "Bleu marine", "Bleu ciel", "Rouge", "Rouge bordeaux",
    "Vert", "Vert foncé", "Beige", "Marron", "Orange", "Jaune", "Violet", "Autre"
]

EQUIPEMENTS = [
    "Climatisation", "Climatisation automatique", "GPS / Navigation",
    "Bluetooth / USB", "Caméra de recul", "Radar de recul",
    "Régulateur de vitesse", "Vitres électriques", "Toit ouvrant",
    "Sièges chauffants", "Aide au stationnement", "Démarrage sans clé",
    "Roue de secours", "Galerie de toit", "Attelage remorque",
    "Apple CarPlay / Android Auto", "Écran tactile", "Coffre électrique"
]

STATUS_OPTIONS = ["available", "maintenance", "retired"]
STATUS_LABELS = {"available": "Disponible", "maintenance": "En maintenance", "retired": "Retiré"}
PAYMENT_LABELS = {"cash": "Espèces", "card": "Carte bancaire", "transfer": "Virement", "deposit": "Caution"}

# ═══════════════════════════════════════════════════════════════════════════
# PAGES LOGIN / REGISTER
# ═══════════════════════════════════════════════════════════════════════════
def render_auth():
    """Page d'authentification et d'inscription."""
    st.set_page_config(page_title="AutoLoc Pro — Connexion", page_icon="🔑", layout="centered")
    
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: Inter, sans-serif; background: #0F172A; }
    .main .block-container { max-width: 460px; padding-top: 4rem; }
    .auth-logo { text-align:center; font-size:2.5rem; margin-bottom:0.5rem; }
    .auth-title { text-align:center; font-size:1.6rem; font-weight:700;
                  color:#F1F5F9; margin-bottom:0.25rem; }
    .auth-sub { text-align:center; color:#94A3B8; font-size:.9rem; margin-bottom:2rem; }
    div[data-testid="stForm"] {
        background:#1E293B; border-radius:16px; padding:28px 32px;
        border:1px solid #334155; box-shadow:0 8px 32px rgba(0,0,0,.4);
    }
    label, div[data-testid="stWidgetLabel"] p { color:#CBD5E1 !important; font-weight:600 !important; }
    input { color:#F1F5F9 !important; background:#0F172A !important;
            -webkit-text-fill-color:#F1F5F9 !important; }
    div[data-baseweb="input"] { background:#0F172A !important; border-color:#475569 !important; }
    .stButton > button {
        background:#2563EB !important; color:white !important; border:none !important;
        border-radius:8px !important; font-weight:700 !important; font-size:1rem !important;
        padding:0.6rem 1.5rem !important; width:100%;
    }
    .stButton > button:hover { background:#1D4ED8 !important; }
    .role-admin { background:#1E3A5F; border:2px solid #3B82F6; border-radius:12px;
                  padding:16px 20px; cursor:pointer; transition:.2s; }
    .role-user  { background:#14532D; border:2px solid #22C55E; border-radius:12px;
                  padding:16px 20px; cursor:pointer; transition:.2s; }
    .role-card p { margin:0; }
    .role-card .icon { font-size:2rem; }
    .role-card .title { font-size:1rem; font-weight:700; color:#F1F5F9; margin-top:4px; }
    .role-card .desc  { font-size:.8rem; color:#94A3B8; margin-top:2px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-logo">🚗</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">AutoLoc Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-sub">Plateforme de gestion de location</div>', unsafe_allow_html=True)

    mode = st.radio("Mode d'authentification", ["🔑 Se connecter", "📝 Créer un compte"],
                    horizontal=True, label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)

    if mode == "🔑 Se connecter":
        with st.form("login_form"):
            email    = st.text_input("Email", placeholder="vous@exemple.com")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Connexion", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Veuillez remplir tous les champs.")
            else:
                r = auth_api("post", "/auth/login", {"email": email, "password": password})
                if r and r.status_code == 200:
                    d = r.json()
                    st.session_state["token"]     = d["access_token"]
                    st.session_state["role"]      = d["role"]
                    st.session_state["full_name"] = d["full_name"]
                    st.session_state["user_id"]   = d["user_id"]
                    st.rerun()
                elif r:
                    st.error(r.json().get("detail", "Erreur de connexion"))

    else:
        # ── Choix du rôle ──
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("""
            <div class="role-card role-admin">
                <p class="icon">🏢</p>
                <p class="title">Administrateur</p>
                <p class="desc">Gérer la flotte, les réservations et les clients</p>
            </div>""", unsafe_allow_html=True)
        with col_r2:
            st.markdown("""
            <div class="role-card role-user">
                <p class="icon">👤</p>
                <p class="title">Client</p>
                <p class="desc">Parcourir les véhicules et faire des réservations</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        role_choice = st.selectbox("Vous êtes :", ["👤 Client", "🏢 Administrateur"])
        role = "admin" if "Administrateur" in role_choice else "user"

        with st.form("register_form"):
            full_name = st.text_input("Nom complet *", placeholder="Ahmed Bennani")
            email     = st.text_input("Email *", placeholder="vous@exemple.com")
            phone     = st.text_input("Téléphone", placeholder="06XXXXXXXX")
            cin       = st.text_input("CIN", placeholder="AB123456") if role == "user" else None
            password  = st.text_input("Mot de passe *", type="password")
            password2 = st.text_input("Confirmer le mot de passe *", type="password")
            submitted = st.form_submit_button("Créer mon compte", use_container_width=True)

        if submitted:
            errors = []
            if not full_name or not email or not password:
                errors.append("Les champs * sont obligatoires")
            if password != password2:
                errors.append("Les mots de passe ne correspondent pas")
            if len(password) < 6:
                errors.append("Mot de passe : 6 caractères minimum")
            if errors:
                for e in errors: st.error(e)
            else:
                payload = {"full_name": full_name, "email": email,
                           "phone": phone or None, "cin": cin or None,
                           "password": password, "role": role}
                r = auth_api("post", "/auth/register", payload)
                if r and r.status_code == 201:
                    d = r.json()
                    st.session_state["token"]     = d["access_token"]
                    st.session_state["role"]      = d["role"]
                    st.session_state["full_name"] = d["full_name"]
                    st.session_state["user_id"]   = d["user_id"]
                    st.success(f"Compte créé ! Bienvenue {d['full_name']} 🎉")
                    st.rerun()
                elif r:
                    st.error(r.json().get("detail", "Erreur lors de l'inscription"))


# ═══════════════════════════════════════════════════════════════════════════
# PORTAIL CLIENT (role=user)
# ═══════════════════════════════════════════════════════════════════════════
def render_user_portal():
    """Interface dédiée aux clients."""
    st.set_page_config(page_title="AutoLoc — Catalogue", page_icon="🚘", layout="wide")

    token     = st.session_state.get("token")
    full_name = st.session_state.get("full_name", "Client")

    def papi(method, path, **kwargs):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            return getattr(requests, method)(f"{API}{path}", headers=headers, timeout=8, **kwargs)
        except Exception as e:
            st.error(str(e)); return None

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("## 🚘 AutoLoc Pro")
        st.markdown(f"**{full_name}**")
        st.markdown("---")
        page = st.radio("Page de navigation", ["🔍 Catalogue", "📋 Mes réservations"],
                        label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Déconnexion", use_container_width=True):
            logout()

    # ── Styles ──
    st.markdown("""<style>
    .car-portal-card {
        background:#1E293B; border-radius:14px; padding:20px 22px;
        border-left:4px solid #3B82F6; margin-bottom:14px;
        box-shadow:0 2px 10px rgba(0,0,0,.2);
    }
    .car-portal-title { font-size:1.1rem; font-weight:700; color:#F1F5F9; margin:0 0 4px; }
    .car-portal-rate  { font-size:1.3rem; font-weight:800; color:#34D399; }
    .car-portal-meta  { color:#CBD5E1; font-size:.85rem; margin-top:8px; line-height:1.8; }
    .booking-status-pending   { background:#FEF3C7; color:#92400E; padding:2px 10px;
                                border-radius:20px; font-size:.75rem; font-weight:700; }
    .booking-status-confirmed { background:#DCFCE7; color:#166534; padding:2px 10px;
                                border-radius:20px; font-size:.75rem; font-weight:700; }
    .booking-status-cancelled { background:#FEE2E2; color:#991B1B; padding:2px 10px;
                                border-radius:20px; font-size:.75rem; font-weight:700; }
    .booking-status-completed { background:#EDE9FE; color:#5B21B6; padding:2px 10px;
                                border-radius:20px; font-size:.75rem; font-weight:700; }
    .btn-book .stButton > button {
        background:#2563EB !important; color:white !important;
        border:none !important; font-weight:700 !important; border-radius:8px !important;
    }
    .btn-cancel-user .stButton > button {
        background:#DC2626 !important; color:white !important;
        border:none !important; font-weight:600 !important; border-radius:8px !important;
    }
    </style>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════
    if page == "🔍 Catalogue":
        st.title("Catalogue des véhicules")
        st.caption("Trouvez et réservez le véhicule qui vous convient")

        # ── Filtres ──
        with st.expander("🔎 Filtres de recherche", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("📅 Date de prise en charge",
                                            value=date.today() + timedelta(days=1),
                                            min_value=date.today())
            with col2:
                end_date = st.date_input("📅 Date de restitution",
                                          value=date.today() + timedelta(days=3),
                                          min_value=date.today() + timedelta(days=1))

            col3, col4, col5 = st.columns(3)
            with col3:
                cat_filter = st.selectbox("Catégorie", ["Toutes","Citadine","Berline",
                                                         "SUV","Utilitaire","Luxe","Monospace"])
            with col4:
                max_rate = st.number_input("Budget max (MAD/j)", min_value=0, value=0, step=50)
            with col5:
                seats_filter = st.number_input("Places min.", min_value=0, value=0, step=1)

        if start_date >= end_date:
            st.error("La date de fin doit être après la date de début.")
            return

        days = (end_date - start_date).days
        params = {"start_date": str(start_date), "end_date": str(end_date)}
        if cat_filter != "Toutes": params["category"] = cat_filter
        if max_rate > 0: params["max_rate"] = max_rate
        if seats_filter > 0: params["seats"] = seats_filter

        r = papi("get", "/portal/cars", params=params)
        if not r or r.status_code != 200:
            st.error("Impossible de charger le catalogue.")
            return

        cars = r.json()
        st.caption(f"**{len(cars)} véhicule(s) disponible(s)** pour {days} jour(s)")

        if not cars:
            st.info("Aucun véhicule disponible pour ces critères. Essayez d'autres dates.")
            return

        for car in cars:
            total_est = car["daily_rate"] * days
            notes_p = f"<p style='margin:6px 0 0;font-size:.82rem;color:#64748B;font-style:italic'>📝 {_html.escape(str(car['notes']))}</p>" if car.get("notes") else ""
            card = (
                "<div class='car-portal-card'>"
                "<div style='display:flex;justify-content:space-between;align-items:flex-start'>"
                "<div>"
                f"<p class='car-portal-title'>🚗 {_html.escape(car['brand'])} {_html.escape(car['model'])} ({car['year']})</p>"
                f"<span style='display:inline-block;background:#1D4ED8;color:#DBEAFE;font-size:.76rem;font-weight:700;padding:2px 9px;border-radius:5px'>{_html.escape(car['license_plate'])}</span>"
                f"&nbsp;<span style='background:#DCFCE7;color:#166534;font-size:.75rem;font-weight:700;padding:2px 9px;border-radius:20px'>Disponible</span>"
                "</div>"
                f"<div style='text-align:right'><p class='car-portal-rate'>{int(car['daily_rate'])} MAD/j</p>"
                f"<p style='margin:2px 0 0;font-size:.8rem;color:#6EE7B7'>≈ {int(total_est):,} MAD pour {days}j</p></div>"
                "</div>"
                f"<div class='car-portal-meta'>⛽ {_html.escape(car['fuel_type'])} &nbsp;·&nbsp; ⚙️ {_html.escape(car['transmission'])} &nbsp;·&nbsp; 🎨 {_html.escape(car['color'])} &nbsp;·&nbsp; 💺 {car['seats']} places &nbsp;·&nbsp; 🏷️ {_html.escape(car['category'])}</div>"
                + notes_p +
                "</div>"
            )
            st.markdown(card, unsafe_allow_html=True)

            col_a, col_b = st.columns([4, 1])
            with col_b:
                st.markdown('<div class="btn-book">', unsafe_allow_html=True)
                if st.button("📅 Réserver", key=f"book_{car['id']}_{start_date}_{end_date}", use_container_width=True):
                    st.session_state["booking_car"]   = car
                    st.session_state["booking_start"] = str(start_date)
                    st.session_state["booking_end"]   = str(end_date)
                    st.session_state["booking_days"]  = days
                    st.session_state["show_booking_form"] = True
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Formulaire de réservation inline ──
            if st.session_state.get("show_booking_form") and st.session_state.get("booking_car", {}).get("id") == car["id"]:
                sel = st.session_state["booking_car"]
                total = sel["daily_rate"] * st.session_state["booking_days"]
                st.markdown(f"""
                <div style='background:#0F172A;border:1.5px solid #3B82F6;border-radius:12px;
                            padding:20px 24px;margin:8px 0 16px'>
                    <p style='margin:0 0 4px;font-size:1rem;font-weight:700;color:#F1F5F9'>
                        📋 Demande de réservation — {sel['brand']} {sel['model']}
                    </p>
                    <p style='margin:0;font-size:.85rem;color:#6EE7B7'>
                        {st.session_state['booking_start']} → {st.session_state['booking_end']}
                        &nbsp;·&nbsp; <strong style='color:#34D399'>{int(total):,} MAD</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                with st.form(f"booking_form_{car['id']}"):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        fname = st.text_input("Nom complet *", value=full_name)
                        fphone = st.text_input("Téléphone *", placeholder="06XXXXXXXX")
                    with col_f2:
                        fcin  = st.text_input("CIN *", placeholder="AB123456")
                        femail = st.text_input("Email", placeholder="vous@exemple.com")
                    fnotes = st.text_area("Remarques", height=60)
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        confirm = st.form_submit_button("✅ Envoyer la demande", use_container_width=True)
                    with col_s2:
                        cancel_form = st.form_submit_button("✖ Annuler", use_container_width=True)

                if confirm:
                    if not fname or not fphone or not fcin:
                        st.error("Veuillez remplir les champs obligatoires (*)")
                    else:
                        rb = papi("post", "/portal/bookings", json={
                            "car_id": sel["id"],
                            "start_date": st.session_state["booking_start"],
                            "end_date":   st.session_state["booking_end"],
                            "full_name": fname, "phone": fphone, "cin": fcin,
                            "email": femail or None, "notes": fnotes or None
                        })
                        if rb and rb.status_code == 201:
                            d = rb.json()
                            st.success(f"✅ Demande #{d['id']} envoyée ! Total estimé : {int(d['total_price']):,} MAD — L'agence va confirmer sous peu.")
                            st.session_state.pop("show_booking_form", None)
                            st.session_state.pop("booking_car", None)
                            st.rerun()
                        elif rb:
                            st.error(rb.json().get("detail", "Erreur"))
                if cancel_form:
                    st.session_state.pop("show_booking_form", None)
                    st.rerun()

    # ════════════════════════════════════════════════
    elif page == "📋 Mes réservations":
        st.title("Mes réservations")

        r = papi("get", "/portal/my-bookings")
        if not r or r.status_code != 200:
            st.error("Impossible de charger vos réservations.")
            return

        bookings = r.json()
        if not bookings:
            st.info("Vous n'avez pas encore de réservation.")
            return

        for b in bookings:
            days = (date.fromisoformat(b["end_date"]) - date.fromisoformat(b["start_date"])).days
            status_map = {
                "pending":   ("⏳ En attente", "booking-status-pending"),
                "confirmed": ("✅ Confirmée",  "booking-status-confirmed"),
                "cancelled": ("❌ Annulée",    "booking-status-cancelled"),
                "completed": ("🏁 Terminée",   "booking-status-completed"),
            }
            label, cls = status_map.get(b["status"], (b["status"], "booking-status-pending"))

            with st.expander(f"#{b['id']} — {b['brand']} {b['model']} · {b['start_date']} → {b['end_date']} · {int(b['total_price']):,} MAD"):
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    st.markdown(f"**Véhicule :** {b['brand']} {b['model']} ({b['license_plate']})")
                    st.markdown(f"**Période :** {b['start_date']} → {b['end_date']} ({days}j)")
                    st.markdown(f"**Total :** {int(b['total_price']):,} MAD")
                with col_i2:
                    st.markdown(f"**Statut :** <span class='{cls}'>{label}</span>", unsafe_allow_html=True)
                    if b.get("notes"):
                        st.caption(f"📝 {b['notes']}")

                if b["status"] in ("pending", "confirmed"):
                    st.markdown('<div class="btn-cancel-user">', unsafe_allow_html=True)
                    if st.button("❌ Annuler cette réservation", key=f"ucancel_{b['id']}"):
                        rd = papi("delete", f"/portal/my-bookings/{b['id']}")
                        if rd and rd.status_code == 200:
                            st.success("Réservation annulée.")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# ROUTER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# PORTAIL SUPERADMIN
# ═══════════════════════════════════════════════════════════════════════════
def render_superadmin_portal():
    """Interface exclusive au superadmin — gestion de tous les comptes."""
    st.set_page_config(page_title="AutoLoc — SuperAdmin", page_icon="🛡️", layout="wide")

    token     = st.session_state.get("token")
    full_name = st.session_state.get("full_name", "SuperAdmin")

    def sapi(method, path, **kwargs):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            return getattr(requests, method)(f"{API}{path}", headers=headers, timeout=8, **kwargs)
        except Exception as e:
            st.error(str(e)); return None

    with st.sidebar:
        st.markdown("## 🛡️ SuperAdmin")
        st.markdown(f"**{full_name}**")
        st.markdown("---")
        st.markdown("<small style='color:#94A3B8'>Plateforme AutoLoc Pro</small>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 Déconnexion", use_container_width=True):
            logout()

    st.title("🛡️ Gestion des comptes")
    st.caption("Vue globale de tous les comptes inscrits sur la plateforme")

    r = sapi("get", "/auth/users")
    if not r or r.status_code != 200:
        st.error("Impossible de charger les comptes.")
        return

    users = r.json()
    current_id = st.session_state.get("user_id")

    admins  = [u for u in users if u["role"] == "admin"]
    clients = [u for u in users if u["role"] == "user"]

    # ── Métriques ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div style="background:#1E293B;border-radius:12px;padding:16px 20px;
            border-left:4px solid #3B82F6;box-shadow:0 2px 8px rgba(0,0,0,.2);margin-bottom:12px">
            <p style="margin:0;color:#93C5FD;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em">Total comptes</p>
            <p style="margin:6px 0 0;color:#F1F5F9;font-size:1.8rem;font-weight:800">{len(users)}</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style="background:#1E293B;border-radius:12px;padding:16px 20px;
            border-left:4px solid #D97706;box-shadow:0 2px 8px rgba(0,0,0,.2);margin-bottom:12px">
            <p style="margin:0;color:#FCD34D;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em">Sociétés (admin)</p>
            <p style="margin:6px 0 0;color:#FBBF24;font-size:1.8rem;font-weight:800">{len(admins)}</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style="background:#1E293B;border-radius:12px;padding:16px 20px;
            border-left:4px solid #16A34A;box-shadow:0 2px 8px rgba(0,0,0,.2);margin-bottom:12px">
            <p style="margin:0;color:#6EE7B7;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em">Clients (user)</p>
            <p style="margin:6px 0 0;color:#34D399;font-size:1.8rem;font-weight:800">{len(clients)}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Filtre ──
    role_filter = st.selectbox("Filtrer", ["Tous", "Sociétés (admin)", "Clients (user)"])
    filtered = users
    if role_filter == "Sociétés (admin)":   filtered = admins
    elif role_filter == "Clients (user)":   filtered = clients

    st.caption(f"{len(filtered)} compte(s)")

    import html as _h
    for u in filtered:
        is_me  = u["id"] == current_id
        is_sa  = u["role"] == "superadmin"
        role_colors = {
            "superadmin": ("#7C3AED", "#EDE9FE", "🛡️ SuperAdmin"),
            "admin":      ("#D97706", "#FEF3C7", "🏢 Admin"),
            "user":       ("#16A34A", "#DCFCE7", "👤 Client"),
        }
        rc, rb, rl = role_colors.get(u["role"], ("#6B7280", "#F3F4F6", u["role"]))
        me_badge = ' <span style="background:#3B82F6;color:white;font-size:.7rem;padding:2px 8px;border-radius:10px">Vous</span>' if is_me else ""

        card = (
            "<div style='background:#1E293B;border-radius:12px;padding:16px 20px;"
            "border-left:4px solid " + rc + ";margin-bottom:10px;"
            "box-shadow:0 2px 8px rgba(0,0,0,.2)'>"
              "<div style='display:flex;justify-content:space-between;align-items:center'>"
                "<div>"
                  "<p style='margin:0;font-size:1rem;font-weight:700;color:#F1F5F9'>"
                  + _h.escape(u["full_name"]) + me_badge + "</p>"
                  "<p style='margin:3px 0 0;font-size:.85rem;color:#94A3B8'>" + _h.escape(u["email"]) + "</p>"
                  + (f"<p style='margin:2px 0 0;font-size:.8rem;color:#64748B'>📞 {_h.escape(u['phone'])}</p>" if u.get("phone") else "")
                  + (f"<p style='margin:2px 0 0;font-size:.8rem;color:#64748B'>🆔 {_h.escape(u['cin'])}</p>" if u.get("cin") else "")
                  + f"<p style='margin:4px 0 0;font-size:.73rem;color:#475569'>Inscrit le {u['created_at'][:10]}</p>"
                "</div>"
                "<div style='text-align:right'>"
                  f"<span style='background:{rb};color:{rc};font-weight:700;font-size:.82rem;"
                  f"padding:4px 12px;border-radius:20px'>{rl}</span>"
                  f"<p style='margin:4px 0 0;font-size:.73rem;color:#64748B'>ID #{u['id']}</p>"
                "</div>"
              "</div>"
            "</div>"
        )
        st.markdown(card, unsafe_allow_html=True)

        if not is_me and not is_sa:
            col_r, col_d, _ = st.columns([2, 2, 4])
            new_role       = "user" if u["role"] == "admin" else "admin"
            new_role_label = "👤 Passer client" if u["role"] == "admin" else "🏢 Passer admin"
            with col_r:
                st.markdown('<div style="margin-bottom:12px">', unsafe_allow_html=True)
                if st.button(new_role_label, key=f"sa_role_{u['id']}", use_container_width=True):
                    rr = sapi("patch", f"/auth/users/{u['id']}/role", json={"role": new_role})
                    if rr and rr.status_code == 200:
                        st.success(f"Rôle → {new_role}")
                        st.rerun()
                    elif rr:
                        st.error(rr.json().get("detail", "Erreur"))
                st.markdown('</div>', unsafe_allow_html=True)
            with col_d:
                st.markdown('<div style="margin-bottom:12px">', unsafe_allow_html=True)
                if st.button("🗑️ Supprimer", key=f"sa_del_{u['id']}", use_container_width=True):
                    rd = sapi("delete", f"/auth/users/{u['id']}")
                    if rd and rd.status_code == 200:
                        st.success("Compte supprimé")
                        st.rerun()
                    elif rd:
                        st.error(rd.json().get("detail", "Erreur"))
                st.markdown('</div>', unsafe_allow_html=True)


if not is_logged_in():
    render_auth()
    st.stop()

if get_role() == "user":
    render_user_portal()
    st.stop()

if get_role() == "superadmin":
    render_superadmin_portal()
    st.stop()

# ── Sinon : interface admin (code existant ci-dessous) ──

st.set_page_config(
    page_title="AutoLoc Pro",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ──────────────────────────────────────────────────────────────────
# ── Styles ──────────────────────────────────────────────────────────────────
st.markdown(get_global_styles(), unsafe_allow_html=True)
st.markdown(get_car_card_styles(), unsafe_allow_html=True)
# ── Sidebar nav ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚗 AutoLoc Pro")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📊 Tableau de bord", "➕ Ajouter une voiture",
         "📋 Parc automobile", "📅 Nouvelle réservation", "🗂️ Réservations",
         "👤 Clients", "⚠️ Retards"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("<small>v2.0 · Gestion de flotte</small>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<small>👤 {st.session_state.get('full_name','Admin')}</small>", unsafe_allow_html=True)
    if st.button("🚪 Déconnexion", key="admin_logout", use_container_width=True):
        logout()

# ── Helper ───────────────────────────────────────────────────────────────────
def api(method, path, **kwargs):
    """API call with JWT token for multi-tenant isolation."""
    token = st.session_state.get("token")
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = getattr(requests, method)(f"{API}{path}", timeout=8, headers=headers, **kwargs)
        return r
    except Exception as e:
        st.error(f"Erreur de connexion à l'API : {e}")
        return None

def get_status_badge(status):
    label = STATUS_LABELS.get(status, status.capitalize())
    if status == "available":
        return f'<span class="badge-available">{label}</span>'
    elif status == "maintenance":
        return f'<span class="badge-maintenance">{label}</span>'
    else:
        return f'<span class="badge-retired">{label}</span>'

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 – Dashboard
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Tableau de bord":
    st.title("Tableau de bord")
    st.caption("Vue d'ensemble de votre parc et activité")

    r = api("get", "/stats")
    if r and r.status_code == 200:
        s = r.json()
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.markdown(f"""<div class="metric-card">
                <p class="metric-value">{s['total_cars']}</p>
                <p class="metric-label">🚗 Total véhicules</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card green">
                <p class="metric-value">{s['available_cars']}</p>
                <p class="metric-label">✅ Disponibles</p></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card red">
                <p class="metric-value">{s['maintenance_cars']}</p>
                <p class="metric-label">🔧 Maintenance</p></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card amber">
                <p class="metric-value">{s['active_bookings']}</p>
                <p class="metric-label">📅 Actives</p></div>""", unsafe_allow_html=True)
        with c5:
            st.markdown(f"""<div class="metric-card teal">
                <p class="metric-value">{s['completed_bookings']}</p>
                <p class="metric-label">✅ Terminées</p></div>""", unsafe_allow_html=True)
        with c6:
            st.markdown(f"""<div class="metric-card violet">
                <p class="metric-value">{s['total_revenue']:,.0f} MAD</p>
                <p class="metric-label">💰 CA Total</p></div>""", unsafe_allow_html=True)

        # Payment metrics row
        st.markdown("<br>", unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.markdown(f"""<div class="metric-card">
                <p class="metric-value">{s['total_collected']:,.0f} MAD</p>
                <p class="metric-label">💰 Total encaissé</p></div>""", unsafe_allow_html=True)
        with p2:
            outstanding_color = "#DC2626" if s['total_outstanding'] > 0 else "#16A34A"
            st.markdown(f"""<div class="metric-card">
                <p class="metric-value" style="color: {outstanding_color};">{s['total_outstanding']:,.0f} MAD</p>
                <p class="metric-label">💵 Total dû</p></div>""", unsafe_allow_html=True)
        with p3:
            st.markdown(f"""<div class="metric-card indigo">
                <p class="metric-value">{s.get('total_deposits_requested', 0):,.0f} MAD</p>
                <p class="metric-label">💳 Acomptes demandés</p></div>""", unsafe_allow_html=True)
        with p4:
            overdue_count = s.get('overdue_bookings', 0)
            overdue_color = "#DC2626" if overdue_count > 0 else "#6B7280"
            st.markdown(f"""<div class="metric-card">
                <p class="metric-value" style="color: {overdue_color};">{overdue_count}</p>
                <p class="metric-label">⚠️ En retard</p></div>""", unsafe_allow_html=True)

        # Overdue warning
        if s.get('overdue_bookings', 0) > 0:
            st.markdown(f"""
            <div class="overdue-alert">
                <p style="margin:0;font-weight:700;color:#DC2626">⚠️ {s['overdue_bookings']} réservation(s) en retard !</p>
                <p style="margin:4px 0 0;font-size:0.85rem;color:#7F1D1D">Consultez la page "Retards" pour les détails.</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Réservations récentes")
        rb = api("get", "/bookings", params={"status": "confirmed"})
        if rb and rb.status_code == 200:
            bookings = rb.json()[:5]
            if bookings:
                df = pd.DataFrame(bookings)[["client_name","brand","model","start_date","end_date","total_price","balance_due"]]
                df.columns = ["Client","Marque","Modèle","Début","Fin","Prix (MAD)","Solde"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune réservation active.")

    with col_b:
        st.subheader("Véhicules récemment ajoutés")
        rc = api("get", "/cars")
        if rc and rc.status_code == 200:
            cars = rc.json()[:5]
            if cars:
                df2 = pd.DataFrame(cars)[["brand","model","year","license_plate","daily_rate","status"]]
                df2.columns = ["Marque","Modèle","Année","Plaque","Tarif/j","Statut"]
                df2["Statut"] = df2["Statut"].map(STATUS_LABELS)
                st.dataframe(df2, use_container_width=True, hide_index=True)
            else:
                st.info("Aucun véhicule enregistré.")
            bookings = rb.json()[:5]
            if bookings:
                df = pd.DataFrame(bookings)[["client_name","brand","model","start_date","end_date","total_price","balance_due"]]
                df.columns = ["Client","Marque","Modèle","Début","Fin","Prix (MAD)","Solde"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Aucune réservation active.")
elif page == "➕ Ajouter une voiture":
    st.title("Ajouter une voiture")
    st.caption("Enregistrez un nouveau véhicule dans votre parc")

    st.subheader("Informations générales")
    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox("Marque *", MARQUES, key="brand_select")
    with col2:
        modeles_dispo = MODELES.get(brand, ["Autre"])
        model = st.selectbox("Modèle *", modeles_dispo, key="model_select")

    with st.form("add_car_form", clear_on_submit=True):
        col3, col4, col5 = st.columns(3)
        with col3:
            year = st.number_input("Année *", min_value=1990, max_value=date.today().year + 1, value=2024)
        with col4:
            mileage = st.number_input("Kilométrage (km) *", min_value=0, value=0, step=1000)
        with col5:
            license_plate = st.text_input("Plaque d'immatriculation *", placeholder="ex. 12345-A-1", help="Format: 12345-A-1")

        col6, col7, col8 = st.columns(3)
        with col6:
            category = st.selectbox("Catégorie *", ["Citadine","Berline","SUV","Utilitaire","Luxe","Monospace"])
        with col7:
            color = st.selectbox("Couleur *", COULEURS)
        with col8:
            status = st.selectbox("Statut *", ["available", "maintenance"], format_func=lambda x: STATUS_LABELS[x])

        st.subheader("Caractéristiques techniques")
        col8, col9, col10, col11 = st.columns(4)
        with col8:
            fuel_type = st.selectbox("Carburant *", ["Essence","Diesel","Hybride","Électrique","GPL"])
        with col9:
            transmission = st.selectbox("Transmission *", ["Manuelle","Automatique"])
        with col10:
            seats = st.number_input("Nombre de places *", min_value=2, max_value=50, value=5)
        with col11:
            daily_rate = st.number_input("Tarif journalier (MAD) *", min_value=1.0, value=300.0, step=50.0)

        st.subheader("Équipements")
        equipements = st.multiselect(
            "Équipements / Options",
            EQUIPEMENTS,
            help="Sélectionnez un ou plusieurs équipements"
        )
        notes_extra = st.text_input("Autres notes", placeholder="Remarques supplémentaires…")

        submitted = st.form_submit_button("➕ Ajouter le véhicule", use_container_width=True)

    if submitted:
        if not license_plate:
            st.error("Veuillez saisir la plaque d'immatriculation.")
        else:
            notes_combined = ", ".join(equipements)
            if notes_extra:
                notes_combined = (notes_combined + " — " + notes_extra) if notes_combined else notes_extra

            r = api("post", "/cars", json={
                "brand": brand, "model": model, "year": int(year),
                "mileage": int(mileage), "fuel_type": fuel_type,
                "transmission": transmission, "color": color,
                "seats": int(seats), "daily_rate": float(daily_rate),
                "license_plate": license_plate, "category": category,
                "status": status,
                "notes": notes_combined or None
            })
            if r and r.status_code == 201:
                st.success(f"✅ **{brand} {model}** ajouté avec succès !")
                st.balloons()
            elif r:
                detail = r.json().get("detail", "Erreur inconnue")
                if isinstance(detail, list):
                    detail = "; ".join([d.get("msg", str(d)) for d in detail])
                st.error(detail)
# PAGE 3 – Parc automobile (with Search, Sort, Export, Calendar)
# ════════════════════════════════════════════════════════════════════════════
elif page == "📋 Parc automobile":
    st.title("Parc automobile")

    # ── Search & Sort & Export bar ──
    col_search, col_sort, col_export = st.columns([3, 2, 1])
    with col_search:
        search_term = st.text_input("🔍 Rechercher", placeholder="Marque, modèle, plaque, couleur, notes...", key="car_search")
    with col_sort:
        sort_option = st.selectbox("Trier par", [
            ("", "Date d'ajout (récent)"),
            ("price_asc", "Prix ↑ croissant"),
            ("price_desc", "Prix ↓ décroissant"),
            ("year_desc", "Année ↓ récente"),
            ("year_asc", "Année ↑ ancienne"),
            ("mileage_asc", "Kilométrage ↑"),
            ("mileage_desc", "Kilométrage ↓"),
            ("brand_asc", "Marque A-Z"),
        ], format_func=lambda x: x[1])
    with col_export:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📤 Export CSV", use_container_width=True):
            r = api("get", "/export/cars")
            if r and r.status_code == 200:
                st.download_button(
                    label="⬇️ Télécharger",
                    data=r.content,
                    file_name="parc_automobile.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # Load cars with search and sort
    params = {}
    if search_term:
        params["search"] = search_term
    if sort_option[0]:
        params["sort_by"] = sort_option[0]

    rc = api("get", "/cars", params=params)
    cars_all = rc.json() if rc and rc.status_code == 200 else []

    marques_dispo = ["Toutes"] + sorted(set(c["brand"] for c in cars_all))
    modeles_tous  = sorted(set(c["model"] for c in cars_all))

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        brand_filter = st.selectbox("Marque", marques_dispo)
    with col_f2:
        if brand_filter != "Toutes":
            modeles_dispo2 = ["Tous"] + sorted(set(c["model"] for c in cars_all if c["brand"] == brand_filter))
        else:
            modeles_dispo2 = ["Tous"] + modeles_tous
        model_filter = st.selectbox("Modèle", modeles_dispo2)
    with col_f3:
        cat_filter = st.selectbox("Catégorie", ["Toutes","Citadine","Berline","SUV","Utilitaire","Luxe","Monospace"])
    with col_f4:
        status_filter = st.selectbox("Statut", ["Tous","Disponible","En maintenance","Retiré"])

    if rc and rc.status_code == 200:
        cars = cars_all
        if brand_filter != "Toutes":
            cars = [c for c in cars if c["brand"] == brand_filter]
        if model_filter != "Tous":
            cars = [c for c in cars if c["model"] == model_filter]
        if cat_filter != "Toutes":
            cars = [c for c in cars if c["category"] == cat_filter]
        if status_filter == "Disponible":
            cars = [c for c in cars if c["status"] == "available"]
        elif status_filter == "En maintenance":
            cars = [c for c in cars if c["status"] == "maintenance"]
        elif status_filter == "Retiré":
            cars = [c for c in cars if c["status"] == "retired"]

        st.caption(f"{len(cars)} véhicule(s) trouvé(s)")

        def build_car_card(car):
            status = car["status"]
            badge = get_status_badge(status)
            mileage_fmt = f"{car['mileage']:,}"
            rate_fmt = str(int(car["daily_rate"]))
            notes_p = ""
            if car.get("notes") and str(car["notes"]).strip():
                notes_p = (
                    "<p style='margin:8px 0 0;font-size:.82rem;"
                    "color:#94A3B8;font-style:italic'>📝 "
                    + _html.escape(str(car["notes"])) + "</p>"
                )
            parts = [
                "<div style='background:#1E293B;border-radius:12px;padding:18px 22px;"
                "margin-bottom:14px;border-left:4px solid #3B82F6;"
                "box-shadow:0 2px 8px rgba(0,0,0,0.25)'>",

                "<div style='display:flex;justify-content:space-between;align-items:flex-start'>",
                "<div>",
                "<p style='margin:0 0 6px;font-size:1.05rem;font-weight:700;color:#F1F5F9'>",
                "🚗 " + _html.escape(car["brand"]) + " " + _html.escape(car["model"]) + " (" + str(car["year"]) + ")",
                "</p>",
                "<span style='display:inline-block;background:#1D4ED8;color:#DBEAFE;"
                "font-size:.76rem;font-weight:700;padding:3px 10px;border-radius:5px;"
                "letter-spacing:.05em'>" + _html.escape(car["license_plate"]) + "</span>",
                "&nbsp;",
                badge,
                "</div>",
                "<p style='margin:0;font-size:1.2rem;font-weight:800;color:#34D399'>"
                + rate_fmt + " MAD/j</p>",
                "</div>",

                "<div style='margin-top:10px;color:#CBD5E1;font-size:.85rem;line-height:1.9'>",
                "⛽ " + _html.escape(car["fuel_type"]) + " &nbsp;·&nbsp; ",
                "⚙️ " + _html.escape(car["transmission"]) + " &nbsp;·&nbsp; ",
                "🎨 " + _html.escape(car["color"]) + " &nbsp;·&nbsp; ",
                "💺 " + str(car["seats"]) + " places &nbsp;·&nbsp; ",
                "📍 " + mileage_fmt + " km &nbsp;·&nbsp; ",
                "🏷️ " + _html.escape(car["category"]),
                "</div>",

                notes_p,
                "</div>",
            ]
            return "".join(parts)

        for car in cars:
            with st.container():
                st.markdown(build_car_card(car), unsafe_allow_html=True)

                col_actions = st.columns([3, 2, 2, 2, 2])
                with col_actions[1]:
                    if car["status"] == "available":
                        st.markdown('<div class="btn-maintenance">', unsafe_allow_html=True)
                        if st.button("🔧 Maintenance", key=f"maint_{car['id']}", help="Mettre en maintenance"):
                            r = api("patch", f"/cars/{car['id']}/status", json={"status": "maintenance"})
                            if r and r.status_code == 200:
                                st.success("Statut mis à jour")
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    elif car["status"] == "maintenance":
                        st.markdown('<div class="btn-disponible">', unsafe_allow_html=True)
                        if st.button("✅ Disponible", key=f"avail_{car['id']}", help="Remettre disponible"):
                            r = api("patch", f"/cars/{car['id']}/status", json={"status": "available"})
                            if r and r.status_code == 200:
                                st.success("Statut mis à jour")
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                with col_actions[2]:
                    st.markdown('<div class="btn-calendar">', unsafe_allow_html=True)
                    if st.button("📅 Calendrier", key=f"cal_{car['id']}", help="Voir disponibilité"):
                        st.session_state[f"show_calendar_{car['id']}"] = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with col_actions[3]:
                    st.markdown('<div class="btn-edit">', unsafe_allow_html=True)
                    if st.button("✏️ Modifier", key=f"edit_{car['id']}", help="Modifier le véhicule"):
                        st.session_state[f"edit_car_{car['id']}"] = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with col_actions[4]:
                    st.markdown('<div class="btn-delete">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{car['id']}", help="Supprimer"):
                        rd = api("delete", f"/cars/{car['id']}")
                        if rd and rd.status_code == 200:
                            st.success("Voiture supprimée")
                            st.rerun()
                        elif rd:
                            st.error(rd.json().get("detail", "Erreur de suppression"))
                    st.markdown('</div>', unsafe_allow_html=True)

                # Calendar view
                if st.session_state.get(f"show_calendar_{car['id']}", False):
                    with st.expander("📅 Disponibilité mensuelle", expanded=True):
                        cal_col1, cal_col2 = st.columns([1, 4])
                        with cal_col1:
                            st.markdown('<div class="btn-close">', unsafe_allow_html=True)
                            if st.button("❌ Fermer", key=f"close_cal_{car['id']}"):
                                st.session_state[f"show_calendar_{car['id']}"] = False
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        with cal_col2:
                            # Get bookings for this car
                            rb = api("get", "/bookings")
                            if rb and rb.status_code == 200:
                                car_bookings = [b for b in rb.json() if b["car_id"] == car["id"] and b["status"] in ("confirmed", "completed")]

                                # Show current month
                                today = date.today()
                                st.write(f"**{calendar.month_name[today.month]} {today.year}**")

                                # Build calendar grid
                                cal = calendar.Calendar()
                                month_days = cal.monthdayscalendar(today.year, today.month)

                                # Header
                                days_header = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
                                header_html = "<div style='display:flex;gap:4px;margin-bottom:4px'>"
                                for d in days_header:
                                    header_html += f"<div style='width:32px;text-align:center;font-weight:700;font-size:0.8rem;color:#64748B'>{d}</div>"
                                header_html += "</div>"
                                st.markdown(header_html, unsafe_allow_html=True)

                                for week in month_days:
                                    week_html = "<div style='display:flex;gap:4px;margin-bottom:4px'>"
                                    for day in week:
                                        if day == 0:
                                            week_html += "<div style='width:32px;height:32px'></div>"
                                        else:
                                            day_date = date(today.year, today.month, day)
                                            day_str = day_date.isoformat()

                                            # Check if booked
                                            is_booked = False
                                            for b in car_bookings:
                                                if b["start_date"] <= day_str <= b["end_date"]:
                                                    is_booked = True
                                                    break

                                            is_today = day_date == today
                                            css_class = "calendar-booked" if is_booked else "calendar-available"
                                            border = "border:2px solid #2563EB;" if is_today else ""

                                            week_html += f"<div class='{css_class}' style='{border}width:32px;height:32px;line-height:32px;text-align:center;border-radius:6px;margin:2px;font-size:0.85rem;font-weight:500'>{day}</div>"
                                    week_html += "</div>"
                                    st.markdown(week_html, unsafe_allow_html=True)

                                st.caption("🟢 Disponible  🔴 Réservé  🔵 Aujourd'hui")

                # Edit form
                if st.session_state.get(f"edit_car_{car['id']}", False):
                    with st.form(f"edit_form_{car['id']}"):
                        st.subheader(f"Modifier {car['brand']} {car['model']}")
                        e_col1, e_col2 = st.columns(2)
                        with e_col1:
                            edit_mileage = st.number_input("Kilométrage", min_value=0, value=car["mileage"], step=1000, key=f"em_{car['id']}")
                            edit_rate = st.number_input("Tarif journalier (MAD)", min_value=1.0, value=float(car["daily_rate"]), step=50.0, key=f"er_{car['id']}")
                        with e_col2:
                            edit_color = st.selectbox("Couleur", COULEURS, index=COULEURS.index(car["color"]) if car["color"] in COULEURS else 0, key=f"ec_{car['id']}")
                            edit_status = st.selectbox("Statut", STATUS_OPTIONS, index=STATUS_OPTIONS.index(car["status"]), format_func=lambda x: STATUS_LABELS[x], key=f"es_{car['id']}")
                        edit_notes = st.text_area("Notes", value=car.get("notes", ""), key=f"en_{car['id']}")

                        e_col_submit, e_col_cancel = st.columns(2)
                        with e_col_submit:
                            edit_submitted = st.form_submit_button("💾 Enregistrer", use_container_width=True)
                        with e_col_cancel:
                            if st.form_submit_button("❌ Annuler", use_container_width=True):
                                st.session_state[f"edit_car_{car['id']}"] = False
                                st.rerun()

                    if edit_submitted:
                        r = api("put", f"/cars/{car['id']}", json={
                            "mileage": int(edit_mileage),
                            "daily_rate": float(edit_rate),
                            "color": edit_color,
                            "status": edit_status,
                            "notes": edit_notes if edit_notes.strip() else None
                        })
                        if r and r.status_code == 200:
                            st.success("Véhicule mis à jour")
                            st.session_state[f"edit_car_{car['id']}"] = False
                            st.rerun()
                        elif r:
                            st.error(r.json().get("detail", "Erreur de mise à jour"))
    else:
        st.info("Aucun véhicule dans le parc.")

# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 – Nouvelle réservation (with Payment Tracking)
# ════════════════════════════════════════════════════════════════════════════
elif page == "📅 Nouvelle réservation":
    st.title("Nouvelle réservation")
    st.caption("Recherchez un véhicule disponible et confirmez la réservation")

    st.subheader("1. Choisissez les dates")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Date de prise en charge *", value=date.today() + timedelta(days=1), min_value=date.today())
    with col_d2:
        end_date = st.date_input("Date de restitution *", value=date.today() + timedelta(days=3), min_value=date.today() + timedelta(days=1))

    if start_date >= end_date:
        st.error("La date de restitution doit être après la date de prise en charge.")
        st.stop()

    days = (end_date - start_date).days
    st.info(f"📆 Durée : **{days} jour(s)**")

    # Initialize session state for this page
    if "search_done" not in st.session_state:
        st.session_state["search_done"] = False
    if "selected_car_id" not in st.session_state:
        st.session_state["selected_car_id"] = None

    def do_search():
        st.session_state["search_done"] = True
        st.session_state["start"] = str(start_date)
        st.session_state["end"] = str(end_date)
        st.session_state["days"] = days
        st.session_state["selected_car_id"] = None

    st.button("🔍 Rechercher les véhicules disponibles", use_container_width=True, on_click=do_search)

    if st.session_state.get("search_done"):
        ra = api("get", "/cars/search/available", params={"start_date": st.session_state["start"], "end_date": st.session_state["end"]})
        if ra and ra.status_code == 200:
            available = ra.json()
            if not available:
                st.warning("Aucun véhicule disponible pour ces dates.")
                st.stop()

            st.subheader(f"2. Sélectionnez un véhicule ({len(available)} disponibles)")

            cats = ["Toutes"] + sorted(set(c["category"] for c in available))
            cat_sel = st.selectbox("Filtrer par catégorie", cats)
            if cat_sel != "Toutes":
                available = [c for c in available if c["category"] == cat_sel]

            if not available:
                st.warning("Aucun véhicule dans cette catégorie pour ces dates.")
                st.stop()

            # ── Visual Car Cards Grid ──
            # Find best value (lowest price per day)
            best_value = min(available, key=lambda x: x["daily_rate"])

            # Use session state to track selection
            if "selected_car_id" not in st.session_state:
                st.session_state["selected_car_id"] = available[0]["id"]

            # Display cars in a grid of 3 columns
            cols_per_row = 3
            for i in range(0, len(available), cols_per_row):
                row_cols = st.columns(min(cols_per_row, len(available) - i))
                for j, car in enumerate(available[i:i + cols_per_row]):
                    with row_cols[j]:
                        is_selected = st.session_state.get("selected_car_id") == car["id"]
                        is_best_value = car["id"] == best_value["id"]
                        card_class = "car-select-card selected" if is_selected else "car-select-card"

                        title_html = f"<p class='car-select-title'>🚗 {car['brand']} {car['model']}</p>"
                        if is_best_value:
                            title_html = f"<p class='car-select-title'>🚗 {car['brand']} {car['model']}<span class='recommended-badge'>⭐ Meilleur prix</span></p>"

                        notes_html = ""
                        if car.get("notes") and str(car["notes"]).strip():
                            notes_html = f"<p class='car-select-notes'>📝 {_html.escape(str(car['notes'])[:80])}{'...' if len(str(car['notes'])) > 80 else ''}</p>"

                        st.markdown(f"""
                        <div class="{card_class}" id="car-card-{car['id']}">
                            <span class="car-select-category">{car['category']}</span>
                            {title_html}
                            <span class="car-select-plate">{car['license_plate']}</span>
                            <p class="car-select-price">{car['daily_rate']:.0f} <span class="car-select-price-unit">MAD/jour</span></p>
                            <div class="car-select-meta">
                                <span class="car-select-tag">📅 {car['year']}</span>
                                <span class="car-select-tag">⛽ {car['fuel_type']}</span>
                                <span class="car-select-tag">⚙️ {car['transmission']}</span>
                                <span class="car-select-tag">🎨 {car['color']}</span>
                                <span class="car-select-tag">💺 {car['seats']} places</span>
                                <span class="car-select-tag">📍 {car['mileage']:,} km</span>
                            </div>
                            {notes_html}
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button(
                            "✅ Sélectionner" if is_selected else "🔘 Choisir",
                            key=f"select_car_{car['id']}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"
                        ):
                            st.session_state["selected_car_id"] = car["id"]
                            st.rerun()

            # Get the selected car
            selected_car = next((c for c in available if c["id"] == st.session_state.get("selected_car_id")), available[0])

            total = selected_car["daily_rate"] * st.session_state["days"]
            notes_v = f'<p style="margin:6px 0 0;font-size:.83rem;color:#93C5FD;font-style:italic">📝 {selected_car["notes"]}</p>' if selected_car.get("notes") else ""

            st.markdown(f"""
            <div class="price-preview">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <p style="margin:0;font-size:1.15rem;font-weight:700;color:#F8FAFC">
                            🚗 {selected_car['brand']} {selected_car['model']} ({selected_car['year']})
                        </p>
                        <p style="margin:4px 0 0;font-size:.85rem;color:#93C5FD">
                            {selected_car['license_plate']} &nbsp;·&nbsp; {selected_car['category']}
                        </p>
                    </div>
                    <div style="text-align:right">
                        <p style="margin:0;font-size:1.5rem;font-weight:800;color:#34D399">{total:,.0f} MAD</p>
                        <p style="margin:2px 0 0;font-size:.8rem;color:#6EE7B7">{selected_car['daily_rate']:.0f} MAD/j × {st.session_state['days']} jours</p>
                    </div>
                </div>
                <div style="margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.1);
                            font-size:.85rem;color:#CBD5E1;display:flex;gap:18px;flex-wrap:wrap">
                    <span>⛽ {selected_car['fuel_type']}</span>
                    <span>⚙️ {selected_car['transmission']}</span>
                    <span>🎨 {selected_car['color']}</span>
                    <span>💺 {selected_car['seats']} places</span>
                    <span>📍 {selected_car['mileage']:,} km</span>
                </div>
                {notes_v}
            </div>
            """, unsafe_allow_html=True)

            st.subheader("3. Informations du client")
            with st.form("booking_form"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    client_name = st.text_input("Nom complet *", placeholder="ex. Ahmed Bennani")
                    client_cin = st.text_input("CIN *", placeholder="ex. AB123456", help="Format: AB123456")
                with col_c2:
                    client_phone = st.text_input("Téléphone *", placeholder="ex. 06XXXXXXXX")
                    client_email = st.text_input("Email", placeholder="ex. ahmed@example.com")

                # Payment section
                st.subheader("4. Paiement")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    deposit_amount = st.number_input("Acompte demandé (MAD)", min_value=0.0, max_value=float(total), value=0.0, step=100.0)
                with col_p2:
                    payment_method = st.selectbox("Méthode de paiement", ["cash", "card", "transfer", "deposit"], format_func=lambda x: PAYMENT_LABELS[x])

                notes = st.text_area("Remarques", height=70)

                balance = total - deposit_amount
                st.markdown(f"""
                <div style="background:#F0FDF4;border-radius:8px;padding:12px 16px;margin:12px 0;border-left:4px solid #16A34A">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <p style="margin:0;font-size:1.1rem;font-weight:700;color:#166534">
                                💰 Total: {total:,.0f} MAD
                            </p>
                            <p style="margin:4px 0 0;font-size:.85rem;color:#15803D">
                                Acompte: {deposit_amount:,.0f} MAD &nbsp;|&nbsp; Solde: {balance:,.0f} MAD
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                confirm = st.form_submit_button("✅ Confirmer la réservation", use_container_width=True)

            if confirm:
                if not all([client_name, client_phone, client_cin]):
                    st.error("Veuillez remplir les champs obligatoires (*)")
                else:
                    # Ensure dates are valid strings
                    start_str = str(st.session_state.get("start", ""))
                    end_str = str(st.session_state.get("end", ""))
                    if not start_str or not end_str:
                        st.error("Dates invalides. Veuillez refaire la recherche.")
                        st.stop()

                    rb = api("post", "/bookings", json={
                        "car_id": selected_car["id"],
                        "client_name": client_name.strip(),
                        "client_phone": client_phone.strip(),
                        "client_email": client_email.strip() if client_email else None,
                        "client_cin": client_cin.strip().upper(),
                        "start_date": start_str,
                        "end_date": end_str,
                        "deposit_amount": float(deposit_amount),
                        "payment_method": payment_method,
                        "notes": notes.strip() if notes else None,
                    })
                    if rb and rb.status_code == 201:
                        data = rb.json()
                        st.success(f"🎉 Réservation **#{data['id']}** confirmée ! Total : **{data['total_price']:,.0f} MAD** | Solde : **{data['balance_due']:,.0f} MAD**")

                        # PDF download
                        rp = api("get", f"/bookings/{data['id']}/contract")
                        if rp and rp.status_code == 200:
                            st.download_button(
                                label="📄 Télécharger le contrat PDF",
                                data=rp.content,
                                file_name=f"contrat_location_{data['id']}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )

                        st.session_state["search_done"] = False
                        st.session_state["selected_car_id"] = None
                        st.balloons()
                    elif rb:
                        detail = rb.json().get("detail", "Erreur")
                        if isinstance(detail, list):
                            detail = "; ".join([d.get("msg", str(d)) for d in detail])
                        st.error(detail)
        elif ra and ra.status_code == 400:
            st.error(ra.json().get("detail", "Erreur de dates"))

# ════════════════════════════════════════════════════════════════════════════
# PAGE 5 – Liste des réservations (with Payment & Export)
# ════════════════════════════════════════════════════════════════════════════
elif page == "🗂️ Réservations":
    st.title("Réservations")

    # Export buttons
    col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 4])
    with col_exp1:
        r_conf = api("get", "/export/bookings", params={"status": "confirmed"})
        if r_conf and r_conf.status_code == 200:
            st.download_button("📤 Export Confirmées", r_conf.content, "reservations_confirmed.csv", "text/csv", use_container_width=True)
    with col_exp2:
        r_all = api("get", "/export/bookings")
        if r_all and r_all.status_code == 200:
            st.download_button("📤 Export Toutes", r_all.content, "reservations_toutes.csv", "text/csv", use_container_width=True)

    tab1, tab2, tab3, tab4 = st.tabs(["⏳ En attente", "✅ Confirmées", "✅ Terminées", "❌ Annulées"])

    def render_bookings(status):
        rb = api("get", "/bookings", params={"status": status})
        if rb and rb.status_code == 200:
            bookings = rb.json()
            if not bookings:
                st.info("Aucune réservation.")
                return
            for b in bookings:
                jours = (date.fromisoformat(b["end_date"]) - date.fromisoformat(b["start_date"])).days
                is_overdue = date.fromisoformat(b["end_date"]) < date.today() and status == "confirmed"

                # Card styling with better contrast
                card_border = "#DC2626" if is_overdue else "#2563EB" if status == "confirmed" else "#16A34A" if status == "completed" else "#6B7280"
                card_bg = "#FEF2F2" if is_overdue else "#EFF6FF" if status == "confirmed" else "#F0FDF4" if status == "completed" else "#F3F4F6"

                expander_title = f"📋 #{b['id']} — {b['client_name']} · {b['brand']} {b['model']}"
                if is_overdue:
                    expander_title = f"🚨 #{b['id']} — {b['client_name']} · {b['brand']} {b['model']} (EN RETARD)"

                # Custom expander with dark visible text
                with st.expander(expander_title, expanded=False):
                    # Styled card container
                    import html as _h
                    _solde     = b.get('balance_due', 0)
                    _solde_col = '#DC2626' if _solde > 0 else '#16A34A'
                    _email_p   = (
                        '<p style="margin:4px 0;color:#374151;font-size:.9rem;">'
                        '<strong style="color:#111827;">📧 Email:</strong> '
                        + _h.escape(str(b['client_email'])) + '</p>'
                    ) if b.get('client_email') else ''
                    _card_html = (
                        '<div style="background:' + card_bg + ';border-left:4px solid ' + card_border + ';'
                        'border-radius:8px;padding:16px;margin:8px 0">'
                          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">'
                            '<span style="font-size:1.1rem;font-weight:700;color:#1F2937">🚗 '
                            + _h.escape(b['brand']) + ' ' + _h.escape(b['model']) + '</span>'
                            '<span style="background:' + card_border + ';color:white;padding:4px 12px;'
                            'border-radius:20px;font-size:.8rem;font-weight:600">'
                            + _h.escape(b['license_plate']) + '</span>'
                          '</div>'
                          '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">'
                            '<div>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">👤 Client:</strong> ' + _h.escape(b['client_name']) + '</p>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">🆔 CIN:</strong> ' + _h.escape(b['client_cin']) + '</p>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">📞 Téléphone:</strong> ' + _h.escape(b['client_phone']) + '</p>'
                              + _email_p +
                            '</div>'
                            '<div>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">📅 Période:</strong> '
                              + b['start_date'] + ' → ' + b['end_date'] + ' (' + str(jours) + 'j)</p>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">💰 Total:</strong> '
                              + f"{b['total_price']:,.0f}" + ' MAD</p>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">💳 Acompte:</strong> '
                              + f"{b.get('deposit_amount',0):,.0f}" + ' MAD</p>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">✅ Payé:</strong> '
                              + f"{b.get('deposit_paid',0):,.0f}" + ' MAD</p>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">💵 Solde:</strong> '
                              '<span style="color:' + _solde_col + ';font-weight:700">'
                              + f"{_solde:,.0f}" + ' MAD</span></p>'
                              '<p style="margin:4px 0;color:#374151;font-size:.9rem"><strong style="color:#111827">💳 Méthode:</strong> '
                              + _h.escape(PAYMENT_LABELS.get(b.get('payment_method','cash'),'Espèces')) + '</p>'
                            '</div>'
                          '</div>'
                        '</div>'
                    )
                    st.markdown(_card_html, unsafe_allow_html=True)

                    if b.get("notes"):
                        st.caption(f"📝 {b['notes']}")

                    # Payment update
                    if status == "confirmed" and b.get('balance_due', 0) > 0:
                        with st.form(f"payment_{b['id']}"):
                            st.markdown("**💳 Mettre à jour le paiement**")
                            pay_col1, pay_col2 = st.columns(2)
                            with pay_col1:
                                new_paid = st.number_input("Montant payé (MAD)", min_value=0.0, max_value=float(b['total_price']), value=float(b.get('deposit_paid', 0)), step=50.0, key=f"np_{b['id']}")
                            with pay_col2:
                                new_method = st.selectbox("Méthode", ["cash", "card", "transfer", "deposit"], index=["cash", "card", "transfer", "deposit"].index(b.get('payment_method', 'cash')), format_func=lambda x: PAYMENT_LABELS[x], key=f"nm_{b['id']}")
                            if st.form_submit_button("💾 Mettre à jour le paiement", use_container_width=True):
                                rp = api("patch", f"/bookings/{b['id']}/payment", json={"deposit_paid": float(new_paid), "payment_method": new_method})
                                if rp and rp.status_code == 200:
                                    st.success("Paiement mis à jour")
                                    st.rerun()
                                elif rp:
                                    st.error(rp.json().get("detail", "Erreur"))

                    # Contract download
                    if st.button("📄 Télécharger contrat", key=f"contract_{b['id']}"):
                        rp = api("get", f"/bookings/{b['id']}/contract")
                        if rp and rp.status_code == 200:
                            st.download_button(
                                label="⬇️ Télécharger PDF",
                                data=rp.content,
                                file_name=f"contrat_location_{b['id']}.pdf",
                                mime="application/pdf",
                                key=f"dl_contract_{b['id']}"
                            )

                    if status == "pending":
                        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                        st.markdown("<p style='font-size:.82rem;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.06em;margin:0 0 8px'>⚡ Décision</p>", unsafe_allow_html=True)
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            st.markdown('<div class="btn-green">', unsafe_allow_html=True)
                            if st.button("✅ Confirmer", key=f"confirm_{b['id']}", use_container_width=True):
                                rc = api("patch", f"/bookings/{b['id']}/confirm")
                                if rc and rc.status_code == 200:
                                    st.success("Réservation confirmée ✅")
                                    st.rerun()
                                elif rc:
                                    st.error(rc.json().get("detail", "Erreur"))
                            st.markdown('</div>', unsafe_allow_html=True)
                        with col_b2:
                            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
                            if st.button("❌ Refuser", key=f"reject_{b['id']}", use_container_width=True):
                                rc = api("patch", f"/bookings/{b['id']}/cancel")
                                if rc and rc.status_code == 200:
                                    st.success("Demande refusée")
                                    st.rerun()
                                elif rc:
                                    st.error(rc.json().get("detail", "Erreur"))
                            st.markdown('</div>', unsafe_allow_html=True)

                    if status == "confirmed":
                        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                        st.markdown("<p style='font-size:.82rem;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.06em;margin:0 0 8px'>⚡ Actions</p>", unsafe_allow_html=True)
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            st.markdown('<div class="btn-green">', unsafe_allow_html=True)
                            if st.button("✅ Marquer terminée", key=f"complete_{b['id']}", use_container_width=True):
                                rc = api("patch", f"/bookings/{b['id']}/complete")
                                if rc and rc.status_code == 200:
                                    st.success("Réservation terminée ✅")
                                    st.rerun()
                                elif rc:
                                    st.error(rc.json().get("detail", "Erreur"))
                            st.markdown('</div>', unsafe_allow_html=True)
                        with col_b2:
                            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
                            if st.button("❌ Annuler réservation", key=f"cancel_{b['id']}", use_container_width=True):
                                rc = api("patch", f"/bookings/{b['id']}/cancel")
                                if rc and rc.status_code == 200:
                                    st.success("Réservation annulée")
                                    st.rerun()
                                elif rc:
                                    st.error(rc.json().get("detail", "Erreur"))
                            st.markdown('</div>', unsafe_allow_html=True)

    with tab1:
        render_bookings("pending")
    with tab2:
        render_bookings("confirmed")
    with tab3:
        render_bookings("completed")
    with tab4:
        render_bookings("cancelled")

# ════════════════════════════════════════════════════════════════════════════
# PAGE 6 – Customer History
# ════════════════════════════════════════════════════════════════════════════
elif page == "👤 Clients":
    st.title("Historique des clients")
    st.caption("Recherchez un client par CIN ou téléphone pour voir son historique")

    search_cin   = st.text_input("🔍 Rechercher par CIN", placeholder="ex. AB123456")
    search_phone = st.text_input("🔍 Ou par téléphone",   placeholder="ex. 06XXXXXXXX")

    if st.button("🔎 Rechercher", use_container_width=True):
        if not search_cin and not search_phone:
            st.warning("Veuillez saisir un CIN ou un numéro de téléphone.")
        else:
            if search_cin:
                r = api("get", f"/customers/{search_cin.strip()}/history?by=cin")
            else:
                r = api("get", f"/customers/{search_phone.strip()}/history?by=phone")

            if r and r.status_code == 404:
                st.error("❌ Aucun client trouvé avec ces informations.")
            elif r and r.status_code == 200:
                data = r.json()
                restant = data.get("total_restant", 0)
                paye    = data.get("total_paye", 0)
                facture = data.get("total_facture", 0)

                st.markdown("---")

                # ── Carte client ──
                restant_color = "#F87171" if restant > 0 else "#34D399"
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1E3A5F 0%,#0F172A 100%);
                            border-radius:16px;padding:24px;margin:16px 0;color:white;">
                    <h2 style="margin:0 0 16px;color:#F8FAFC;font-size:1.5rem;">
                        👤 {data['client_name']}
                    </h2>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">
                        <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:16px;">
                            <p style="margin:0;color:#93C5FD;font-size:.82rem;text-transform:uppercase;">🆔 CIN</p>
                            <p style="margin:8px 0 0;color:white;font-size:1.15rem;font-weight:700;">{data['client_cin']}</p>
                        </div>
                        <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:16px;">
                            <p style="margin:0;color:#93C5FD;font-size:.82rem;text-transform:uppercase;">📞 Téléphone</p>
                            <p style="margin:8px 0 0;color:white;font-size:1.15rem;font-weight:700;">{data['client_phone'] or 'N/A'}</p>
                        </div>
                        <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:16px;">
                            <p style="margin:0;color:#93C5FD;font-size:.82rem;text-transform:uppercase;">📧 Email</p>
                            <p style="margin:8px 0 0;color:white;font-size:1.15rem;font-weight:700;">{data['client_email'] or 'N/A'}</p>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;margin-top:16px;">
                        <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:14px;text-align:center;">
                            <p style="margin:0;color:#93C5FD;font-size:.78rem;text-transform:uppercase;">📅 Réservations</p>
                            <p style="margin:6px 0 0;color:#FBBF24;font-size:1.6rem;font-weight:800;">{data['total_bookings']}</p>
                        </div>
                        <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:14px;text-align:center;">
                            <p style="margin:0;color:#93C5FD;font-size:.78rem;text-transform:uppercase;">💰 Total facturé</p>
                            <p style="margin:6px 0 0;color:#F8FAFC;font-size:1.4rem;font-weight:800;">{facture:,.0f} MAD</p>
                        </div>
                        <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:14px;text-align:center;">
                            <p style="margin:0;color:#93C5FD;font-size:.78rem;text-transform:uppercase;">✅ Total payé</p>
                            <p style="margin:6px 0 0;color:#34D399;font-size:1.4rem;font-weight:800;">{paye:,.0f} MAD</p>
                        </div>
                        <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:14px;text-align:center;">
                            <p style="margin:0;color:#93C5FD;font-size:.78rem;text-transform:uppercase;">⚠️ Reste à payer</p>
                            <p style="margin:6px 0 0;color:{restant_color};font-size:1.4rem;font-weight:800;">{restant:,.0f} MAD</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("---")
                st.subheader("📋 Historique des réservations")

                if data["bookings"]:
                    for b in data["bookings"]:
                        jours = (date.fromisoformat(b["end_date"]) - date.fromisoformat(b["start_date"])).days
                        s = b["status"]
                        status_bg     = {"confirmed":"#DCFCE7","completed":"#F0FDF4","cancelled":"#FEF2F2","pending":"#FEF9C3"}.get(s,"#F9FAFB")
                        status_border = {"confirmed":"#16A34A","completed":"#059669","cancelled":"#DC2626","pending":"#D97706"}.get(s,"#6B7280")
                        status_text   = {"confirmed":"✅ Confirmée","completed":"🏁 Terminée","cancelled":"❌ Annulée","pending":"⏳ En attente"}.get(s, s)
                        b_restant     = b.get("balance_due", 0)
                        solde_color   = "#DC2626" if b_restant > 0 else "#16A34A"
                        notes_html    = f'<p style="margin:4px 0;color:#374151;font-size:.9rem;"><strong>📝 Notes:</strong> {b["notes"]}</p>' if b.get("notes") else ""

                        with st.expander(f"#{b['id']} — {b['brand']} {b['model']} · {b['start_date']} → {b['end_date']}"):
                            st.markdown(f"""
                            <div style="background:{status_bg};border-left:4px solid {status_border};
                                        border-radius:8px;padding:16px;margin:8px 0;">
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                                    <span style="font-size:1.05rem;font-weight:700;color:#1F2937;">🚗 {b["brand"]} {b["model"]}</span>
                                    <span style="background:{status_border};color:white;padding:4px 12px;
                                                 border-radius:20px;font-size:.8rem;font-weight:600;">{status_text}</span>
                                </div>
                                <p style="margin:4px 0;color:#374151;font-size:.9rem;"><strong>🔖 Plaque:</strong> {b["license_plate"]}</p>
                                <p style="margin:4px 0;color:#374151;font-size:.9rem;"><strong>📅 Période:</strong> {b["start_date"]} → {b["end_date"]} ({jours}j)</p>
                                <p style="margin:4px 0;color:#374151;font-size:.9rem;"><strong>💰 Total facturé:</strong> {b["total_price"]:,.0f} MAD</p>
                                <p style="margin:4px 0;color:#374151;font-size:.9rem;"><strong>✅ Montant payé:</strong> <span style="color:#16A34A;font-weight:700;">{b.get("deposit_paid",0):,.0f} MAD</span></p>
                                <p style="margin:4px 0;color:#374151;font-size:.9rem;"><strong>⚠️ Reste à payer:</strong> <span style="color:{solde_color};font-weight:700;">{b_restant:,.0f} MAD</span></p>
                                {notes_html}
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Aucune réservation trouvée pour ce client.")
            elif r:
                st.error("Erreur lors de la recherche.")

# ════════════════════════════════════════════════════════════════════════════
# PAGE 7 – Overdue Bookings
# ════════════════════════════════════════════════════════════════════════════
elif page == "⚠️ Retards":
    st.title("Réservations en retard")
    st.caption("Véhicules non restitués à la date prévue")

    r = api("get", "/bookings/overdue")
    if r and r.status_code == 200:
        overdue = r.json()
        if not overdue:
            st.success("✅ Aucune réservation en retard !")
        else:
            st.error(f"⚠️ {len(overdue)} réservation(s) en retard")

            for b in overdue:
                days_overdue = int(b.get('days_overdue', 0))
                with st.expander(f"🚨 #{b['id']} — {b['client_name']} · {b['brand']} {b['model']} · {days_overdue} jour(s) de retard"):
                    col_o1, col_o2 = st.columns(2)
                    with col_o1:
                        st.markdown(f"**Client:** {b['client_name']}")
                        st.markdown(f"**CIN:** {b['client_cin']}")
                        st.markdown(f"**Téléphone:** {b['client_phone']}")
                        st.markdown(f"**Email:** {b.get('client_email', 'N/A')}")
                    with col_o2:
                        st.markdown(f"**Véhicule:** {b['brand']} {b['model']} ({b['license_plate']})")
                        st.markdown(f"**Date prévue de retour:** {b['end_date']}")
                        st.markdown(f"**Jours de retard:** {days_overdue}")
                        st.markdown(f"**Total:** {b['total_price']:,.0f} MAD")
                        st.markdown(f"**Solde:** {b.get('balance_due', 0):,.0f} MAD")

                    if b.get('notes'):
                        st.caption(f"📝 {b['notes']}")

                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        if st.button("📞 Contacter", key=f"contact_{b['id']}"):
                            st.info(f"Numéro: {b['client_phone']}")
                    with col_act2:
                        if st.button("✅ Marquer terminée", key=f"ov_complete_{b['id']}"):
                            rc = api("patch", f"/bookings/{b['id']}/complete")
                            if rc and rc.status_code == 200:
                                st.success("Réservation terminée")
                                st.rerun()
                            elif rc:
                                st.error(rp.json().get("detail", "Erreur"))
    else:
        st.error("Impossible de charger les retards.")
