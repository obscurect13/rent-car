"""Common CSS styles for all pages"""

def get_global_styles():
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main .block-container { background: #F1F5F9; }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 4px solid #2563EB;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .metric-card.green  { border-color: #16A34A; }
    .metric-card.amber  { border-color: #D97706; }
    .metric-card.violet { border-color: #7C3AED; }
    .metric-card.red    { border-color: #DC2626; }
    .metric-card.teal   { border-color: #0D9488; }
    .metric-card.orange { border-color: #EA580C; }

    .metric-value { font-size: 2rem; font-weight: 700; color: #0F172A; margin: 0; }
    .metric-label { font-size: 0.80rem; color: #475569; text-transform: uppercase;
                    letter-spacing: 0.06em; margin: 0; margin-top: 4px; }

    /* ── Sidebar foncée ── */
    section[data-testid="stSidebar"] { background: #0F172A !important; }
    /* Cibler UNIQUEMENT les éléments directs de la sidebar, pas via * global */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] small,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stRadio label {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label {
        color: #CBD5E1 !important; font-size: .95rem;
    }

    /* ── Tabs : texte toujours visible (noir foncé) ── */
    div[data-testid="stTabs"] button[data-baseweb="tab"] p,
    div[data-testid="stTabs"] button[data-baseweb="tab"] span,
    div[data-testid="stTabs"] [role="tab"] p,
    div[data-testid="stTabs"] [role="tab"] {
        color: #1E293B !important;
        font-weight: 600 !important;
    }
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] p,
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #2563EB !important;
        font-weight: 700 !important;
    }

    /* ── Expander : texte toujours visible ── */
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary {
        color: #0F172A !important;
        font-weight: 600 !important;
    }

    div[data-testid="stForm"] {
        background: white;
        border-radius: 12px;
        padding: 24px 28px;
        border: 1px solid #CBD5E1;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }

    label, .stSelectbox label, .stTextInput label,
    .stNumberInput label, .stTextArea label,
    .stMultiSelect label, .stDateInput label,
    div[data-testid="stWidgetLabel"] p,
    div[data-testid="stWidgetLabel"] label {
        color: #1E293B !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }

    input[type="text"], input[type="number"], input[type="email"],
    input, textarea {
        color: #0F172A !important;
        background-color: #ffffff !important;
        -webkit-text-fill-color: #0F172A !important;
    }

    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"] {
        background-color: #ffffff !important;
        color: #0F172A !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] input,
    div[data-baseweb="textarea"] textarea {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
    }

    div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-weight: 500 !important;
    }

    div[data-baseweb="select"] > div, div[data-baseweb="select"] span {
        color: #0F172A !important;
        background: white !important;
        border-color: #94A3B8 !important;
    }

    .stCaption, small { color: #475569 !important; }

    /* ── Boutons généraux (bleu) ── */
    .stButton > button {
        background: #2563EB !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
    }
    .stButton > button:hover { background: #1D4ED8 !important; }

    /* ── Boutons de formulaire (stFormSubmitButton) ── */
    /* Cible TOUS les boutons submit de formulaire avec couleur visible */
    .stFormSubmitButton > button {
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 0.55rem 1rem !important;
        width: 100% !important;
        font-size: 0.95rem !important;
    }
    /* Le fond est défini inline dans chaque form pour vert/rouge */
    /* Fallback bleu si pas de style inline */
    .stFormSubmitButton > button:not([style]) {
        background: #2563EB !important;
    }

    /* ── Expander header lisible ── */
    div[data-testid="stExpander"] {
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
        background: white !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #0F172A !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    /* Fond des forms à l'intérieur des expanders — sans bordure parasite */
    div[data-testid="stExpander"] div[data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 4px 0 !important;
    }

    h1 { font-weight: 700 !important; color: #0F172A !important; }
    h2 { font-weight: 600 !important; color: #1E293B !important; }
    h3 { font-weight: 600 !important; color: #1E293B !important; }

    div[data-testid="stAlert"] p { color: #1E293B !important; }
    .stDataFrame { background: white; border-radius: 8px; }

    .price-preview {
        background: linear-gradient(135deg, #1E3A5F 0%, #0F172A 100%);
        border-radius: 14px;
        padding: 20px 24px;
        margin: 12px 0 18px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 4px 14px rgba(0,0,0,0.18);
    }

    .overdue-alert {
        background: #FEF2F2;
        border-left: 4px solid #DC2626;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }

    .inspection-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #CBD5E1;
        margin-bottom: 12px;
    }

    .insurance-alert {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .insurance-expired {
        background: #FEF2F2;
        border-left: 4px solid #DC2626;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }

    /* ── Calendrier disponibilité ── */
    .calendar-available {
        background: #DCFCE7;
        color: #166534;
        font-weight: 600;
    }
    .calendar-booked {
        background: #FEE2E2;
        color: #991B1B;
        font-weight: 600;
    }

    /* ── Boutons d'action parc automobile ── */
    /* Maintenance → orange */
    .btn-maintenance .stButton > button {
        background: #D97706 !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .btn-maintenance .stButton > button:hover { background: #B45309 !important; }

    /* Disponible → vert */
    .btn-disponible .stButton > button {
        background: #16A34A !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .btn-disponible .stButton > button:hover { background: #15803D !important; }

    /* Calendrier → bleu ciel */
    .btn-calendar .stButton > button {
        background: #0284C7 !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .btn-calendar .stButton > button:hover { background: #0369A1 !important; }

    /* Modifier → violet */
    .btn-edit .stButton > button {
        background: #7C3AED !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .btn-edit .stButton > button:hover { background: #6D28D9 !important; }

    /* Supprimer → rouge */
    .btn-delete .stButton > button {
        background: #DC2626 !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .btn-delete .stButton > button:hover { background: #B91C1C !important; }

    /* Fermer → gris */
    .btn-close .stButton > button {
        background: #64748B !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .btn-close .stButton > button:hover { background: #475569 !important; }

    /* Boutons actions réservation */
    .btn-green .stButton > button {
        background: #16A34A !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .btn-green .stButton > button:hover { background: #15803D !important; }

    .btn-red .stButton > button {
        background: #DC2626 !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .btn-red .stButton > button:hover { background: #B91C1C !important; }
    </style>
    """


def get_car_card_styles():
    return """
    <style>
    .car-select-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 16px;
        padding: 20px;
        border: 2px solid #e2e8f0;
        transition: all 0.2s ease;
        cursor: pointer;
        height: 100%;
    }
    .car-select-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px);
    }
    .car-select-card.selected {
        border-color: #2563eb;
        background: linear-gradient(145deg, #eff6ff 0%, #dbeafe 100%);
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.2);
    }
    .car-select-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 8px 0;
    }
    .car-select-plate {
        display: inline-block;
        background: #1e40af;
        color: #dbeafe;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 6px;
        letter-spacing: 0.08em;
        margin-bottom: 12px;
    }
    .car-select-price {
        font-size: 1.6rem;
        font-weight: 800;
        color: #059669;
        margin: 8px 0 4px 0;
    }
    .car-select-price-unit {
        font-size: 0.85rem;
        color: #10b981;
        font-weight: 500;
    }
    .car-select-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
    }
    .car-select-tag {
        background: #f1f5f9;
        color: #475569;
        font-size: 0.78rem;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 500;
    }
    .car-select-category {
        display: inline-block;
        background: #fef3c7;
        color: #92400e;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 8px;
    }
    .car-select-notes {
        font-size: 0.8rem;
        color: #64748b;
        font-style: italic;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #e2e8f0;
    }
    .recommended-badge {
        display: inline-block;
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-left: 8px;
    }
    </style>
    """
