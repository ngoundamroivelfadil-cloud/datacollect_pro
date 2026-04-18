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
html, body, [class*="css"] {
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

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox select, .stDateInput input {
    background: #f0f2f6 !important;
    border: 1px solid #888888 !important;
    border-radius: 10px !important;
    color: #000000 !important;
    caret-color: #000000 !important;
    box-sizing: border-box !important;
    max-width: 100% !important;
    margin: 0 !important;
}

.stTextInput input::placeholder, .stNumberInput input::placeholder {
    color: #555555 !important;
    opacity: 1 !important;
}

.stTextInput input:focus, .stNumberInput input:focus {
    border-color: rgba(233,69,96,0.5) !important;
    box-shadow: 0 0 0 2px rgba(233,69,96,0.1) !important;
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

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #00d084, #00a86b) !important;
    color: #0a0a0f !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
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

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }

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
            INF 232 · EC2
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
            ["➕ Saisir des données", "📤 Importer CSV/Excel", "📊 Analyse descriptive", "🗃️ Voir toutes les données", "🤖 Prédiction (IA)", "⚙️ Administration"]
        )

    st.markdown("""
    <div style='position:fixed; bottom:20px; left:0; right:0; text-align:center;
                color:#44445a; font-size:0.72rem; padding:0 20px;'>
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
        st.metric("👨‍🎓 Étudiants enregistrés", len(df_edu))
    with col2:
        st.metric("📦 Ventes enregistrées", len(df_com))
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
    st.markdown("""
    <div class="info-box" style='text-align:center;'>
        <div style='font-family:Syne; font-size:1rem; font-weight:700; color:#c8c8d8; margin-bottom:6px;'>
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
                semestre = st.selectbox("Semestre", ["S1", "S2", "S3", "S4", "S5", "S6"])

            st.markdown("#### 2. Notes du Semestre (Saisie Multiple)")
            st.markdown("Remplissez la grille ci-dessous. Vous pouvez ajouter autant de matières que nécessaire en bas de la grille.")
            
            # Grille par défaut
            default_grid = pd.DataFrame(
                [
                    {"Matière": "INF232", "Crédits": 6.0, "Note CC": 0.0, "Note TP": 0.0, "Note EE": 0.0},
                    {"Matière": "INF212", "Crédits": 6.0, "Note CC": 0.0, "Note TP": 0.0, "Note EE": 0.0},
                    {"Matière": "MAT232", "Crédits": 6.0, "Note CC": 0.0, "Note TP": None, "Note EE": 0.0}, # Math n'a généralement pas de TP
                ]
            )
            
            edited_df = st.data_editor(
                default_grid, 
                num_rows="dynamic", 
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Matière": st.column_config.TextColumn("Unité d'enseignement", required=True),
                    "Crédits": st.column_config.NumberColumn("Crédits", min_value=1.0, max_value=30.0, step=1.0, required=True),
                    "Note CC": st.column_config.NumberColumn("Note CC", min_value=0.0, max_value=100.0, step=0.25),
                    "Note TP": st.column_config.NumberColumn("Note TP", min_value=0.0, max_value=100.0, step=0.25),
                    "Note EE": st.column_config.NumberColumn("Note EE", min_value=0.0, max_value=100.0, step=0.25)
                }
            )

            submitted = st.form_submit_button("💾 Enregistrer le Semestre", use_container_width=True)

            if submitted:
                if nom and prenom and matricule:
                    conn = get_conn()
                    count = 0
                    total_credits = 0
                    somme_points = 0
                    
                    for index, row in edited_df.iterrows():
                        matiere = row.get("Matière")
                        if pd.isna(matiere) or str(matiere).strip() == "":
                            continue
                            
                        val_creds = row.get("Crédits")
                        creds = float(val_creds) if pd.notna(val_creds) else 6.0
                        
                        val_ncc = row.get("Note CC")
                        val_ntp = row.get("Note TP")
                        val_nex = row.get("Note EE")
                        
                        ncc = float(val_ncc) if pd.notna(val_ncc) else 0.0
                        ntp = float(val_ntp) if pd.notna(val_ntp) else 0.0
                        nex = float(val_nex) if pd.notna(val_nex) else 0.0
                        
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
                        count += 1
                        total_credits += creds
                        somme_points += points * creds
                        
                    conn.commit()
                    conn.close()
                    
                    if count > 0:
                        mgp = somme_points / total_credits if total_credits > 0 else 0
                        st.markdown(f"""
                        <div class="success-msg">
                            ✅ <strong>Semestre enregistré avec succès pour {prenom} {nom} !</strong><br>
                            📊 {count} Unités d'enseignement ajoutées (Total Crédits: {total_credits:.0f})<br>
                            🎯 <strong>Moyenne Générale Pondérée (MGP) : {mgp:.2f} / 4.00</strong>
                        </div>
                        """, unsafe_allow_html=True)
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
                                      font_color='#c8c8d8')
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
                c1.metric("MGP (GPA) / 4.00", f"{mgp_4:.2f}")
                c2.metric("Moyenne Globale", f"{moy_gen:.2f} / 20")
                c3.metric("Crédits Validés", f"{credits_valides:.0f} / {total_credits:.0f}")
                
                st.markdown("#### Relevé par unité d'enseignement")
                df_show = df_etu[['matiere', 'credits', 'note_cc', 'note_tp', 'note_examen', 'note_finale', 'Grade', 'Points', 'Decision', 'semestre']].copy()
                df_show.columns = ['Unité d\'Enseignement', 'Crédits', 'CC/20', 'TP/30', 'EE/50', 'Moy/20', 'Cote', 'Points', 'Décision', 'Semestre']
                st.dataframe(df_show, use_container_width=True)
                
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
            col1, col2, col3 = st.columns(3)
            with col1:
                filtre_filiere = st.selectbox("Filtrer par filière", ["Toutes"] + list(df['filiere'].unique()))
            with col2:
                filtre_niveau = st.selectbox("Filtrer par niveau", ["Tous"] + list(df['niveau'].unique()))
            with col3:
                filtre_mention = st.selectbox("Filtrer par mention", ["Toutes"] + list(df['mention'].unique()))

            df_filtered = df.copy()
            if filtre_filiere != "Toutes": df_filtered = df_filtered[df_filtered['filiere'] == filtre_filiere]
            if filtre_niveau != "Tous": df_filtered = df_filtered[df_filtered['niveau'] == filtre_niveau]
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
                    conn = get_conn()
                    conn.execute("DELETE FROM etudiants WHERE id=?", (to_delete,))
                    conn.commit()
                    conn.close()
                    st.success("Étudiant supprimé avec succès !")
                    st.rerun()
                    
        with col2:
            st.markdown("#### Zone de Danger")
            if st.button("🚨 Vider TOUTE la base Éducation", help="Action irréversible !"):
                conn = get_conn()
                conn.execute("DELETE FROM etudiants")
                conn.commit()
                conn.close()
                st.success("La base de données Éducation a été entièrement vidée.")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COMMERCE
# ═══════════════════════════════════════════════════════════════════════════════
elif module == "🛒 Commerce":
    st.markdown('<span class="section-badge com-badge">🛒 Module Commerce</span>', unsafe_allow_html=True)

    # ── SAISIR ────────────────────────────────────────────────────────────────
    if page_com == "➕ Saisir des données":
        st.markdown("### Saisie des données de ventes")

        with st.form("form_vente", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                produit = st.text_input("Produit ", placeholder="Ex: Smartphone, Cahier...", key="produit")
                quantite = st.number_input("Quantité ", 1, 100000, 1)
                region = st.selectbox("Région ", ["Centre", "Littoral", "Ouest", "Nord", "Adamaoua", "Est", "Sud", "Sud-Ouest", "Nord-Ouest", "Extrême-Nord", "Autre"])
            with col2:
                categorie = st.selectbox("Catégorie ", ["Électronique", "Alimentaire", "Vêtements", "Mobilier", "Fournitures", "Cosmétiques", "Agriculture", "Santé", "Services", "Autre"])
                prix_unitaire = st.number_input("Prix unitaire (FCFA) ", 0.0, 10000000.0, step=25.0)
                vendeur = st.text_input("Vendeur/Agent", key="vendeur")
            with col3:
                mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Mobile Money", "Orange Money" ,"Carte bancaire", "Crypto"])
                date_vente = st.date_input("Date de vente", value=date.today())

            submitted = st.form_submit_button("💾 Enregistrer la vente", use_container_width=True)

            if submitted:
                if produit and prix_unitaire > 0:
                    montant = round(quantite * prix_unitaire, 2)
                    conn = get_conn()
                    conn.execute("""
                        INSERT INTO ventes (produit, categorie, quantite, prix_unitaire,
                        montant_total, region, vendeur, date_vente, mode_paiement, date_saisie)
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (produit, categorie, quantite, prix_unitaire, montant,
                          region, vendeur, str(date_vente), mode_paiement,
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()
                    st.markdown(f"""
                    <div class="success-msg">
                        ✅ Vente enregistrée ! <strong>{produit}</strong> × {quantite} = 
                        <strong>{montant:,.0f} FCFA</strong>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("⚠️ Veuillez remplir tous les champs obligatoires (*)")

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
                                montant_total, region, vendeur, date_vente, mode_paiement, date_saisie)
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
                filtre_mode = st.selectbox("Filtrer par paiement", ["Tous"] + list(df['mode_paiement'].unique()))

            df_filtered = df.copy()
            if filtre_cat != "Toutes": df_filtered = df_filtered[df_filtered['categorie'] == filtre_cat]
            if filtre_region != "Toutes": df_filtered = df_filtered[df_filtered['region'] == filtre_region]
            if filtre_mode != "Tous": df_filtered = df_filtered[df_filtered['mode_paiement'] == filtre_mode]

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
                    conn = get_conn()
                    conn.execute("DELETE FROM ventes WHERE id=?", (to_delete,))
                    conn.commit()
                    conn.close()
                    st.success("Vente supprimée avec succès !")
                    st.rerun()
                    
        with col2:
            st.markdown("#### Zone de Danger")
            if st.button("🚨 Vider TOUTE la base Commerce", help="Action irréversible !"):
                conn = get_conn()
                conn.execute("DELETE FROM ventes")
                conn.commit()
                conn.close()
                st.success("La base de données Commerce a été entièrement vidée.")
                st.rerun()
