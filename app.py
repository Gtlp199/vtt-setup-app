import streamlit as st
import pandas as pd
from datetime import datetime

# Import pour la connexion Google Sheets
try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS_LIB = True
except ImportError:
    HAS_GSHEETS_LIB = False

# Configuration de la page Streamlit
st.set_page_config(
    page_title="VTT Suspension & Torque Manager",
    page_icon="🚵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application CSS Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .status-badge-ok {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 0.4rem 0.8rem;
        border-radius: 0.375rem;
        font-weight: bold;
        display: inline-block;
    }
    .status-badge-warn {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.4rem 0.8rem;
        border-radius: 0.375rem;
        font-weight: bold;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DONNÉES GROUNDÉES DE LA BASE DE DONNÉES DES VÉLOS
# ---------------------------------------------------------

BIKES_DATA = {
    "pivot_ampd_2026": {
        "name": "Pivot Shuttle AMP'd (2026)",
        "type": "E-VTTAE All-Mountain / Enduro (Moteur Avinox)",
        "weight_ref": "85 kg",
        "suspensions_recommended": {
            "fork": {
                "model": "RockShox ZEB Ultimate 3.2 (160mm)",
                "pressure": "152 - 154 psi (10.5 - 10.6 bar)",
                "sag": "15% - 20% (24 - 32 mm)",
                "lsr": "7 - 8 clics depuis ouvert (sens horaire)",
                "lsc": "Position Médiane (Middle)",
                "hsc": "Position Médiane (Middle)"
            },
            "shock": {
                "model": "RockShox Super Deluxe Ultimate (185x55mm)",
                "pressure": "237 psi (Calcul Pivot: 2.2 x 85kg + 50 psi)",
                "sag": "30% (16.5 mm)",
                "lsr": "8 clics depuis ouvert (sens horaire)",
                "lsc": "Position Médiane (Middle)",
                "hsc": "Position Médiane (Middle)"
            }
        },
        "torques": [
            {"zone": "Cadre & Cinématique", "component": "Link Bolt M14x20 (Main Link) [Réf #13]", "torque": "35 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Flip Chip Bolt M14x20 [Réf #15]", "torque": "35 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Trunnion Mount Bolt M10x16.5 [Réf #14]", "torque": "13 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Front Shock Bolt M8x45.7 [Réf #12]", "torque": "13 Nm", "notes": "Graisse axe / Loctite filet"},
            {"zone": "Cadre & Cinématique", "component": "Axe de roue arrière 157mm UDH", "torque": "15 Nm", "notes": "Graisser le filetage"},
            {"zone": "Transmission & Moteur", "component": "Vis de patte SRAM UDH [Réf #5]", "torque": "25 Nm", "notes": "Pas à droite / UDH Bolt"},
            {"zone": "Transmission & Moteur", "component": "Vis de montage Moteur Avinox M2S [Réf J]", "torque": "25 Nm", "notes": "Loctite 243"},
            {"zone": "Transmission & Moteur", "component": "Ecrou Spider Plateau Avinox [Réf K]", "torque": "35 Nm", "notes": "Graisser"},
            {"zone": "Transmission & Moteur", "component": "Fixation Batterie 800Wh [Réf I]", "torque": "5 Nm", "notes": "Loctite 243"},
            {"zone": "Composants", "component": "Vis Sabot Moteur M6x12 [Réf #23]", "torque": "6 Nm", "notes": "Loctite 243"},
            {"zone": "Composants", "component": "Vis Anti-dérailleur M5x12 [Réf #35]", "torque": "5 Nm", "notes": "Loctite 243"}
        ],
        "schematic_info": "Manuel d'atelier Pivot Shuttle AMP'd (Avinox System)."
    },
    "transition_patrol_2024": {
        "name": "Transition Patrol Carbone (2024/2025)",
        "type": "Enduro Musculaire (Mullet)",
        "weight_ref": "85 kg",
        "suspensions_recommended": {
            "fork": {
                "model": "Öhlins RXF 38 m.2 Kit Coil (160mm)",
                "pressure": "N/A (Ressort Helicoidal)",
                "spring_rate": "Ressort 9.7 N/mm (Blanc / 82kg) à 10.6 N/mm (Noir / 91kg)",
                "sag": "15% - 20% (24 - 32 mm)",
                "preload": "0 à 2 tours max depuis contact",
                "lsr": "Ajustement selon sensation (sens horaire)",
                "lsc": "Ajustement progressif",
                "hsc": "4 positions (1-3 descente, 0 blocage montees)"
            },
            "shock": {
                "model": "Öhlins TTX 22 Coil (205x65mm)",
                "pressure": "N/A (Ressort Helicoidal)",
                "spring_rate": "Ressort 457 lbs",
                "sag": "25% - 35% (16.25 - 22.75 mm)",
                "preload": "2 tours complets maximum après contact",
                "lsr": "Compter clics depuis fermeture complète (Pos 0)",
                "lsc": "Molette bleue (Ajuster selon motricité)",
                "hsc": "3 positions (I: Souple, II: Polyvalent, III: Pédalage)"
            }
        },
        "torques": [
            {"zone": "Cadre & Cinématique", "component": "Axe de roue arrière (UDH) [Réf #33]", "torque": "10 - 12 Nm", "notes": "Graisser les filets"},
            {"zone": "Cadre & Cinématique", "component": "Axe du pivot principal (Main Pivot) [Réf #5/#7]", "torque": "19 Nm", "notes": "Frein filet bleu / Graisser l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Axe central de la biellette [Réf #27/#29]", "torque": "19 Nm", "notes": "Serrage croisé et progressif"},
            {"zone": "Cadre & Cinématique", "component": "Pivots de haubans [Réf #25]", "torque": "19 Nm", "notes": "Vérifier sens des entretoises coniques"},
            {"zone": "Cadre & Cinématique", "component": "Pivots de bases (Horst Link) [Réf #16]", "torque": "19 Nm", "notes": "Vis larges spécifiques cadre carbone"},
            {"zone": "Cadre & Cinématique", "component": "Fixations d'amortisseur Haute/Basse [Réf #11, #19/#22]", "torque": "10 - 12 Nm", "notes": "Ne pas dépasser pour ne pas brider"},
            {"zone": "Transmission & Moteur", "component": "Vis de la patte UDH [Réf #35]", "torque": "25 Nm", "notes": "Attention: Filetage inversé (anti-horaire)"},
            {"zone": "Freins", "component": "Disques SRAM HS2 (Moyeux Hope Pro 5)", "torque": "6.2 Nm", "notes": "Torx T25 / Serrage en étoile"},
            {"zone": "Freins", "component": "Étriers SRAM Maven (Fixation Post Mount)", "torque": "9.5 Nm", "notes": "Centrer l'étrier levier serré"}
        ],
        "schematic_info": "Vue éclatée officielle Transition Patrol ASM Carbon."
    },
    "santacruz_vala_2026": {
        "name": "Santa Cruz Vala GX AXS (2026)",
        "type": "E-VTTAE All-Mountain (Bosch Gen 5)",
        "weight_ref": "85 kg",
        "suspensions_recommended": {
            "fork": {
                "model": "FOX 38 Float Performance Elite, Grip X2 (160mm)",
                "pressure": "~89 - 93 psi (pour 85kg)",
                "sag": "15% - 20% (24 - 32 mm)",
                "lsr": "9 - 10 clics depuis ouvert",
                "hsr": "3 clics depuis ouvert",
                "lsc": "6 clics depuis ouvert",
                "hsc": "4 clics depuis ouvert"
            },
            "shock": {
                "model": "FOX Float X Performance Elite (205x60mm)",
                "pressure": "~210 - 227 psi (pour 85kg)",
                "sag": "30% (18 mm)",
                "lsr": "8 clics depuis ouvert",
                "lsc": "5 - 6 clics depuis ouvert"
            }
        },
        "torques": [
            {"zone": "Cadre & Cinématique", "component": "Pivot Axle M15x91 [Label C]", "torque": "20 Nm", "notes": "Loctite 242 sur filet / Graisse sur axe"},
            {"zone": "Cadre & Cinématique", "component": "Trunnion Screw M10x10 [Label T]", "torque": "16 Nm", "notes": "Loctite 242"},
            {"zone": "Cadre & Cinématique", "component": "Ancrage Inférieur Amortisseur M8x45 [Label H]", "torque": "15.6 Nm", "notes": "Loctite 242"},
            {"zone": "Cadre & Cinématique", "component": "Pivot Horst Link / Bases [Label F]", "torque": "9 Nm", "notes": "Loctite 242"},
            {"zone": "Transmission & Moteur", "component": "Vis Moteur Bosch DU (BDU38) [Label N, O]", "torque": "30 Nm", "notes": "Réf Bosch EB11.200.15J"},
            {"zone": "Transmission & Moteur", "component": "Patte SRAM UDH [Label C]", "torque": "20 Nm", "notes": "Pas à gauche (Reverse thread)"},
            {"zone": "Composants", "component": "Vis de Disque 6 Trous", "torque": "6 Nm", "notes": "Torx T25"},
            {"zone": "Composants", "component": "Étriers de Frein Post Mount", "torque": "9 - 10 Nm", "notes": "Alignement étrier"}
        ],
        "schematic_info": "Vues éclatées Santa Cruz Vala 2026 Carbon."
    },
    "norco_sight_2024": {
        "name": "Norco Sight Carbon Gen 5 (2024)",
        "type": "All-Mountain / Enduro",
        "weight_ref": "80-90 kg",
        "suspensions_recommended": {
            "fork": {
                "model": "Öhlins RXF 38 m.2 Air (170mm)",
                "pressure": "Chambre Principale: 100 - 110 psi | Chambre Ramp Up: 190 - 200 psi",
                "sag": "10% - 15% (17 - 25.5 mm)",
                "lsr": "10 - 11 clics depuis ouvert",
                "note_gonflage": "⚠️ Gonfler la chambre Ramp Up EN PREMIER, puis la chambre principale."
            },
            "shock": {
                "model": "Öhlins TTX Air 2 (205x60mm)",
                "pressure": "~170 - 190 psi (pour SAG 30%)",
                "sag": "25% - 35% (cible: 18 mm / 30%)",
                "lsr": "Ajustement Öhlins TTX (depuis fermé)",
                "lsc": "Molette bleue (Position Médiane)",
                "hsc": "3 positions (1: Souple, 2: Polyvalent, P: Pédalage)"
            }
        },
        "torques": [
            {"zone": "Cadre & Cinématique", "component": "Main Pivot Shaft (Axe Pivot Principal)", "torque": "21 Nm", "notes": "Graisser l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Linkarm to Front Triangle (Trunnion)", "torque": "16 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Linkarm to Seat Stays", "torque": "14 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Chain Stay to Seat Stays", "torque": "14 Nm", "notes": "Loctite 243"},
            {"zone": "Transmission & Moteur", "component": "UDH Derailleur Hanger Bolt", "torque": "20 Nm", "notes": "Pas à gauche (Left hand thread)"},
            {"zone": "Cadre & Cinématique", "component": "Axe de roue arrière 12x148mm", "torque": "10 Nm", "notes": "Graisser le filetage"}
        ],
        "schematic_info": "Norco Sight Carbon Gen 5 Assembly Document (MY24)."
    }
}

# Initialisation de la mémoire locale de session
if "local_history" not in st.session_state:
    st.session_state.local_history = []

# ---------------------------------------------------------
# LOGIQUE DE CONNEXION GOOGLE SHEETS
# ---------------------------------------------------------

gsheets_connected = False
conn = None

if HAS_GSHEETS_LIB:
    try:
        # Vérifier si les secrets Streamlit contiennent la configuration gsheets
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            conn = st.connection("gsheets", type=GSheetsConnection)
            gsheets_connected = True
    except Exception as e:
        gsheets_connected = False

# ---------------------------------------------------------
# INTERFACE PRINCIPALE
# ---------------------------------------------------------

st.markdown('<div class="main-header">🚵 VTT Technical & Setup Manager</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Gestionnaire de réglages suspensions & couples de serrage synchronisé Cloud</div>', unsafe_allow_html=True)

# Barre latérale : Sélection du vélo et configuration
st.sidebar.header("⚙️ Configuration Vélo & Pilote")

selected_bike_key = st.sidebar.selectbox(
    "Choisissez votre vélo :",
    options=list(BIKES_DATA.keys()),
    format_func=lambda x: BIKES_DATA[x]["name"]
)

bike_info = BIKES_DATA[selected_bike_key]

st.sidebar.info(f"**Modèle** : {bike_info['name']}\n\n**Type** : {bike_info['type']}")

user_weight = st.sidebar.number_input("Poids du pilote équipé (kg) :", min_value=40, max_value=130, value=85)

# Status de synchronisation Google Sheets
st.sidebar.divider()
st.sidebar.header("☁️ Synchronisation Cloud")

if gsheets_connected:
    st.sidebar.markdown('<div class="status-badge-ok">🟢 Google Sheets Connecté</div>', unsafe_allow_html=True)
    st.sidebar.caption("Vos réglages enregistrés sont automatiquement synchronisés avec votre feuille Google Sheets.")
else:
    st.sidebar.markdown('<div class="status-badge-warn">🟡 Sauvegarde Locale & CSV</div>', unsafe_allow_html=True)
    st.sidebar.caption("Les réglages sont sauvegardés pendant votre session. Pour activer la synchro Google Sheets automatique, configurez vos clés d'accès.")

    with st.sidebar.expander("🛠️ Comment connecter Google Sheets ?"):
        st.write("""
        **Procédure rapide (3 min) :**
        1. Créez une feuille **Google Sheets** sur votre Google Drive.
        2. Allez sur votre tableau de bord **Streamlit Community Cloud**.
        3. Dans les paramètres de votre App (*Settings -> Secrets*), ajoutez la configuration `[connections.gsheets]` avec votre lien Google Sheet et les clés d'API Google Service Account.
        """)

# Choix de la rubrique
nav_option = st.radio(
    "Sélectionnez la rubrique :",
    ["🔧 Réglages Suspensions", "🔩 Couples de Serrage & Schémas"],
    horizontal=True
)

st.divider()

# ---------------------------------------------------------
# RUBRIQUE 1 : RÉGLAGES SUSPENSIONS
# ---------------------------------------------------------
if nav_option == "🔧 Réglages Suspensions":
    st.subheader(f"📊 Préconisations Suspensions - {bike_info['name']} ({user_weight} kg)")
    
    recom = bike_info["suspensions_recommended"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🍴 Fourche Avant")
        fork = recom["fork"]
        st.write(f"**Modèle** : {fork['model']}")
        if "pressure" in fork:
            st.write(f"**Pression recommandée** : `{fork['pressure']}`")
        if "spring_rate" in fork:
            st.write(f"**Ressort recommandé** : `{fork['spring_rate']}`")
        st.write(f"**SAG Cible** : {fork['sag']}")
        if "preload" in fork:
            st.write(f"**Précontrainte** : {fork['preload']}")
        st.write(f"**Rebond (LSR/HSR)** : {fork.get('lsr', 'N/A')}")
        if "note_gonflage" in fork:
            st.warning(fork["note_gonflage"])

    with col2:
        st.markdown("### 🛞 Amortisseur Arrière")
        shock = recom["shock"]
        st.write(f"**Modèle** : {shock['model']}")
        if "pressure" in shock:
            st.write(f"**Pression recommandée** : `{shock['pressure']}`")
        if "spring_rate" in shock:
            st.write(f"**Ressort recommandé** : `{shock['spring_rate']}`")
        st.write(f"**SAG Cible** : {shock['sag']}")
        if "preload" in shock:
            st.write(f"**Précontrainte** : {shock['preload']}")
        st.write(f"**Rebond (LSR)** : {shock.get('lsr', 'N/A')}")
        st.write(f"**Compression (LSC/HSC)** : LSC `{shock.get('lsc', 'N/A')}` | HSC `{shock.get('hsc', 'N/A')}`")

    st.divider()
    
    # FORMULAIRE DE SAISIE TERRAIN
    st.subheader("📝 Saisie de vos réglages du jour (Terrain)")
    st.write("Remplissez ce formulaire sur le terrain pour enregistrer vos sensations et ajustements.")
    
    with st.form("ride_setup_form"):
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            date_ride = st.date_input("Date de la sortie", datetime.today())
            terrain_type = st.selectbox("Type de terrain", ["Flow / Smooth", "Sol cassant / Racines", "Bike Park / Gros impacts", "Boue / Glissant"])
            weather_cond = st.selectbox("Météo", ["Sec / Ensoleillé", "Humide / Pluie légère", "Très humide / Boue"])
            
        with f_col2:
            st.markdown("**Ajustements Fourche**")
            fork_press_user = st.text_input("Pression / Ressort Fourche", value=fork.get('pressure', 'Coil'))
            fork_lsr_user = st.text_input("Rebond Fourche (clics)", value="7 clics")
            fork_comp_user = st.text_input("Compression Fourche", value="Milieu")
            
        with f_col3:
            st.markdown("**Ajustements Amortisseur**")
            shock_press_user = st.text_input("Pression / Ressort Amortisseur", value=shock.get('pressure', 'Coil'))
            shock_lsr_user = st.text_input("Rebond Amortisseur (clics)", value="8 clics")
            shock_comp_user = st.text_input("Compression Amortisseur", value="Milieu")

        comments = st.text_area("Notes & Sensations :", placeholder="Ex: -5 psi en fourche pour conserver de la motricité sur racines mouillées. Très bon maintien.")
        
        submit_button = st.form_submit_button("💾 Enregistrer la session")
        
        if submit_button:
            new_entry = {
                "Date": str(date_ride),
                "Vélo": bike_info["name"],
                "Poids_Pilote_kg": user_weight,
                "Terrain": terrain_type,
                "Météo": weather_cond,
                "Fourche_Réglage": f"{fork_press_user} | Rebond: {fork_lsr_user} | Comp: {fork_comp_user}",
                "Amortisseur_Réglage": f"{shock_press_user} | Rebond: {shock_lsr_user} | Comp: {shock_comp_user}",
                "Commentaires": comments
            }
            
            # Sauvegarde locale session
            st.session_state.local_history.append(new_entry)
            
            # Sauvegarde Google Sheets si connecté
            if gsheets_connected and conn is not None:
                try:
                    existing_data = conn.read()
                    updated_df = pd.concat([pd.DataFrame(existing_data), pd.DataFrame([new_entry])], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("✅ Réglage enregistré et synchronisé automatiquement sur Google Sheets !")
                except Exception as err:
                    st.warning(f"Enregistré en mémoire locale. Erreur synchro Google Sheets: {err}")
            else:
                st.success("✅ Réglage enregistré dans l'historique de session !")

    # TABLEAU DE L'HISTORIQUE
    if st.session_state.local_history:
        st.subheader("📚 Historique de vos réglages enregistrés")
        df_hist = pd.DataFrame(st.session_state.local_history)
        st.dataframe(df_hist, use_container_width=True)
        
        # Bouton d'exportation CSV
        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger l'historique complet (.csv)",
            data=csv_data,
            file_name=f"vtt_setups_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ---------------------------------------------------------
# RUBRIQUE 2 : COUPLES DE SERRAGE & SCHÉMAS
# ---------------------------------------------------------
else:
    st.subheader(f"🔩 Couples de Serrage & Documentation - {bike_info['name']}")
    
    st.info(f"📄 **Référence schéma** : {bike_info['schematic_info']}")
    
    torques_df = pd.DataFrame(bike_info["torques"])
    
    # Filtre par Zone
    zones = ["Toutes les zones"] + list(torques_df["zone"].unique())
    selected_zone = st.selectbox("Filtrer par zone du vélo :", zones)
    
    if selected_zone != "Toutes les zones":
        filtered_df = torques_df[torques_df["zone"] == selected_zone]
    else:
        filtered_df = torques_df
        
    st.dataframe(
        filtered_df[["zone", "component", "torque", "notes"]],
        column_config={
            "zone": "Zone",
            "component": "Composant / Axe",
            "torque": "Couple préconisé (Nm)",
            "notes": "Instructions (Frein filet / Graisse)"
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("""
    ---
    ### 💡 Rappels de Sécurité & Montage Atelier :
    * **Patte SRAM UDH** : La vis de blocage UDH possède un **filetage inversé / pas à gauche** (serrer dans le sens anti-horaire) à **20–25 Nm**.
    * **Frein filet** : Utilisez du frein filet moyen (ex: Loctite 242/243) sur les filetages spécifiés.
    * **Graissage des axes** : Appliquez de la graisse uniquement sur le fût / corps de l'axe, jamais sur les filets recevant du frein filet.
    * **Étriers de frein (Post Mount)** : Serrage recommandé à **9.5 Nm**. Centrer l'étrier levier enfoncé.
    * **Disques de frein (SRAM HS2 6 trous)** : Serrage à **6.2 Nm** en étoile croisée (clé Torx T25).
    """)

# Footer
st.divider()
st.caption("Gemini Notebook Studio - VTT Setup & Torque Application.")
