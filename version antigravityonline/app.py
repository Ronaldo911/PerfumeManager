import os
import streamlit as st
import pandas as pd
from datetime import datetime
from models.base_model import BaseModel
from services.stock_service import StockService
from views.dashboard_view import DashboardView
from views.achats_view import AchatsView
from views.production_view import ProductionView
from views.ventes_view import VentesView
from views.credits_view import CreditsView
from views.offres_pertes_view import OffresPertesView
from views.catalogues_view import CataloguesView
from views.mouvements_view import MouvementsView
from views.settings_view import SettingsView
from utils.constants import FILES, DATA_DIR, IMG_DIR, BACKUP_DIR
from utils.helpers import new_id

# =========================================================
# CONFIGURATION SYSTEM & CUSTOM STYLES
# =========================================================
st.set_page_config(
    page_title="Parfum Manager PRO - Ultimate MVC", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Luxury Light Theme Styling
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Global Body and background styling */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background: radial-gradient(circle at 50% 50%, #ffffff 0%, #f7f4fc 100%) !important;
        color: #2b1f3d !important;
    }

    /* Titles styling */
    h1, h2, h3, h4, h5, h6 {
        color: #2b1f3d !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
    }
    
    .stApp h1 {
        background: linear-gradient(135deg, #2b1f3d 0%, #b89739 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 25px !important;
    }

    /* Luxury Sidebar Styling (Tailwind-like) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #59168b 0%, #6e11b0 100%) !important;
        border-right: none !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .sidebar-header {
        background: transparent !important;
        padding: 30px 15px !important;
        text-align: center;
        border-bottom: 1px solid #8200da;
    }
    [data-testid="stSidebar"] .sidebar-header h1 {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff !important;
        text-shadow: none;
        margin: 0;
        background: none;
        -webkit-text-fill-color: initial;
    }
    [data-testid="stSidebar"] .stRadio label {
        display: flex !important;
        align-items: center;
        padding: 12px 18px !important;
        cursor: pointer;
        font-size: 15px;
        font-weight: 500;
        border-left: none;
        margin: 5px 12px !important;
        border-radius: 8px;
        transition: all 0.3s ease;
        background-color: transparent !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #8200da !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stRadio label:has(input:checked) {
        background: #ffffff !important;
        color: #59168b !important;
        font-weight: 500;
        border-left: none !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
    }
    [data-testid="stSidebar"] .stRadio label:has(input:checked) * {
        color: #59168b !important;
    }
    [data-testid="stSidebar"] input[type="radio"] {
        display: none !important;
    }
    /* Hide the native Streamlit radio circles */
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    /* Hide the 'Navigation' group label just in case */
    [data-testid="stSidebar"] .stRadio > label {
        display: none !important;
    }
    .sidebar-separator {
        height: 1px;
        background: #8200da;
        margin: 15px 0;
    }
    .sidebar-footer {
        background-color: transparent;
        padding: 15px;
        text-align: center;
        font-size: 11px;
        color: rgba(255, 255, 255, 0.7) !important;
        border-top: 1px solid #8200da;
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
    }
    
    /* Content Cards with Glassmorphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(224, 192, 104, 0.28) !important;
        padding: 16px !important;
        border-radius: 12px !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.3s ease !important;
        height: 185px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
    }
    .metric-card:hover {
        transform: translateY(-4px) !important;
        border-color: rgba(224, 192, 104, 0.6) !important;
        box-shadow: 0 10px 24px rgba(224, 192, 104, 0.15) !important;
    }
    
    .catalog-item {
        backdrop-filter: blur(12px);
        border: 1px solid rgba(224, 192, 104, 0.25) !important;
        border-radius: 14px !important;
        padding: 20px !important;
        margin-bottom: 22px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.04) !important;
    }
    .catalog-item:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(224, 192, 104, 0.5) !important;
        box-shadow: 0 10px 24px rgba(224, 192, 104, 0.18) !important;
    }
    
    /* Boutique Header Banner */
    .shop-header {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(247, 244, 252, 0.9) 100%) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(224, 192, 104, 0.35) !important;
        padding: 25px 30px !important;
        border-radius: 14px !important;
        margin-bottom: 30px !important;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
    }
    .shop-header h1 {
        background: linear-gradient(135deg, #2b1f3d 0%, #b89739 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-size: 34px !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }

    /* Overriding Streamlit native Widgets */
    
    /* Input Elements (Text, Selectbox, Number, Textarea) */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[role="combobox"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(224, 192, 104, 0.3) !important;
        border-radius: 8px !important;
        color: #2b1f3d !important;
        padding: 10px 14px !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus, .stSelectbox div[role="combobox"]:focus {
        border-color: #7b1fa2 !important;
        box-shadow: 0 0 8px rgba(123, 31, 162, 0.2) !important;
        background-color: #ffffff !important;
    }

    /* Labels styling */
    label p {
        color: #2b1f3d !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        letter-spacing: 0.3px !important;
    }

    /* Tabs override to luxury pills */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: rgba(43, 31, 61, 0.6) !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
        font-size: 14.5px !important;
        border-bottom: 2px solid transparent !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #2b1f3d !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #7b1fa2 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #7b1fa2 !important;
    }

    /* Action buttons override */
    div.stButton > button {
        background: linear-gradient(135deg, #7b1fa2 0%, #e0c068 100%) !important;
        border: 1px solid rgba(224, 192, 104, 0.4) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: 0.8px !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 12px rgba(123, 31, 162, 0.15) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(224, 192, 104, 0.25) !important;
        border-color: #e0c068 !important;
    }
    div.stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* Alerts / Notifications styling */
    [data-testid="stNotification"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(224, 192, 104, 0.3) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    }
    [data-testid="stNotification"] * {
        color: #2b1f3d !important;
    }
    .stAlert {
        border-radius: 10px !important;
    }
    
    /* st.metric styling overrides */
    [data-testid="stMetricValue"] {
        color: #7b1fa2 !important;
        font-weight: 800 !important;
        font-size: 26px !important;
    }
    [data-testid="stMetricLabel"] p {
        color: #2b1f3d !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
</style>
""",unsafe_allow_html=True)

# =========================================================
# INITIALISATION
# =========================================================
def init_system():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Init settings & configs if they don't exist
    if not os.path.exists(FILES["shop_config"]):
        df_shop = pd.DataFrame({
            "Boutique_Nom": ["Ma Parfumerie"],
            "Logo_Path": [""],
            "Theme_Couleur": ["#6a1b9a"],
            "Date_Creation": [datetime.now().strftime("%Y-%m-%d")]
        })
        df_shop.to_csv(FILES["shop_config"], index=False)
        
    if not os.path.exists(FILES["categories"]):
        df_cat = pd.DataFrame({
            "ID": [new_id() for _ in range(6)],
            "Nom": ["Alcool", "Base Parfum", "Flacon", "Fixateur", "Seringue", "Emballage"],
            "Seuil_Alerte": [500, 200, 50, 100, 20, 30],
            "Couleur": ["#e0c068", "#7b1fa2", "#c2185b", "#00bcd4", "#009688", "#ff9800"],
            "Date_Ajout": [datetime.now().strftime("%Y-%m-%d")] * 6
        })
        df_cat.to_csv(FILES["categories"], index=False)
        
    if not os.path.exists(FILES["tailles"]):
        df_tailles = pd.DataFrame({
            "ID": [new_id() for _ in range(7)],
            "Taille": ["3 ML", "5 ML", "10 ML", "30 ML", "50 ML", "100 ML", "200 ML"],
            "Ordre": [1, 2, 3, 4, 5, 6, 7],
            "Actif": [True] * 7
        })
        df_tailles.to_csv(FILES["tailles"], index=False)
        
    if not os.path.exists(FILES["prix_vente"]):
        df_prix = pd.DataFrame({
            "ID": [new_id() for _ in range(7)],
            "Taille": ["3 ML", "5 ML", "10 ML", "30 ML", "50 ML", "100 ML", "200 ML"],
            "Prix_TND": [4.0, 6.0, 10.0, 25.0, 40.0, 75.0, 140.0]
        })
        df_prix.to_csv(FILES["prix_vente"], index=False)

    if not os.path.exists(FILES["clients"]):
        unique_clients = set()
        if os.path.exists(FILES["ventes"]):
            df_v = pd.read_csv(FILES["ventes"])
            if "Client" in df_v.columns:
                unique_clients.update(df_v["Client"].dropna().astype(str).tolist())
        if os.path.exists(FILES["credits_history"]):
            df_c = pd.read_csv(FILES["credits_history"])
            if "Client" in df_c.columns:
                unique_clients.update(df_c["Client"].dropna().astype(str).tolist())
        
        unique_clients = {c.strip() for c in unique_clients if c.strip() and c.strip().lower() != "anonyme"}
        
        clients_data = []
        for i, c_name in enumerate(sorted(list(unique_clients))):
            clients_data.append({
                "ID": new_id(),
                "Code": f"CLI-{(i+1):03d}",
                "Nom": c_name,
                "Telephone": "",
                "Date_Ajout": datetime.now().strftime("%Y-%m-%d")
            })
            
        df_clients = pd.DataFrame(clients_data, columns=["ID", "Code", "Nom", "Telephone", "Date_Ajout"])
        df_clients.to_csv(FILES["clients"], index=False)


    # Trigger loading tables into session_state
    for key in FILES.keys():
        BaseModel.load_df(key)
        
    # Verify categories color column exists
    df_cat = BaseModel.load_df("categories")
    if not df_cat.empty and "Couleur" not in df_cat.columns:
        default_colors = ["#e0c068", "#7b1fa2", "#c2185b", "#00bcd4", "#009688", "#ff9800"]
        if len(df_cat) > len(default_colors):
            default_colors += ["#7b1fa2"] * (len(df_cat) - len(default_colors))
        df_cat["Couleur"] = default_colors[:len(df_cat)]
        st.session_state["categories"] = df_cat
        BaseModel.save_df("categories")

    StockService.rebuild_inventory()

init_system()

# =========================================================
# HEADER BOUTIQUE
# =========================================================
def render_header():
    df_shop = BaseModel.load_df("shop_config")
    if not df_shop.empty:
        nom = df_shop.iloc[0]["Boutique_Nom"]
        logo_path = df_shop.iloc[0]["Logo_Path"]
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if logo_path and os.path.exists(str(logo_path)):
                st.image(str(logo_path), width=120)
            else:
                st.markdown("<div style='font-size:72px;text-align:center;'>🏪</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='shop-header'>
                <h1 style='margin:0;'>{nom}</h1>
                <p style='margin:5px 0 0 0;'>Parfum Manager Ultimate (Version Antigravity)</p>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
    st.markdown("""
    <div class='sidebar-header'>
        <h1>Parfum Manager</h1>
        <p style='margin:5px 0 0 0;font-size:12px;opacity:0.8;'>Ultimate Edition</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)
    
    if 'navigate_to' in st.session_state:
        st.session_state['main_nav_menu'] = st.session_state['navigate_to']
        del st.session_state['navigate_to']
        
    menu = st.radio(
        "Navigation",
        [
            "🏠 Tableau de Bord",
            "🛒 Gestion des Achats",
            "🏭 Fabrication Production",
            "💰 Terminal de Ventes",
            "🎁 Offres & Pertes",
            "💳 Suivi des Crédits",
            "📚 Catalogues Visuels",
            "🔄 Journal Mouvements",
            "⚙️ Paramètres Système"
        ],
        key="main_nav_menu",
        label_visibility="collapsed"
    )
    
    st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class='sidebar-footer'>
        Parfum Manager v3.5 | MVC<br>
        Antigravity Edition
    </div>
    """, unsafe_allow_html=True)

# Render boutique header on top
render_header()

# =========================================================
# PAGE ROUTER
# =========================================================
if menu == "🏠 Tableau de Bord":
    DashboardView.render()
elif menu == "🛒 Gestion des Achats":
    AchatsView.render()
elif menu == "🏭 Fabrication Production":
    ProductionView.render()
elif menu == "💰 Terminal de Ventes":
    VentesView.render()
elif menu == "🎁 Offres & Pertes":
    OffresPertesView.render()
elif menu == "💳 Suivi des Crédits":
    CreditsView.render()
elif menu == "📚 Catalogues Visuels":
    CataloguesView.render()
elif menu == "🔄 Journal Mouvements":
    MouvementsView.render()
elif menu == "⚙️ Paramètres Système":
    SettingsView.render()




























