import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import os
from datetime import datetime, date
import io
from fpdf import FPDF

# ─── PDF GENERATION UTILS ─────────────────────────────────────────────────────
class DataCollectPDF(FPDF):
    def header(self):
        # Draw a subtle background border/frame
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.1)
        self.rect(5, 5, 200, 287)
        
        if os.path.exists("logo.svg"):
             # fpdf2 supports svg naturally if installed with dependencies
             try:
                 self.image("logo.svg", 10, 8, 25)
             except:
                 pass
        
        self.set_font('helvetica', 'B', 22)
        self.set_text_color(26, 26, 46) # Deep blue
        self.set_x(40)
        self.cell(0, 10, 'DATA-COLLECT PRO', ln=True, align='L')
        
        self.set_font('helvetica', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.set_x(40)
        self.cell(0, 5, 'L\'Intelligence de Données au service de la Performance', ln=True, align='L')
        
        self.ln(12)
        self.set_draw_color(233, 69, 96) # Accent color
        self.set_line_width(0.8)
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, 'Ce document est une production officielle de la plateforme DataCollect Pro.', ln=True, align='C')
        self.cell(0, 5, f'Page {self.page_no()}/{{nb}} - Généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}', align='C')

def generate_bulletin_pdf(df_etu_pdf, etu_info):
    pdf = DataCollectPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titre du document
    pdf.set_font('helvetica', 'B', 18)
    pdf.set_text_color(233, 69, 96)
    pdf.cell(0, 15, f"RELEVÉ DE NOTES OFFICIEL", ln=True, align='C')
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 8, f"SESSION : {etu_info['semestre'].upper()}", ln=True, align='C')
    pdf.ln(10)
    
    # Infos Etudiant dans un cadre
    pdf.set_fill_color(245, 245, 250)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, 65, 190, 40, 'F')
    
    pdf.set_xy(15, 70)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(40, 8, "NOM & PRÉNOM :", 0)
    pdf.set_font('helvetica', '', 11)
    pdf.cell(0, 8, f"{etu_info['prenom'].upper()} {etu_info['nom'].upper()}", ln=1)
    
    pdf.set_x(15)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(40, 8, "MATRICULE :", 0)
    pdf.set_font('helvetica', '', 11)
    pdf.cell(0, 8, f"{etu_info['matricule']}", ln=1)
    
    pdf.set_x(15)
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(40, 8, "FILIÈRE / NIVEAU :", 0)
    pdf.set_font('helvetica', '', 11)
    pdf.cell(0, 8, f"{etu_info['filiere']} - {etu_info['niveau']}", ln=1)
    
    pdf.ln(20)
    
    # Tableau des notes
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(233, 69, 96)
    pdf.set_text_color(255, 255, 255)
    
    # Header
    cols = [("Matière", 65), ("Crédits", 15), ("CC", 15), ("TP", 15), ("EXAM", 15), ("Moy/20", 20), ("Grade", 15), ("Décision", 30)]
    for txt, width in cols:
        pdf.cell(width, 10, txt, 1, 0, 'C', 1)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('helvetica', '', 9)
    
    fill = False
    for _, row in df_etu_pdf.iterrows():
        pdf.set_fill_color(250, 250, 250) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(65, 8, f" {str(row['matiere'])[:35]}", 1, 0, 'L', fill)
        pdf.cell(15, 8, str(row.get('credits', 6)), 1, 0, 'C', fill)
        pdf.cell(15, 8, f"{row['note_cc']:.2f}", 1, 0, 'C', fill)
        pdf.cell(15, 8, f"{row['note_tp']:.2f}", 1, 0, 'C', fill)
        pdf.cell(15, 8, f"{row['note_examen']:.2f}", 1, 0, 'C', fill)
        pdf.cell(20, 8, f"{row['note_finale']:.2f}", 1, 0, 'C', fill)
        pdf.cell(15, 8, str(row['mention']), 1, 0, 'C', fill)
        _, _, decision = get_lmd_info(row['note_finale'])
        pdf.cell(30, 8, decision, 1, 1, 'C', fill)
        fill = not fill
    
    # Résumé final
    pdf.ln(10)
    total_credits = df_etu_pdf['credits'].sum()
    moy_gen = np.average(df_etu_pdf['note_finale'], weights=df_etu_pdf['credits']) if total_credits > 0 else df_etu_pdf['note_finale'].mean()
    
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_fill_color(233, 69, 96)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(145, 10, "MOYENNE GÉNÉRALE DU SEMESTRE ", 1, 0, 'R', 1)
    pdf.cell(45, 10, f"{moy_gen:.2f} / 20", 1, 1, 'C', 1)
    
    # Blocs signatures
    pdf.ln(20)
    pdf.set_text_color(0, 0, 0)
    curr_y = pdf.get_y()
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_xy(10, curr_y)
    pdf.cell(90, 8, "L'Étudiant(e)", ln=0, align='C')
    pdf.cell(90, 8, "Le Chef de Département", ln=1, align='C')
    
    pdf.set_font('helvetica', 'I', 8)
    pdf.cell(90, 5, "(Signature précédée de la mention 'Lu et approuvé')", ln=0, align='C')
    pdf.cell(90, 5, "(Signature et Cachet)", ln=1, align='C')
    
    # Placeholder for Stamp
    pdf.set_draw_color(233, 69, 96)
    pdf.set_line_width(0.5)
    pdf.set_xy(135, curr_y + 15)
    pdf.cell(40, 20, "CACHET", 1, 0, 'C')

    return pdf.output()

def generate_facture_pdf(df_panier, vente_info):
    pdf = DataCollectPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titre Facture
    pdf.set_font('helvetica', 'B', 20)
    pdf.set_text_color(0, 208, 132) # Primary comm color
    pdf.cell(0, 15, "FACTURE COMMERCIALE", ln=True, align='C')
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"N° FACT : {datetime.now().strftime('%Y%m%d%H%M%S')}", ln=True, align='C')
    pdf.ln(10)
    
    # Cadre Infos Client/Vente
    pdf.set_fill_color(240, 250, 245)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, 65, 190, 30, 'F')
    
    pdf.set_xy(15, 68)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(30, 6, "DATE :", 0)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(65, 6, f"{vente_info['date_vente']}", 0)
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(30, 6, "VENDEUR :", 0)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 6, f"{vente_info['vendeur'].upper()}", ln=1)
    
    pdf.set_x(15)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(30, 6, "RÉGION :", 0)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(65, 6, f"{vente_info['region']}", 0)
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(30, 6, "PAIEMENT :", 0)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 6, f"{vente_info['mode_paiement']}", ln=1)
    
    pdf.ln(12)
    
    # Tableau des articles
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_fill_color(0, 208, 132)
    pdf.set_text_color(255, 255, 255)
    
    pdf.cell(90, 10, "   Désignation Produit", 1, 0, 'L', 1)
    pdf.cell(25, 10, "Qté", 1, 0, 'C', 1)
    pdf.cell(35, 10, "Prix Unit.", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Total (FCFA)", 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('helvetica', '', 10)
    
    total_facture = 0
    fill = False
    for _, row in df_panier.iterrows():
        p = row.get("Produit")
        if pd.isna(p) or str(p).strip() == "": continue
        
        q = int(row.get("Quantité", 1))
        pu = float(row.get("Prix unitaire (FCFA)", 0.0))
        stotal = q * pu
        total_facture += stotal
        
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(90, 8, f"  {str(p)[:45]}", 1, 0, 'L', fill)
        pdf.cell(25, 8, str(q), 1, 0, 'C', fill)
        pdf.cell(35, 8, f"{pu:,.0f}", 1, 0, 'C', fill)
        pdf.cell(40, 8, f"{stotal:,.0f}", 1, 1, 'C', fill)
        fill = not fill
    
    # Total Final
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_fill_color(0, 208, 132)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(115, 12, "MONTANT TOTAL À PAYER (FCFA) ", 1, 0, 'R', 1)
    pdf.cell(75, 12, f"{total_facture:,.0f} FCFA", 1, 1, 'C', 1)
    
    # Mentions légales & Signatures
    pdf.ln(20)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('helvetica', 'B', 10)
    curr_y = pdf.get_y()
    
    pdf.set_xy(10, curr_y)
    pdf.cell(90, 8, "Signature Client", ln=0, align='C')
    pdf.cell(90, 8, "Cachet de l'Entreprise", ln=1, align='C')
    
    pdf.ln(10)
    pdf.set_font('helvetica', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Les marchandises vendues ne sont ni reprises ni échangées après livraison.", ln=True, align='C')
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(0, 208, 132)
    pdf.cell(0, 10, "MERCI DE VOTRE CONFIANCE !", ln=True, align='C')
    
    return pdf.output()

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataCollect Pro",
    page_icon="logo.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Root variables */
:root {
    --edu-primary: #1a1a2e;
    --edu-accent: #e94560;
    --edu-light: #16213e;
    --com-primary: #0d3b2e;
    --com-accent: #00d084;
    --com-light: #1a5c45;
    --neutral: #f0f2f5;
    --card-bg: rgba(255,255,255,0.05);
}

/* Global */
html, body {
    font-family: 'DM Sans', sans-serif;
}

.main { background: #0a0a0f; color: #e8e8f0; }
.stApp { background: #0a0a0f; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d1a 0%, #0a1628 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #c8c8d8 !important;
}

/* Headers */
h1, h2, h3 { font-family: 'Syne', sans-serif; }

/* Cards */
.metric-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 24px;
    margin: 8px 0;
    backdrop-filter: blur(10px);
}

.edu-card { border-left: 4px solid #e94560; }
.com-card { border-left: 4px solid #00d084; }

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #e94560, #a855f7, #00d084);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin-bottom: 8px;
}

.hero-sub {
    color: #8888a8;
    font-size: 1.1rem;
    font-weight: 300;
    margin-bottom: 32px;
}

.section-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 12px;
}

.edu-badge { background: rgba(233,69,96,0.15); color: #e94560; border: 1px solid rgba(233,69,96,0.3); }
.com-badge { background: rgba(0,208,132,0.15); color: #00d084; border: 1px solid rgba(0,208,132,0.3); }

.stat-number {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1;
}

.stat-label {
    font-size: 0.8rem;
    color: #8888a8;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

.success-msg {
    background: linear-gradient(135deg, rgba(0,208,132,0.15), rgba(0,208,132,0.05));
    border: 1px solid rgba(0,208,132,0.3);
    border-radius: 12px;
    padding: 16px 20px;
    color: #00d084;
    font-weight: 500;
    margin: 12px 0;
}

.info-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
}

/* Redefine specific info-box for consistency */
.info-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #e94560, #a855f7) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.5px !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(233,69,96,0.35) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #8888a8;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: rgba(233,69,96,0.2) !important;
    color: #e94560 !important;
}

/* Dataframe - Removed overflow:hidden to fix stable input positioning */
.stDataFrame { border-radius: 12px; }

/* Divider */
hr { border-color: rgba(255,255,255,0.08); }

/* Labels */
label { color: #c8c8d8 !important; }

/* Metric */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px !important;
}

[data-testid="stMetricValue"] { color: #e8e8f0 !important; font-family: 'Syne', sans-serif !important; }
[data-testid="stMetricLabel"] { color: #8888a8 !important; }
[data-testid="stMetricDelta"] svg { fill: currentColor !important; }
</style>
""", unsafe_allow_html=True)

# ─── DATABASE ──────────────────────────────────────────────────────────────────
DB_PATH = "datacollect.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS etudiants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, prenom TEXT, matricule TEXT,
            filiere TEXT, niveau TEXT, semestre TEXT,
            matiere TEXT, note_cc REAL, note_examen REAL,
            note_finale REAL, mention TEXT, absences INTEGER,
            date_saisie TEXT
        )
    """)
    try:
        c.execute("ALTER TABLE etudiants ADD COLUMN note_tp REAL DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE etudiants ADD COLUMN credits REAL DEFAULT 6")
    except:
        pass
    c.execute("""
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit TEXT, categorie TEXT, quantite INTEGER,
            prix_unitaire REAL, montant_total REAL,
            region TEXT, vendeur TEXT, date_vente TEXT,
            mode_paiement TEXT, date_saisie TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS achats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit TEXT, categorie TEXT, quantite INTEGER,
            prix_achat REAL, fournisseur TEXT, date_achat TEXT,
            date_saisie TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ajustements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit TEXT, quantite_ajustee INTEGER,
            motif TEXT, date_ajustement TEXT, date_saisie TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            horodatage TEXT,
            module TEXT,
            action TEXT,
            details TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_conn(): return sqlite3.connect(DB_PATH)

def get_etudiants():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM etudiants ORDER BY date_saisie DESC", conn)
    conn.close()
    return df

def get_ventes():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM ventes ORDER BY date_saisie DESC", conn)
    conn.close()
    return df

def get_achats():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM achats ORDER BY date_saisie DESC", conn)
    conn.close()
    return df

def get_ajustements():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM ajustements ORDER BY date_saisie DESC", conn)
    conn.close()
    return df

def get_audit_logs():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM audit_logs ORDER BY id DESC", conn)
    conn.close()
    return df

def log_action(module: str, action: str, details: str):
    """Enregistre une action sensible dans le journal d'audit."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO audit_logs (horodatage, module, action, details) VALUES (?,?,?,?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), module, action, details)
    )
    conn.commit()
    conn.close()

def get_lmd_info(note_20):
    n = note_20 * 5
    if n >= 80: return "A", 4.00, "Validé"
    elif n >= 75: return "A-", 3.70, "Validé"
    elif n >= 70: return "B+", 3.30, "Validé"
    elif n >= 65: return "B", 3.00, "Validé"
    elif n >= 60: return "B-", 2.70, "Validé"
    elif n >= 55: return "C+", 2.30, "Validé"
    elif n >= 50: return "C", 2.00, "Validé"
    elif n >= 45: return "C-", 1.70, "Capitalisé"
    elif n >= 40: return "D+", 1.30, "Capitalisé"
    elif n >= 35: return "D", 1.00, "Rattrapage"
    else: return "E/F", 0.00, "Rattrapage"

def mention(note):
    grade, _, _ = get_lmd_info(note)
    return grade

# ─── INIT ──────────────────────────────────────────────────────────────────────
init_db()

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px'>
        <div style='font-family:Syne; font-size:1.6rem; font-weight:800; 
                    background:linear-gradient(135deg,#e94560,#00d084 );
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    background-clip:text;'>
            DataCollect Pro
        </div>
        <div style='color:#555570; font-size:0.75rem; letter-spacing:2px; 
                    text-transform:uppercase; margin-top:4px;'>
            ROI-V ABDEL
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    module = st.radio(
        "📌 Module",
        ["🏠 Accueil", "📚 Éducation", "🛒 Commerce"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    if module == "📚 Éducation":
        page_edu = st.selectbox(
            "Navigation",
            ["➕ Saisir des données", "📤 Importer CSV/Excel", "📊 Analyse descriptive", "🎓 Bulletin de notes", "🗃️ Voir toutes les données", "🤖 Prédiction (IA)", "⚙️ Administration"]
        )
    elif module == "🛒 Commerce":
        page_com = st.selectbox(
            "Navigation",
            ["➕ Saisir des données", "📥 Entrées Stock (Achats)", "📤 Importer CSV/Excel", "📊 Analyse descriptive", "🗃️ Voir toutes les données", "🤖 Prédiction (IA)", "⚙️ Administration"]
        )

    st.markdown("""
    <div style='position:fixed; bottom:20px; left:0; right:0; text-align:center;
                color:#44445a; font-size:0.72rem; padding:0 20px; z-index:99;'>
        © 2026 ROI-V ABDEL Tous droits réservés<br>
        <span style='color:#e94560'>♥</span> Concus par NGOUNDAM_V ABDEL_FADIL 
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ACCUEIL
# ═══════════════════════════════════════════════════════════════════════════════
if module == "🏠 Accueil":
    col_logo, col_titre = st.columns([1, 4])
    with col_logo:
        st.image("logo.svg", width=100)
    with col_titre:
        st.markdown('<div class="hero-title">DataCollect Pro</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Plateforme intelligente de collecte & d\'analyse descriptive des données</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    df_edu = get_etudiants()
    df_com = get_ventes()

    with col1:
        # On compte les matricules uniques, pas les lignes de matières
        nb_etudiants = df_edu['matricule'].nunique() if not df_edu.empty else 0
        st.metric("👨‍🎓 Étudiants inscrits", nb_etudiants)
    with col2:
        # On compte les sessions de vente (bons de caisse déposés au même moment)
        nb_ventes = df_com['date_saisie'].nunique() if not df_com.empty else 0
        st.metric("🧾 Factures générées", nb_ventes)
    with col3:
        moy = round(df_edu['note_finale'].mean(), 2) if len(df_edu) > 0 else 0
        st.metric("📈 Moyenne générale", f"{moy}/20")
    with col4:
        ca = f"{df_com['montant_total'].sum():,.0f} FCFA" if len(df_com) > 0 else "0 FCFA"
        st.metric("💰 Chiffre d'affaires", ca)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<span class="section-badge edu-badge">📚 Module Éducation</span>', unsafe_allow_html=True)
        st.markdown("""
        <div class="metric-card edu-card">
            <div style='font-family:Syne; font-size:1.1rem; font-weight:700; color:#e8e8f0; margin-bottom:12px;'>
                Gestion des résultats académiques
            </div>
            <div style='color:#8888a8; font-size:0.9rem; line-height:1.7;'>
                ✦ Saisie des notes par matière<br>
                ✦ Calcul automatique des moyennes<br>
                ✦ Attribution des mentions<br>
                ✦ Suivi des absences<br>
                ✦ Statistiques par filière/niveau<br>
                ✦ Graphiques & tableaux de bord
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown('<span class="section-badge com-badge">🛒 Module Commerce</span>', unsafe_allow_html=True)
        st.markdown("""
        <div class="metric-card com-card">
            <div style='font-family:Syne; font-size:1.1rem; font-weight:700; color:#e8e8f0; margin-bottom:12px;'>
                Suivi des performances commerciales
            </div>
            <div style='color:#8888a8; font-size:0.9rem; line-height:1.7;'>
                ✦ Enregistrement des ventes<br>
                ✦ Calcul du chiffre d'affaires<br>
                ✦ Analyse par produit & catégorie<br>
                ✦ Performance par région & vendeur<br>
                ✦ Évolution temporelle des ventes<br>
                ✦ Graphiques & tableaux de bord
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🕒 Derniers Enregistrements")
    
    col_e, col_v = st.columns(2)
    
    with col_e:
        st.markdown("**📜 Récemment inscrits (Étudiants)**")
        if not df_edu.empty:
            # On prend le dernier enregistrement par matricule (pour lister les personnes)
            recent_edu = df_edu.sort_values('date_saisie', ascending=False).drop_duplicates('matricule').head(5)
            st.dataframe(recent_edu[['matricule', 'nom', 'filiere', 'niveau']], use_container_width=True, hide_index=True)
        else:
            st.info("Aucun étudiant enregistré.")

    with col_v:
        st.markdown("**💸 Dernières Ventes (Bons de caisse)**")
        if not df_com.empty:
            # On groupe par session de saisie pour montrer les transactions
            recent_v = df_com.groupby('date_saisie').agg({
                'vendeur': 'first',
                'montant_total': 'sum'
            }).reset_index().sort_values('date_saisie', ascending=False).head(5)
            
            recent_v.columns = ['Date/Heure Saisie', 'Agent Vendeur', 'Montant Total (FCFA)']
            st.dataframe(recent_v, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune vente enregistrée.")

    st.markdown("---")
    st.markdown("""
    <div class="info-box" style='text-align:center;'>
        <div style='font-family:Syne; font-size:1rem; font-weight:700; color:#8888a8; margin-bottom:6px;'>
            🚀 Comment démarrer ?
        </div>
        <div style='color:#8888a8; font-size:0.88rem;'>
            Sélectionnez un module dans le menu de gauche → Saisissez ou importez vos données → Consultez les analyses
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ÉDUCATION
# ═══════════════════════════════════════════════════════════════════════════════
elif module == "📚 Éducation":
    st.markdown('<span class="section-badge edu-badge">📚 Module Éducation</span>', unsafe_allow_html=True)

    # ── SAISIR ────────────────────────────────────────────────────────────────
    if page_edu == "➕ Saisir des données":
        st.markdown("### Saisie des résultats académiques")

        with st.form("form_etudiant", clear_on_submit=True):
            st.markdown("#### 1. Informations de l'Étudiant")
            col1, col2, col3 = st.columns(3)
            with col1:
                nom = st.text_input("Nom ", key="nom")
                filiere = st.selectbox("Filière ", ["Informatique", "Mathématiques", "Physique", "Chimie", "Biologie", "Économie", "Droit", "Médecine", "Autre"])
            with col2:
                prenom = st.text_input("Prénom ", key="prenom")
                niveau = st.selectbox("Niveau ", ["Licence 1", "Licence 2", "Licence 3", "Master 1", "Master 2", "Doctorat"])
            with col3:
                matricule = st.text_input("Matricule", key="matricule")

            st.markdown("---")
            st.markdown("#### 2. Notes du Semestre (Saisie Multiple)")
            st.markdown("Remplissez la grille ci-dessous. Vous pouvez ajouter autant de matières que nécessaire.")
            
            # Grille par défaut
            default_grid = pd.DataFrame(
                [
                    {"Matière": "INF232", "Semestre": "S1", "Crédits": 6.0, "Note CC (/20)": 0.0, "Note TP (/30)": 0.0, "Note EE (/50)": 0.0},
                    {"Matière": "INF212", "Semestre": "S1", "Crédits": 6.0, "Note CC (/20)": 0.0, "Note TP (/30)": 0.0, "Note EE (/50)": 0.0},
                    {"Matière": "MAT232", "Semestre": "S2", "Crédits": 6.0, "Note CC (/20)": 0.0, "Note TP (/30)": None, "Note EE (/50)": 0.0},
                ]
            )
            
            edited_df = st.data_editor(
                default_grid, 
                num_rows="dynamic", 
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Matière": st.column_config.TextColumn("Unité d'enseignement", required=True),
                    "Semestre": st.column_config.SelectboxColumn("Semestre", options=["S1", "S2"], required=True),
                    "Crédits": st.column_config.NumberColumn("Crédits", min_value=1.0, max_value=30.0, step=1.0, required=True),
                    "Note CC (/20)": st.column_config.NumberColumn("Note CC (/20)", min_value=0.0, max_value=20.0, step=0.25),
                    "Note TP (/30)": st.column_config.NumberColumn("Note TP (/30)", min_value=0.0, max_value=30.0, step=0.25),
                    "Note EE (/50)": st.column_config.NumberColumn("Note EE (/50)", min_value=0.0, max_value=50.0, step=0.25)
                }
            )

            submitted = st.form_submit_button("💾 Enregistrer le Semestre", use_container_width=True)

            if submitted:
                if nom and prenom and matricule:
                    conn = get_conn()
                    count = 0
                    stats_sem = {}
                    
                    for index, row in edited_df.iterrows():
                        matiere = row.get("Matière")
                        if pd.isna(matiere) or str(matiere).strip() == "":
                            continue
                        
                        semestre = row.get("Semestre", "S1")   
                        val_creds = row.get("Crédits")
                        creds = float(val_creds) if pd.notna(val_creds) else 6.0
                        
                        val_ncc = row.get("Note CC (/20)")
                        val_ntp = row.get("Note TP (/30)")
                        val_nex = row.get("Note EE (/50)")
                        
                        ncc = float(val_ncc) if pd.notna(val_ncc) else 0.0
                        nex = float(val_nex) if pd.notna(val_nex) else 0.0
                        
                        if pd.isna(val_ntp):
                            ntp = 0.0
                            note_finale = round((ncc + nex) / 3.5, 2)
                        else:
                            ntp = float(val_ntp)
                            note_finale = round((ncc + ntp + nex) / 5, 2)
                            
                        ment = mention(note_finale)
                        _, points, _ = get_lmd_info(note_finale)
                        
                        conn.execute("""
                            INSERT INTO etudiants (nom, prenom, matricule, filiere, niveau, semestre,
                            matiere, note_cc, note_tp, note_examen, note_finale, mention, absences, date_saisie, credits)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (nom, prenom, matricule, filiere, niveau, semestre, matiere,
                              ncc, ntp, nex, note_finale, ment, 0,
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), creds))
                              
                        if semestre not in stats_sem:
                            stats_sem[semestre] = {'credits': 0, 'points': 0}
                        stats_sem[semestre]['credits'] += creds
                        stats_sem[semestre]['points'] += points * creds
                        count += 1
                        
                    conn.commit()
                    conn.close()
                    
                    if count > 0:
                        st.markdown(f"""
                        <div class="success-msg">
                            ✅ <strong>Bilan Académique enregistré avec succès pour {prenom} {nom} !</strong><br>
                            📊 {count} Unités d'enseignement ont été traitées et sauvegardées.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        cols = st.columns(len(stats_sem) + 1)
                        tot_c = 0
                        tot_p = 0
                        for i, sem in enumerate(sorted(stats_sem.keys())):
                            c = stats_sem[sem]['credits']
                            p = stats_sem[sem]['points']
                            tot_c += c
                            tot_p += p
                            mgp_s = p / c if c > 0 else 0
                            cols[i].metric(f"MGP {sem}", f"{mgp_s:.2f} / 4.00")
                            
                        mgp_gen = tot_p / tot_c if tot_c > 0 else 0
                        cols[-1].metric("MGP Générale", f"{mgp_gen:.2f} / 4.00", delta="Bilan")
                    else:
                        st.warning("Aucune matière valide n'a été saisie dans le tableau.")
                else:
                    st.error("⚠️ Veuillez remplir les informations obligatoires de l'étudiant (Nom, Prénom, Matricule).")

    # ── IMPORTER ──────────────────────────────────────────────────────────────
    elif page_edu == "📤 Importer CSV/Excel":
        st.markdown("### Importation de données — Éducation")
        st.markdown("""
        <div class="info-box">
            📋 <strong>Format attendu :</strong> nom, prenom, matricule, filiere, niveau, semestre, matiere, credits, note_cc, note_tp, note_examen
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([2,1])
        with col1:
            uploaded = st.file_uploader("Choisir un fichier", type=["csv", "xlsx", "xls"])
        with col2:
            # Generate template
            template = pd.DataFrame({
                'nom': ['Dupont', 'Martin'],
                'prenom': ['Jean', 'Marie'],
                'matricule': ['20INF001', '20INF002'],
                'filiere': ['Informatique', 'Informatique'],
                'niveau': ['Licence 2', 'Licence 2'],
                'semestre': ['S1', 'S2'],
                'matiere': ['Analyse de données', 'Algèbre'],
                'credits': [6.0, 6.0],
                'note_cc': [14.5, 12.0],
                'note_tp': [25.0, 20.5],
                'note_examen': [38.0, 42.5]
            })
            buffer = io.BytesIO()
            template.to_excel(buffer, index=False)
            st.download_button("📥 Télécharger le modèle", buffer.getvalue(),
                               "modele_etudiants.xlsx", use_container_width=True)

        if uploaded:
            try:
                if uploaded.name.endswith('.csv'):
                    df_import = pd.read_csv(uploaded)
                else:
                    df_import = pd.read_excel(uploaded)

                st.markdown(f"**{len(df_import)} ligne(s) détectée(s) :**")
                st.dataframe(df_import.head(10), use_container_width=True)

                if st.button("✅ Confirmer l'importation", use_container_width=True):
                    conn = get_conn()
                    count = 0
                    for _, row in df_import.iterrows():
                        try:
                            ncc = float(row.get('note_cc', 0))
                            ntp = float(row.get('note_tp', 0))
                            nex = float(row.get('note_examen', 0))
                            nf = round((ncc + ntp + nex) / 5, 2)
                            ment = mention(nf)
                            creds = float(row.get('credits', 6.0))
                            conn.execute("""
                                INSERT INTO etudiants (nom, prenom, matricule, filiere, niveau, semestre,
                                matiere, note_cc, note_tp, note_examen, note_finale, mention, absences, date_saisie, credits)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                            """, (row.get('nom',''), row.get('prenom',''), row.get('matricule',''),
                                  row.get('filiere',''), row.get('niveau',''), row.get('semestre',''),
                                  row.get('matiere',''), ncc, ntp, nex,
                                  nf, ment, 0,
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), creds))
                            count += 1
                        except: pass
                    conn.commit()
                    conn.close()
                    st.markdown(f'<div class="success-msg">✅ {count} enregistrement(s) importé(s) avec succès !</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier : {e}")

    # ── ANALYSE ───────────────────────────────────────────────────────────────
    elif page_edu == "📊 Analyse descriptive":
        st.markdown("### Analyse descriptive — Éducation")
        df = get_etudiants()

        if df.empty:
            st.warning("⚠️ Aucune donnée disponible. Commencez par saisir ou importer des données.")
        else:
            # KPIs
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: st.metric("👨‍🎓 Total étudiants", len(df))
            with col2:
                if 'credits' in df.columns and df['credits'].sum() > 0:
                    moy_pond = np.average(df['note_finale'], weights=df['credits'])
                else:
                    moy_pond = df['note_finale'].mean()
                st.metric("📈 Moyenne pondérée", f"{moy_pond:.2f}/20")
            with col3: st.metric("🏆 Note max", f"{df['note_finale'].max():.2f}/20")
            with col4: st.metric("📉 Note min", f"{df['note_finale'].min():.2f}/20")
            with col5:
                taux = len(df[df['note_finale'] >= 10]) / len(df) * 100
                st.metric("✅ Taux de réussite", f"{taux:.1f}%")

            st.markdown("---")
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Distributions", "🎓 Par filière", "📚 Par matière", "📋 Statistiques"])

            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.histogram(df, x='note_finale', nbins=20,
                                       title="Distribution des notes finales",
                                       color_discrete_sequence=['#e94560'],
                                       template='plotly_dark')
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      font_color="#c8c8d8")
                    fig.add_vline(x=10, line_dash="dash", line_color="#00d084", annotation_text="Seuil 10/20")
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    mention_counts = df['mention'].value_counts()
                    fig2 = px.pie(values=mention_counts.values, names=mention_counts.index,
                                  title="Répartition des mentions",
                                  color_discrete_sequence=['#e94560','#a855f7','#00d084','#f59e0b','#64748b'],
                                  template='plotly_dark', hole=0.4)
                    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#c8c8d8')
                    st.plotly_chart(fig2, use_container_width=True)

                # Box plot notes
                fig3 = px.box(df, x='niveau', y='note_finale', color='niveau',
                              title="Distribution des notes par niveau",
                              template='plotly_dark',
                              color_discrete_sequence=['#e94560','#a855f7','#00d084','#f59e0b','#3b82f6','#ef4444'])
                fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                   font_color='#c8c8d8', showlegend=False)
                st.plotly_chart(fig3, use_container_width=True)

            with tab2:
                moy_filiere = df.groupby('filiere').agg(
                    Moyenne=('note_finale','mean'),
                    Effectif=('id','count'),
                    Taux_reussite=('note_finale', lambda x: (x>=10).mean()*100)
                ).round(2).reset_index()

                col1, col2 = st.columns(2)
                with col1:
                    fig = px.bar(moy_filiere, x='filiere', y='Moyenne',
                                 title="Moyenne par filière",
                                 color='Moyenne', color_continuous_scale='RdPu',
                                 template='plotly_dark')
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      font_color='#c8c8d8')
                    fig.add_hline(y=10, line_dash="dash", line_color="#00d084")
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig2 = px.bar(moy_filiere, x='filiere', y='Taux_reussite',
                                  title="Taux de réussite par filière (%)",
                                  color='Taux_reussite', color_continuous_scale='Greens',
                                  template='plotly_dark')
                    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       font_color='#c8c8d8')
                    st.plotly_chart(fig2, use_container_width=True)

                st.dataframe(moy_filiere.style.background_gradient(subset=['Moyenne'], cmap='RdPu'),
                             use_container_width=True)

            with tab3:
                moy_mat = df.groupby('matiere').agg(
                    Moyenne=('note_finale','mean'),
                    Effectif=('id','count')
                ).round(2).sort_values('Moyenne', ascending=True).reset_index()

                fig = px.bar(moy_mat, x='Moyenne', y='matiere', orientation='h',
                             title="Moyenne par matière", color='Moyenne',
                             color_continuous_scale='RdPu', template='plotly_dark')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  font_color='#c8c8d8')
                st.plotly_chart(fig, use_container_width=True)

            with tab4:
                st.markdown("**Statistiques descriptives complètes**")
                stats = df[['note_cc','note_tp','note_examen','note_finale']].describe().round(3)
                stats.index = ['Nb observations','Moyenne','Écart-type','Minimum','Q1 (25%)','Médiane (50%)','Q3 (75%)','Maximum']
                st.dataframe(stats.style.background_gradient(cmap='RdPu'), use_container_width=True)

                # Correlation
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.scatter(df, x='note_cc', y='note_examen', color='mention',
                                     title="Corrélation CC vs Examen",
                                     template='plotly_dark',
                                     color_discrete_sequence=['#e94560','#a855f7','#00d084','#f59e0b','#64748b'])
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      font_color='#c8c8d8')
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig2 = px.scatter(df, x='note_tp', y='note_finale',
                                      title="Corrélation TP vs Note Finale",
                                      color='mention', template='plotly_dark',
                                      color_discrete_sequence=['#e94560','#a855f7','#00d084','#f59e0b','#64748b'])
                    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       font_color='#c8c8d8')
                    st.plotly_chart(fig2, use_container_width=True)

    # ── BULLETIN DE NOTES ─────────────────────────────────────────────────────
    elif page_edu == "🎓 Bulletin de notes":
        st.markdown("### 🎓 Bulletin de notes (Relevé Officiel)")
        df = get_etudiants()
        if df.empty:
            st.warning("⚠️ Aucune donnée disponible.")
        else:
            col_search, col_sem = st.columns(2)
            etudiants_uniques = df[['matricule', 'nom', 'prenom']].drop_duplicates()
            etudiants_list = etudiants_uniques['matricule'] + " - " + etudiants_uniques['nom'] + " " + etudiants_uniques['prenom']
            
            with col_search:
                search_etu = st.selectbox("Sélectionnez un étudiant", etudiants_list.tolist())
                matricule_sel = search_etu.split(" - ")[0]
            
            with col_sem:
                semestres = ["Tous"] + list(df[df['matricule'] == matricule_sel]['semestre'].unique())
                sem_sel = st.selectbox("Semestre", semestres)
                
            df_etu = df[df['matricule'] == matricule_sel].copy()
            if sem_sel != "Tous":
                df_etu = df_etu[df_etu['semestre'] == sem_sel].copy()
                
            st.markdown("---")
            if df_etu.empty:
                st.info("Aucun résultat pour ce filtre.")
            else:
                nom_etu = df_etu['nom'].iloc[0]
                prenom_etu = df_etu['prenom'].iloc[0]
                niveau_etu = df_etu['niveau'].iloc[0]
                st.markdown(f"**Étudiant :** {prenom_etu} {nom_etu} | **Matricule :** {matricule_sel} | **Niveau :** {niveau_etu}")
                
                if 'credits' not in df_etu.columns:
                    df_etu['credits'] = 6.0
                    
                # Compute LMD fields dynamically
                df_etu[['Grade', 'Points', 'Decision']] = df_etu.apply(
                    lambda row: pd.Series(get_lmd_info(row['note_finale'])), axis=1
                )
                    
                total_credits = df_etu['credits'].sum()
                if total_credits > 0:
                    moy_gen = np.average(df_etu['note_finale'], weights=df_etu['credits'])
                    mgp_4 = np.average(df_etu['Points'], weights=df_etu['credits'])
                else:
                    moy_gen = df_etu['note_finale'].mean()
                    mgp_4 = df_etu['Points'].mean()
                    
                credits_valides = df_etu[df_etu['Decision'].isin(['Validé', 'Capitalisé'])]['credits'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("MGP (GPA) Globale", f"{mgp_4:.2f} / 4.00")
                c2.metric("Moyenne Globale", f"{moy_gen:.2f} / 20")
                c3.metric("Crédits Cumulés", f"{credits_valides:.0f} / {total_credits:.0f}")
                
                if sem_sel == "Tous":
                    semestres_presents = sorted(df_etu['semestre'].unique())
                    if len(semestres_presents) > 1:
                        st.markdown("#### 📅 Détail MGP par Semestre")
                        cols_sem = st.columns(len(semestres_presents))
                        for i, sem in enumerate(semestres_presents):
                            df_s = df_etu[df_etu['semestre'] == sem]
                            tc_s = df_s['credits'].sum()
                            mgp_s = np.average(df_s['Points'], weights=df_s['credits']) if tc_s > 0 else 0.0
                            cv_s = df_s[df_s['Decision'].isin(['Validé', 'Capitalisé'])]['credits'].sum()
                            cols_sem[i].metric(f"MGP {sem}", f"{mgp_s:.2f}", f"{cv_s:.0f}/{tc_s:.0f} Crédits", delta_color="off")
                
                st.markdown("#### Relevé par unité d'enseignement")
                df_show = df_etu[['matiere', 'credits', 'note_cc', 'note_tp', 'note_examen', 'note_finale', 'Grade', 'Points', 'Decision', 'semestre']].copy()
                df_show.columns = ['Unité d\'Enseignement', 'Crédits', 'CC/20', 'TP/30', 'EE/50', 'Moy/20', 'Cote', 'Points', 'Décision', 'Semestre']
                st.dataframe(df_show, use_container_width=True)
                
                # PDF Download Button
                try:
                    current_etu_info = {
                        'nom': nom_etu, 'prenom': prenom_etu, 'matricule': matricule_sel,
                        'filiere': niveau_etu.split(' ')[0], 'niveau': niveau_etu, 'semestre': sem_sel
                    }
                    pdf_bulletin = generate_bulletin_pdf(df_etu, current_etu_info)
                    st.download_button(
                        label="📄 Télécharger le Bulletin (PDF)",
                        data=bytes(pdf_bulletin),
                        file_name=f"Bulletin_{nom_etu}_{sem_sel}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erreur PDF : {e}")
                
                if sem_sel == "Tous":
                    if credits_valides >= 45:
                        st.markdown(f'<div class="success-msg">🎊 Bilan Annuel : ADMIS EN CLASSE SUPÉRIEURE (Crédits acquis : {credits_valides:.0f}/{total_credits:.0f}) !</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"🛑 Bilan Annuel : AJOURNÉ (Redoublement). Seulement {credits_valides:.0f}/{total_credits:.0f} crédits acquis (45 requis pour passage conditionnel).")
                else:
                    if credits_valides == total_credits and total_credits > 0:
                        st.markdown(f'<div class="success-msg">✅ Semestre Totalement Validé avec {credits_valides:.0f} crédits obtenus !</div>', unsafe_allow_html=True)
                    elif credits_valides > 0:
                        st.warning(f"⚠️ Semestre Partiellement Validé (Crédits acquis : {credits_valides:.0f}/{total_credits:.0f}).")
                    else:
                        st.error(f"❌ Semestre Non Validé - Aucun crédit acquis.")
                
                st.markdown("---")
                if st.button("⬅️ Retour à la saisie de données", use_container_width=True):
                    st.info("💡 Remontez tout simplement en haut de la page et choisissez **'➕ Saisir des données'** dans la petite boîte de Navigation.")

    # ── TOUTES DONNÉES ────────────────────────────────────────────────────────
    elif page_edu == "🗃️ Voir toutes les données":
        st.markdown("### Toutes les données — Étudiants")
        df = get_etudiants()
        if df.empty:
            st.warning("⚠️ Aucune donnée disponible.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                filtre_filiere = st.selectbox("Filtrer par filière", ["Toutes"] + list(df['filiere'].unique()))
            with col2:
                filtre_niveau = st.selectbox("Filtrer par niveau", ["Tous"] + list(df['niveau'].unique()))
            with col3:
                filtre_semestre = st.selectbox("Filtrer par semestre", ["Tous"] + list(df['semestre'].unique()))
            with col4:
                filtre_mention = st.selectbox("Filtrer par mention", ["Toutes"] + list(df['mention'].unique()))

            df_filtered = df.copy()
            if filtre_filiere != "Toutes": df_filtered = df_filtered[df_filtered['filiere'] == filtre_filiere]
            if filtre_niveau != "Tous": df_filtered = df_filtered[df_filtered['niveau'] == filtre_niveau]
            if filtre_semestre != "Tous": df_filtered = df_filtered[df_filtered['semestre'] == filtre_semestre]
            if filtre_mention != "Toutes": df_filtered = df_filtered[df_filtered['mention'] == filtre_mention]

            st.markdown(f"**{len(df_filtered)} enregistrement(s) trouvé(s)**")
            st.dataframe(df_filtered.drop(columns=['date_saisie']), use_container_width=True)

            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exporter en CSV", csv, "etudiants.csv", "text/csv", use_container_width=True)

    # ── PREDICTION IA ─────────────────────────────────────────────────────────
    elif page_edu == "🤖 Prédiction (IA)":
        st.markdown("### 🤖 Prédiction (Régression Linéaire)")
        df = get_etudiants()
        if len(df) < 3:
            st.warning("⚠️ Pas assez de données pour l'apprentissage. Veuillez saisir au moins 3 étudiants.")
        else:
            st.markdown("Dans ce module de **Machine Learning**, nous utilisons la régression linéaire simple pour prédire la Note d'Examen en fonction de la Note de CC.")
            
            x = df['note_cc'].values
            y = df['note_examen'].values
            a, b = np.polyfit(x, y, 1)
            
            st.info(f"**Équation du modèle :** Note Examen = {a:.2f} × (Note CC) + {b:.2f}")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("#### Testez le modèle")
                cc_input = st.number_input("Entrez une note de CC (sur 20)", 0.0, 20.0, 10.0, step=0.5)
                pred_examen = a * cc_input + b
                pred_examen = max(0, min(20, pred_examen))
                
                pred_finale = cc_input * 0.4 + pred_examen * 0.6
                
                st.markdown(f'''
                <div class="metric-card edu-card">
                    <div style="font-size:0.9rem; color:#8888a8;">Note d'Examen estimée :</div>
                    <div style="font-size:2rem; font-weight:800; color:#e94560;">{pred_examen:.2f} / 20</div>
                    <hr>
                    <div style="font-size:0.9rem; color:#8888a8;">Note Finale estimée :</div>
                    <div style="font-size:1.5rem; font-weight:700; color:#e8e8f0;">{pred_finale:.2f} / 20</div>
                </div>
                ''', unsafe_allow_html=True)
                
            with col2:
                fig = px.scatter(df, x='note_cc', y='note_examen', color='mention',
                                 title="Droite de régression (CC vs Examen)",
                                 template='plotly_dark')
                x_range = np.array([0, 20])
                fig.add_trace(go.Scatter(x=x_range, y=a*x_range + b, 
                                         mode='lines', name='Tendance linéaire',
                                         line=dict(color='#00d084', width=3, dash='dash')))
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#c8c8d8')
                st.plotly_chart(fig, use_container_width=True)

    # ── ADMINISTRATION ────────────────────────────────────────────────────────
    elif page_edu == "⚙️ Administration":
        st.markdown("### ⚙️ Administration & Nettoyage")
        st.markdown("Espace réservé à la maintenance de la base de données.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Supprimer un étudiant")
            df = get_etudiants()
            if df.empty:
                st.info("La base est vide.")
            else:
                etu_list = df['id'].astype(str) + " - " + df['prenom'] + " " + df['nom'] + " (" + df['matricule'] + ")"
                to_delete = st.selectbox("Sélectionnez l'étudiant à supprimer", df['id'].tolist(), format_func=lambda x: etu_list[df['id'] == x].values[0])
                if st.button("🗑️ Supprimer la sélection", key="btn_del_etu"):
                    row_e = df[df['id'] == to_delete].iloc[0]
                    details_e = f"Matricule: {row_e['matricule']} | {row_e['prenom']} {row_e['nom']} | {row_e['filiere']} - {row_e['niveau']}"
                    conn = get_conn()
                    conn.execute("DELETE FROM etudiants WHERE id=?", (to_delete,))
                    conn.commit()
                    conn.close()
                    log_action("Éducation", "SUPPRESSION ÉTUDIANT", f"ID#{to_delete} - {details_e}")
                    st.success("Étudiant supprimé avec succès !")
                    st.rerun()
                    
        with col2:
            st.markdown("#### Zone de Danger")
            if st.button("🚨 Vider TOUTE la base Éducation", help="Action irréversible !"):
                df_before_edu = get_etudiants()
                conn = get_conn()
                conn.execute("DELETE FROM etudiants")
                conn.commit()
                conn.close()
                log_action("Éducation", "VIDAGE BASE ÉTUDIANTS", f"{len(df_before_edu)} enregistrement(s) supprimé(s) en une fois.")
                st.success("La base de données Éducation a été entièrement vidée.")
                st.rerun()

        # ── JOURNAL D'AUDIT (ÉDUCATION) ───────────────────────────────────────
        st.markdown("---")
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(233,69,96,0.12), rgba(168,85,247,0.08));
                    border: 1px solid rgba(233,69,96,0.3); border-radius: 14px; padding: 20px; margin-bottom: 16px;'>
            <div style='font-family:Syne; font-size:1.15rem; font-weight:800; color:#e94560; margin-bottom:4px;'>
                🔍 Journal d'Audit — Traçabilité des Actions
            </div>
            <div style='color:#8888a8; font-size:0.88rem;'>
                Toutes les suppressions effectuées dans le module Éducation sont enregistrées ici. Aucune action ne peut être cachée.
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_audit_edu = get_audit_logs()
        # Filtrer uniquement les actions Education
        df_audit_edu = df_audit_edu[df_audit_edu['module'] == 'Éducation']
        
        if df_audit_edu.empty:
            st.info("Éducation : Aucune action enregistrée dans le journal pour le moment.")
        else:
            def color_action_edu(val):
                if "SUPPRESSION" in val or "VIDAGE" in val:
                    return 'color: #e94560; font-weight: bold'
                return 'color: #00d084;'

            st.markdown(f"⚠️ **{len(df_audit_edu)} action(s)** enregistrée(s) pour ce module.")
            st.dataframe(
                df_audit_edu[['horodatage', 'action', 'details']]
                .rename(columns={'horodatage': 'Date & Heure', 'action': 'Action', 'details': 'Détails'})
                .style.map(color_action_edu, subset=['Action']),
                use_container_width=True,
                hide_index=True
            )
            csv_edu = df_audit_edu.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exporter le Journal Éducation (CSV)",
                data=csv_edu,
                file_name=f"audit_education_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COMMERCE
# ═══════════════════════════════════════════════════════════════════════════════
elif module == "🛒 Commerce":
    st.markdown('<span class="section-badge com-badge">🛒 Module Commerce</span>', unsafe_allow_html=True)

    # ── SAISIR ────────────────────────────────────────────────────────────────
    if page_com == "➕ Saisir des données":
        st.markdown("### Saisie des données de ventes")

        with st.form("form_vente", clear_on_submit=True):
            st.markdown("#### 🛒 Détails de la Transaction")
            col1, col2, col3 = st.columns(3)
            with col1:
                vendeur = st.text_input("Vendeur / Agent", help="Identité de l'agent commercial.", placeholder="Ex: Paul", key="vendeur_com")
            with col2:
                region = st.selectbox("Région de vente", ["Centre", "Littoral", "Ouest", "Nord", "Adamaoua", "Est", "Sud", "Sud-Ouest", "Nord-Ouest", "Extrême-Nord", "Autre"])
            with col3:
                mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile Money", "Orange Money" ,"Carte bancaire"])
                date_vente = st.date_input("Date de vente", value=date.today())

            st.markdown("---")
            st.markdown("#### 📦 Articles du Panier")
            
            # Grille de produits par défaut
            default_sales = pd.DataFrame([{"Produit": "", "Catégorie": "Alimentaire", "Quantité": 1, "Prix unitaire (FCFA)": 0.0}])

            edited_sales = st.data_editor(
                default_sales,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Produit": st.column_config.TextColumn("Désignation Produit", required=True),
                    "Catégorie": st.column_config.SelectboxColumn("Catégorie", options=["Électronique", "Alimentaire", "Vêtements", "Mobilier", "Fournitures", "Autre"]),
                    "Quantité": st.column_config.NumberColumn("Qté", min_value=1, step=1, required=True),
                    "Prix unitaire (FCFA)": st.column_config.NumberColumn("Prix Unitaire", min_value=0.0, step=25.0, required=True)
                }
            )

            submitted = st.form_submit_button("💳 Enregistrer la Facture / Vente", use_container_width=True)

            if submitted:
                if vendeur:
                    conn = get_conn()
                    total_facture = 0
                    articles_count = 0
                    
                    for index, row in edited_sales.iterrows():
                        prod = row.get("Produit")
                        if pd.isna(prod) or str(prod).strip() == "":
                            continue
                            
                        cat = row.get("Catégorie", "Autre")
                        qte = int(row.get("Quantité", 1))
                        pu = float(row.get("Prix unitaire (FCFA)", 0.0))
                        montant = round(qte * pu, 2)
                        
                        conn.execute("""
                            INSERT INTO ventes (produit, categorie, quantite, prix_unitaire,
                            montant_total, region, vendeur, date_vente, mode_paiement, date_saisie)
                            VALUES (?,?,?,?,?,?,?,?,?,?)
                        """, (prod, cat, qte, pu, montant,
                              region, vendeur, str(date_vente), mode_paiement,
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
                        total_facture += montant
                        articles_count += 1
                        
                    conn.commit()
                    conn.close()
                    
                    if articles_count > 0:
                        log_action(
                            "Commerce", "NOUVELLE VENTE",
                            f"Vendeur: {vendeur} | Région: {region} | {articles_count} article(s) | Total: {total_facture:,.0f} FCFA | Paiement: {mode_paiement} | Date: {date_vente}"
                        )
                        st.markdown(f"""
                        <div class="success-msg" style="border-left: 5px solid #00d084;">
                            🎉 <strong>Vente réussie !</strong><br>
                            🧾 Facture enregistrée par <strong>{vendeur}</strong><br>
                            📦 {articles_count} articles traités<br>
                            💰 TOTAL : <span style="font-size: 1.5rem;">{total_facture:,.0f} FCFA</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Invoice PDF Button
                        try:
                            vente_info = {
                                'vendeur': vendeur, 'region': region, 'date_vente': str(date_vente),
                                'mode_paiement': mode_paiement
                            }
                            pdf_invoice = generate_facture_pdf(edited_sales, vente_info)
                            st.download_button(
                                label="🧾 Imprimer la Facture (PDF)",
                                data=bytes(pdf_invoice),
                                file_name=f"Facture_{datetime.now().strftime('%d%m%Y_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Erreur Facture PDF : {e}")
                    else:
                        st.error("⚠️ Veuillez entrer le nom du vendeur pour valider la transaction.")

    # ── GESTION DES STOCKS (ACHATS) ───────────────────────────────────────────
    elif page_com == "📥 Entrées Stock (Achats)":
        st.markdown("### 📦 Gestion des Stocks & Approvisionnements")
        
        tab1, tab2, tab3 = st.tabs(["🛒 Nouvel Achat (Stock +)", "📊 État des Stocks", "📜 Historique des Achats"])
        
        with tab1:
            with st.container(border=True):
                st.markdown("#### Enregistrer un arrivage de marchandise")
                with st.form("form_achat", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        fournisseur = st.text_input("Fournisseur", placeholder="Ex: Grossiste ABC...")
                        date_achat = st.date_input("Date d'achat", value=date.today())
                    with col2:
                        st.info("💡 Saisissez vos achats dans la grille ci-dessous.")

                    # Grille d'achats
                    df_default_achats = pd.DataFrame([{"Produit": "", "Catégorie": "Alimentaire", "Quantité": 10, "Prix d'Achat (Unitaire)": 0.0}])
                    
                    edited_achats = st.data_editor(
                        df_default_achats,
                        num_rows="dynamic",
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Produit": st.column_config.TextColumn("Désignation Produit", required=True),
                            "Catégorie": st.column_config.SelectboxColumn("Catégorie", options=["Électronique", "Alimentaire", "Vêtements", "Mobilier", "Fournitures", "Autre"]),
                            "Quantité": st.column_config.NumberColumn("Qté achetée", min_value=1, step=1),
                            "Prix d'Achat (Unitaire)": st.column_config.NumberColumn("Prix d'Achat (Cout)", min_value=0.0, step=50.0)
                        }
                    )
                    
                    btn_achat = st.form_submit_button("📥 Valider l'entrée en Stock", use_container_width=True)
                
                if btn_achat:
                    if fournisseur:
                        conn = get_conn()
                        total_depense = 0
                        count_a = 0
                        for _, row in edited_achats.iterrows():
                            p = row.get("Produit")
                            if pd.isna(p) or str(p).strip() == "": continue
                            
                            c = row.get("Catégorie", "Autre")
                            q = int(row.get("Quantité", 0))
                            pa = float(row.get("Prix d'Achat (Unitaire)", 0.0))
                            
                            conn.execute("""
                                INSERT INTO achats (produit, categorie, quantite, prix_achat, fournisseur, date_achat, date_saisie)
                                VALUES (?,?,?,?,?,?,?)
                            """, (p, c, q, pa, fournisseur, str(date_achat), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            
                            total_depense += (q * pa)
                            count_a += 1
                        
                        conn.commit()
                        conn.close()
                        if count_a > 0:
                            log_action(
                                "Commerce", "NOUVEL ACHAT STOCK",
                                f"Fournisseur: {fournisseur} | {count_a} produit(s) | Dépense totale: {total_depense:,.0f} FCFA | Date achat: {date_achat}"
                            )
                            st.markdown(f'<div class="success-msg">✅ {count_a} produits ajoutés au stock ! Dépense totale : {total_depense:,.0f} FCFA</div>', unsafe_allow_html=True)
                        else:
                            st.warning("Aucun produit valide saisi.")
                    else:
                        st.error("Veuillez préciser le fournisseur.")

        with tab2:
            st.markdown("#### 📊 Tableau de bord de l'Inventaire")
            df_achats = get_achats()
            df_ventes = get_ventes()
            
            if df_achats.empty and df_ventes.empty:
                st.info("Aucune donnée de stock ou de vente disponible.")
            else:
                # Calculer les stocks par produit
                stock_in = df_achats.groupby('produit')['quantite'].sum().reset_index().rename(columns={'quantite': 'Entrées'})
                stock_out = df_ventes.groupby('produit')['quantite'].sum().reset_index().rename(columns={'quantite': 'Sorties'})
                
                # Récupérer et calculer les ajustements
                df_ajust = get_ajustements()
                if not df_ajust.empty:
                    stock_adj = df_ajust.groupby('produit')['quantite_ajustee'].sum().reset_index().rename(columns={'quantite_ajustee': 'Ajustements'})
                else:
                    stock_adj = pd.DataFrame(columns=['produit', 'Ajustements'])
                
                # Fusionner pour avoir l'état global
                inventory = pd.merge(stock_in, stock_out, on='produit', how='outer').fillna(0)
                inventory = pd.merge(inventory, stock_adj, on='produit', how='outer').fillna(0)
                
                inventory['Stock Actuel'] = inventory['Entrées'] - inventory['Sorties'] + inventory['Ajustements']
                
                # Styling
                def color_stock(val):
                    color = '#00d084' if val > 5 else '#e94560'
                    return f'color: {color}; font-weight: bold'

                st.dataframe(
                    inventory.style.map(color_stock, subset=['Stock Actuel']),
                    use_container_width=True
                )
                
                # Alertes
                stock_bas = inventory[inventory['Stock Actuel'] <= 5]['produit'].tolist()
                if stock_bas:
                    st.error(f"🚨 **ALERTE STOCK BAS :** {', '.join(stock_bas)} (Moins de 5 unités restantes !)")

        with tab3:
            st.markdown("#### 📜 Historique chronologique des approvisionnements")
            df_ach = get_achats()
            if df_ach.empty:
                st.info("Aucun achat enregistré pour le moment.")
            else:
                # Colonnes de recherche
                c1, c2 = st.columns(2)
                with c1:
                    search_p = st.text_input("Filtrer par produit (achat)", placeholder="Rechercher...")
                with c2:
                    search_f = st.text_input("Filtrer par fournisseur", placeholder="Rechercher...")
                
                df_f = df_ach.copy()
                if search_p:
                    df_f = df_f[df_f['produit'].str.contains(search_p, case=False, na=False)]
                if search_f:
                    df_f = df_f[df_f['fournisseur'].str.contains(search_f, case=False, na=False)]
                
                # Ajout d'une colonne montant total pour l'affichage
                df_f['Montant Total'] = df_f['quantite'] * df_f['prix_achat']
                
                st.dataframe(
                    df_f[['date_achat', 'produit', 'categorie', 'quantite', 'prix_achat', 'Montant Total', 'fournisseur']],
                    use_container_width=True,
                    hide_index=True
                )
                
                st.metric("Total investi en stock sur la sélection", f"{df_f['Montant Total'].sum():,.0f} FCFA")

    # ── IMPORTER ──────────────────────────────────────────────────────────────
    elif page_com == "📤 Importer CSV/Excel":
        st.markdown("### Importation de données — Commerce")
        st.markdown("""
        <div class="info-box">
            📋 <strong>Format attendu :</strong> produit, categorie, quantite, prix_unitaire, region, vendeur, date_vente, mode_paiement
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([2,1])
        with col1:
            uploaded = st.file_uploader("Choisir un fichier", type=["csv", "xlsx", "xls"])
        with col2:
            template = pd.DataFrame({
                'produit': ['Téléphone', 'Cahier'],
                'categorie': ['Électronique', 'Fournitures'],
                'quantite': [5, 100],
                'prix_unitaire': [150000, 500],
                'region': ['Centre', 'Littoral'],
                'vendeur': ['Paul', 'Marie'],
                'date_vente': ['2024-01-15', '2024-01-16'],
                'mode_paiement': ['Mobile Money', 'Espèces']
            })
            buffer = io.BytesIO()
            template.to_excel(buffer, index=False)
            st.download_button("📥 Télécharger le modèle", buffer.getvalue(),
                               "modele_ventes.xlsx", use_container_width=True)

        if uploaded:
            try:
                if uploaded.name.endswith('.csv'):
                    df_import = pd.read_csv(uploaded)
                else:
                    df_import = pd.read_excel(uploaded)

                st.markdown(f"**{len(df_import)} ligne(s) détectée(s) :**")
                st.dataframe(df_import.head(10), use_container_width=True)

                if st.button("✅ Confirmer l'importation", use_container_width=True):
                    conn = get_conn()
                    count = 0
                    for _, row in df_import.iterrows():
                        try:
                            qt = int(row.get('quantite', 1))
                            pu = float(row.get('prix_unitaire', 0))
                            mt = round(qt * pu, 2)
                            conn.execute("""
                                INSERT INTO ventes (produit, categorie, quantite, prix_unitaire,
                                montant_total, region, vendeur, date_vente, mode_paiement, date_e)
                                VALUES (?,?,?,?,?,?,?,?,?,?)
                            """, (row.get('produit',''), row.get('categorie',''), qt, pu, mt,
                                  row.get('region',''), row.get('vendeur',''),
                                  str(row.get('date_vente','')), row.get('mode_paiement','Espèces'),
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            count += 1
                        except: pass
                    conn.commit()
                    conn.close()
                    st.markdown(f'<div class="success-msg">✅ {count} enregistrement(s) importé(s) avec succès !</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erreur : {e}")

    # ── ANALYSE ───────────────────────────────────────────────────────────────
    elif page_com == "📊 Analyse descriptive":
        st.markdown("### Analyse descriptive — Commerce")
        df = get_ventes()

        if df.empty:
            st.warning("⚠️ Aucune donnée disponible. Commencez par saisir ou importer des données.")
        else:
            st.markdown("#### 📅 Filtres temporel")
            df['date_vente'] = pd.to_datetime(df['date_vente'], errors='coerce')
            valid_dates = df.dropna(subset=['date_vente'])
            min_date = valid_dates['date_vente'].min().date() if not valid_dates.empty else date(2020, 1, 1)
            max_date = valid_dates['date_vente'].max().date() if not valid_dates.empty else date.today()
            
            c1, c2 = st.columns(2)
            with c1:
                start_date = st.date_input("Date de début", value=min_date, min_value=min_date, max_value=max_date)
            with c2:
                end_date = st.date_input("Date de fin", value=max_date, min_value=min_date, max_value=max_date)
                
            mask = (df['date_vente'].dt.date >= start_date) & (df['date_vente'].dt.date <= end_date)
            df = df.loc[mask]
            
            if df.empty:
                st.warning("Aucune vente sur cette période.")
                st.stop()

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: st.metric("📦 Total ventes", len(df))
            with col2: st.metric("💰 CA Total", f"{df['montant_total'].sum():,.0f} FCFA")
            with col3: st.metric("📈 Vente moyenne", f"{df['montant_total'].mean():,.0f} FCFA")
            with col4: st.metric("🔢 Qté totale", f"{df['quantite'].sum():,}")
            with col5: st.metric("🛍️ Produits distincts", df['produit'].nunique())

            st.markdown("---")
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Vue générale", "🗺️ Par région", "📦 Par produit", "📋 Statistiques"])

            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    cat_ca = df.groupby('categorie')['montant_total'].sum().sort_values(ascending=False).reset_index()
                    fig = px.bar(cat_ca, x='categorie', y='montant_total',
                                 title="Chiffre d'affaires par catégorie",
                                 color='montant_total', color_continuous_scale='Greens',
                                 template='plotly_dark')
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      font_color='#c8c8d8')
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    mode_count = df['mode_paiement'].value_counts()
                    fig2 = px.pie(values=mode_count.values, names=mode_count.index,
                                  title="Modes de paiement", hole=0.4,
                                  color_discrete_sequence=['#00d084','#a855f7','#e94560','#f59e0b','#3b82f6'],
                                  template='plotly_dark')
                    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#c8c8d8')
                    st.plotly_chart(fig2, use_container_width=True)

                if 'date_vente' in df.columns and df['date_vente'].notna().any():
                    try:
                        df['date_vente'] = pd.to_datetime(df['date_vente'], errors='coerce')
                        df_time = df.dropna(subset=['date_vente'])
                        if not df_time.empty:
                            daily = df_time.groupby('date_vente')['montant_total'].sum().reset_index()
                            fig3 = px.line(daily, x='date_vente', y='montant_total',
                                           title="Évolution du CA dans le temps",
                                           template='plotly_dark', line_shape='spline')
                            fig3.update_traces(line_color='#00d084', fill='tozeroy',
                                               fillcolor='rgba(0,208,132,0.1)')
                            fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                               font_color='#c8c8d8')
                            st.plotly_chart(fig3, use_container_width=True)
                    except: pass

            with tab2:
                region_ca = df.groupby('region').agg(
                    CA=('montant_total','sum'),
                    Ventes=('id','count'),
                    Qte=('quantite','sum')
                ).round(2).sort_values('CA', ascending=False).reset_index()

                col1, col2 = st.columns(2)
                with col1:
                    fig = px.bar(region_ca, x='region', y='CA', title="CA par région",
                                 color='CA', color_continuous_scale='Greens', template='plotly_dark')
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      font_color='#c8c8d8')
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig2 = px.pie(region_ca, values='CA', names='region',
                                  title="Part du CA par région", hole=0.35,
                                  template='plotly_dark',
                                  color_discrete_sequence=px.colors.qualitative.Dark2)
                    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#c8c8d8')
                    st.plotly_chart(fig2, use_container_width=True)

                st.dataframe(region_ca.style.background_gradient(subset=['CA'], cmap='Greens'),
                             use_container_width=True)

            with tab3:
                prod_stats = df.groupby('produit').agg(
                    CA=('montant_total','sum'),
                    Quantite=('quantite','sum'),
                    Ventes=('id','count'),
                    Prix_moy=('prix_unitaire','mean')
                ).round(2).sort_values('CA', ascending=False).head(15).reset_index()

                fig = px.bar(prod_stats, x='CA', y='produit', orientation='h',
                             title="Top 15 produits par CA", color='CA',
                             color_continuous_scale='Greens', template='plotly_dark')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  font_color='#c8c8d8')
                st.plotly_chart(fig, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    fig2 = px.scatter(df, x='quantite', y='montant_total', color='categorie',
                                      title="Quantité vs Montant total",
                                      template='plotly_dark',
                                      color_discrete_sequence=px.colors.qualitative.Dark2)
                    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                       font_color='#c8c8d8')
                    st.plotly_chart(fig2, use_container_width=True)

            with tab4:
                st.markdown("**Statistiques descriptives complètes**")
                stats = df[['quantite','prix_unitaire','montant_total']].describe().round(2)
                stats.index = ['Nb observations','Moyenne','Écart-type','Minimum','Q1 (25%)','Médiane (50%)','Q3 (75%)','Maximum']
                st.dataframe(stats.style.background_gradient(cmap='Greens'), use_container_width=True)

    # ── TOUTES DONNÉES ────────────────────────────────────────────────────────
    elif page_com == "🗃️ Voir toutes les données":
        st.markdown("### Toutes les données — Ventes")
        df = get_ventes()
        if df.empty:
            st.warning("⚠️ Aucune donnée disponible.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                filtre_cat = st.selectbox("Filtrer par catégorie", ["Toutes"] + list(df['categorie'].unique()))
            with col2:
                filtre_region = st.selectbox("Filtrer par région", ["Toutes"] + list(df['region'].unique()))
            with col3:
                filtre_vendeur = st.selectbox("Filtrer par vendeur", ["Tous"] + list(df['vendeur'].unique()))

            col4, col5 = st.columns([1, 2])
            with col4:
                filtre_mode = st.selectbox("Filtrer par paiement", ["Tous"] + list(df['mode_paiement'].unique()))
            with col5:
                # Filtrage par date si la colonne existe
                if 'date_vente' in df.columns:
                    df['date_vente_dt'] = pd.to_datetime(df['date_vente']).dt.date
                    date_min, date_max = df['date_vente_dt'].min(), df['date_vente_dt'].max()
                    filtre_dates = st.date_input("Filtrer par période", [date_min, date_max], min_value=date_min, max_value=date_max)
                else:
                    filtre_dates = None

            df_filtered = df.copy()
            if filtre_cat != "Toutes": df_filtered = df_filtered[df_filtered['categorie'] == filtre_cat]
            if filtre_region != "Toutes": df_filtered = df_filtered[df_filtered['region'] == filtre_region]
            if filtre_vendeur != "Tous": df_filtered = df_filtered[df_filtered['vendeur'] == filtre_vendeur]
            if filtre_mode != "Tous": df_filtered = df_filtered[df_filtered['mode_paiement'] == filtre_mode]
            
            if filtre_dates and len(filtre_dates) == 2:
                df_filtered['date_vente_dt'] = pd.to_datetime(df_filtered['date_vente']).dt.date
                df_filtered = df_filtered[(df_filtered['date_vente_dt'] >= filtre_dates[0]) & 
                                          (df_filtered['date_vente_dt'] <= filtre_dates[1])]
                df_filtered = df_filtered.drop(columns=['date_vente_dt'])

            st.markdown(f"**{len(df_filtered)} enregistrement(s) — CA filtré : {df_filtered['montant_total'].sum():,.0f} FCFA**")
            st.dataframe(df_filtered.drop(columns=['date_saisie']), use_container_width=True)

            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exporter en CSV", csv, "ventes.csv", "text/csv", use_container_width=True)

    # ── PREDICTION IA ─────────────────────────────────────────────────────────
    elif page_com == "🤖 Prédiction (IA)":
        st.markdown("### 🤖 Prédiction (Régression Linéaire) - Ventes")
        df = get_ventes()
        if len(df) < 3:
            st.warning("⚠️ Pas assez de données pour l'apprentissage. Veuillez saisir au moins 3 ventes.")
        else:
            st.markdown("Ce module d'**Intelligence Artificielle** utilise une régression linéaire simple pour modéliser le Montant Total en fonction de la Quantité vendue.")
            
            x = df['quantite'].values
            y = df['montant_total'].values
            a, b = np.polyfit(x, y, 1)
            
            st.info(f"**Modèle linéaire global :** Montant Total = {a:.2f} × Quantité + {b:.2f} FCFA")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("#### Estimateur de CA global")
                qt_input = st.number_input("Entrez une quantité suggérée", 1, 10000, 10)
                pred_ca = a * qt_input + b
                pred_ca = max(0, pred_ca)
                
                st.markdown(f'''
                <div class="metric-card com-card">
                    <div style="font-size:0.9rem; color:#8888a8;">Chiffre d'Affaires estimé :</div>
                    <div style="font-size:2rem; font-weight:800; color:#00d084;">{pred_ca:,.0f} FCFA</div>
                </div>
                ''', unsafe_allow_html=True)
                
            with col2:
                fig = px.scatter(df, x='quantite', y='montant_total', color='categorie',
                                 title="Droite de régression (Quantité vs Montant)",
                                 template='plotly_dark')
                x_range = np.array([df['quantite'].min(), df['quantite'].max()])
                fig.add_trace(go.Scatter(x=x_range, y=a*x_range + b, 
                                         mode='lines', name='Tendance',
                                         line=dict(color='#e94560', width=3, dash='dash')))
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#c8c8d8')
                st.plotly_chart(fig, use_container_width=True)

    # ── ADMINISTRATION ────────────────────────────────────────────────────────
    elif page_com == "⚙️ Administration":
        st.markdown("### ⚙️ Administration & Nettoyage (Ventes)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Supprimer une vente")
            df = get_ventes()
            if df.empty:
                st.info("La base est vide.")
            else:
                vente_list = df['id'].astype(str) + " - " + df['produit'] + " (" + df['montant_total'].astype(str) + " FCFA)"
                to_delete = st.selectbox("Sélectionnez la vente à supprimer", df['id'].tolist(), format_func=lambda x: vente_list[df['id'] == x].values[0])
                if st.button("🗑️ Supprimer la sélection", key="btn_del_vente"):
                    row_v = df[df['id'] == to_delete].iloc[0]
                    details_v = f"Produit: {row_v['produit']} | Qté: {row_v['quantite']} | Montant: {row_v['montant_total']} FCFA | Vendeur: {row_v['vendeur']} | Date: {row_v['date_vente']}"
                    conn = get_conn()
                    conn.execute("DELETE FROM ventes WHERE id=?", (to_delete,))
                    conn.commit()
                    conn.close()
                    log_action("Commerce", "SUPPRESSION VENTE", f"ID#{to_delete} - {details_v}")
                    st.success("Vente supprimée avec succès !")
                    st.rerun()
                    
        with col2:
            st.markdown("#### Zone de Danger")
            if st.button("🚨 Vider TOUTE la base Commerce", help="Action irréversible !"):
                conn = get_conn()
                df_before = get_ventes()
                conn.execute("DELETE FROM ventes")
                conn.commit()
                conn.close()
                log_action("Commerce", "VIDAGE BASE VENTES", f"{len(df_before)} enregistrements supprimés en une fois.")
                st.success("La base de données Commerce a été entièrement vidée.")
                st.rerun()
                    
        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("#### Supprimer une entrée de stock (Achat)")
            df_a = get_achats()
            if df_a.empty:
                st.info("Aucun achat en base.")
            else:
                ach_list = df_a['id'].astype(str) + " - " + df_a['produit'] + " (" + df_a['quantite'].astype(str) + " unités)"
                to_del_ach = st.selectbox("Sélectionnez l'achat à supprimer", df_a['id'].tolist(), format_func=lambda x: ach_list[df_a['id'] == x].values[0])
                if st.button("🗑️ Supprimer cet achat", key="btn_del_ach"):
                    row_a = df_a[df_a['id'] == to_del_ach].iloc[0]
                    details_a = f"Produit: {row_a['produit']} | Qté: {row_a['quantite']} | Fournisseur: {row_a['fournisseur']}"
                    conn = get_conn()
                    conn.execute("DELETE FROM achats WHERE id=?", (to_del_ach,))
                    conn.commit()
                    conn.close()
                    log_action("Commerce", "SUPPRESSION ACHAT", f"ID#{to_del_ach} - {details_a}")
                    st.success("Entrée de stock supprimée !")
                    st.rerun()
        
        st.markdown("### 🛠️ Correction & Ajustement Approfondis")
        col_mod, col_reg = st.columns(2)
        
        with col_mod:
            st.markdown("#### ✏️ Modifier une erreur sur un Achat")
            df_a = get_achats()
            if not df_a.empty:
                ach_list_full = df_a['id'].astype(str) + " - " + df_a['produit'] + " (" + df_a['fournisseur'] + ")"
                ach_to_edit = st.selectbox("Sélectionner l'achat à corriger", df_a['id'].tolist(), format_func=lambda x: ach_list_full[df_a['id'] == x].values[0], key="sel_edit_ach")
                
                # Formulaire de modification
                row = df_a[df_a['id'] == ach_to_edit].iloc[0]
                with st.form("form_edit_achat"):
                    new_prod = st.text_input("Désignation Produit", value=row['produit'])
                    col_q, col_p = st.columns(2)
                    new_qty = col_q.number_input("Quantité", value=int(row['quantite']), min_value=1)
                    new_pu = col_p.number_input("Prix Achat Unitaire", value=float(row['prix_achat']), min_value=0.0)
                    new_fourn = st.text_input("Fournisseur", value=row['fournisseur'])
                    
                    if st.form_submit_button("✅ Enregistrer les modifications"):
                        old_qty = int(row['quantite'])
                        old_prod = row['produit']
                        conn = get_conn()
                        conn.execute("""
                            UPDATE achats SET produit=?, quantite=?, prix_achat=?, fournisseur=?
                            WHERE id=?
                        """, (new_prod, new_qty, new_pu, new_fourn, ach_to_edit))
                        conn.commit()
                        conn.close()
                        log_action(
                            "Commerce", "MODIFICATION ACHAT",
                            f"ID#{ach_to_edit} | Produit: '{old_prod}' → '{new_prod}' | Qté: {old_qty} → {new_qty} | Prix: {row['prix_achat']} → {new_pu} | Fourn: {row['fournisseur']} → {new_fourn}"
                        )
                        st.success("Achat mis à jour avec succès !")
                        st.rerun()
            else:
                st.info("Aucun achat à modifier.")

        with col_reg:
            st.markdown("#### ⚖️ Régularisation Manuelle (Inventaire)")
            st.info("Utilisez ceci pour corriger le stock sans modifier les factures d'achat (ex: casse, vol, don, erreur inventaire brute).")
            
            with st.form("form_regu_stock", clear_on_submit=True):
                # Liste des produits existants pour suggérer
                df_v_reg = get_ventes()
                df_a_reg = get_achats()
                all_prods = sorted(list(set(df_v_reg['produit'].unique().tolist() + df_a_reg['produit'].unique().tolist())))
                prod_reg = st.selectbox("Produit à régulariser", all_prods if all_prods else ["Aucun produit"])
                qty_reg = st.number_input("Quantité à ajouter/retirer", value=0, help="Positif pour ajouter (ex: stock retrouvé), Négatif pour retirer (ex: casse).")
                motif_reg = st.selectbox("Motif de l'ajustement", ["Erreur de saisie", "Casse / Avarie", "Vol / Perte", "Don / Échantillon", "Inventaire physique", "Autre"])
                date_reg = st.date_input("Date du constat", value=date.today())
                
                if st.form_submit_button("💾 Valider la régularisation"):
                    if prod_reg and prod_reg != "Aucun produit" and qty_reg != 0:
                        conn = get_conn()
                        conn.execute("""
                            INSERT INTO ajustements (produit, quantite_ajustee, motif, date_ajustement, date_saisie)
                            VALUES (?,?,?,?,?)
                        """, (prod_reg, qty_reg, motif_reg, str(date_reg), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        conn.close()
                        signe = "+" if qty_reg > 0 else ""
                        log_action(
                            "Commerce", "AJUSTEMENT STOCK",
                            f"Produit: '{prod_reg}' | Quantité ajustée: {signe}{qty_reg} | Motif: {motif_reg} | Date constat: {date_reg}"
                        )
                        st.success(f"Stock ajusté de {qty_reg} pour '{prod_reg}' !")
                        st.rerun()
                    else:
                        st.error("Veuillez remplir correctement les champs.")

        # Historique des régularisations
        st.markdown("---")
        st.markdown("#### 📜 Historique des Ajustements Manuels")
        df_aj = get_ajustements()
        if not df_aj.empty:
            st.dataframe(df_aj[['date_ajustement', 'produit', 'quantite_ajustee', 'motif']], use_container_width=True, hide_index=True)
            if st.button("🗑️ Effacer tout l'historique des ajustements"):
                 conn = get_conn()
                 conn.execute("DELETE FROM ajustements")
                 conn.commit()
                 conn.close()
                 log_action("Commerce", "VIDAGE AJUSTEMENTS", "Tout l'historique des ajustements manuels a été effacé.")
                 st.rerun()
        else:
            st.info("Aucun ajustement manuel enregistré.")

        # ── JOURNAL D'AUDIT ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(233,69,96,0.12), rgba(168,85,247,0.08));
                    border: 1px solid rgba(233,69,96,0.3); border-radius: 14px; padding: 20px; margin-bottom: 16px;'>
            <div style='font-family:Syne; font-size:1.15rem; font-weight:800; color:#e94560; margin-bottom:4px;'>
                🔍 Journal d'Audit — Traçabilité des Actions
            </div>
            <div style='color:#8888a8; font-size:0.88rem;'>
                Toutes les modifications, suppressions et ajustements effectués sont enregistrés ici automatiquement.
                Aucune action sensible ne peut être cachée.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        df_audit = get_audit_logs()
        if df_audit.empty:
            st.info("Aucune action enregistrée dans le journal pour le moment.")
        else:
            # Filtres rapides
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtre_action = st.selectbox(
                    "Filtrer par type d'action",
                    ["Toutes"] + sorted(df_audit['action'].unique().tolist())
                )
            with col_f2:
                filtre_module = st.selectbox(
                    "Filtrer par module",
                    ["Tous"] + sorted(df_audit['module'].unique().tolist())
                )
            
            df_audit_f = df_audit.copy()
            if filtre_action != "Toutes":
                df_audit_f = df_audit_f[df_audit_f['action'] == filtre_action]
            if filtre_module != "Tous":
                df_audit_f = df_audit_f[df_audit_f['module'] == filtre_module]
            
            st.markdown(f"⚠️ **{len(df_audit_f)} action(s) enregistrée(s)** dans le journal (filtré).")
            
            # Affichage avec badge couleur
            def color_action(val):
                if "SUPPRESSION" in val or "VIDAGE" in val:
                    return 'color: #e94560; font-weight: bold'
                elif "MODIFICATION" in val:
                    return 'color: #f59e0b; font-weight: bold'
                elif "AJUSTEMENT" in val:
                    return 'color: #a855f7; font-weight: bold'
                return 'color: #00d084;'
            
            st.dataframe(
                df_audit_f[['horodatage', 'module', 'action', 'details']]
                .rename(columns={'horodatage': 'Date & Heure', 'module': 'Module', 'action': 'Action', 'details': 'Détails'})
                .style.map(color_action, subset=['Action']),
                use_container_width=True,
                hide_index=True
            )
            
            # Export CSV
            csv_audit = df_audit_f.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exporter le Journal (CSV)",
                data=csv_audit,
                file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
