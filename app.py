import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Configuration de la page Streamlit
st.set_page_config(
    page_title="VTT Technical & Suspension Manager",
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
    .metric-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2563EB;
        margin-bottom: 1rem;
    }
    .torque-header {
        background-color: #3B82F6;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DONNÉES GROUNDÉES DE LA BASE DE DONNÉES DES VÉLOS
# ---------------------------------------------------------

BIKES_DATA = {
    "pivot_ampd_2026": {
        "name": "Pivot Shuttle AMP'd (2026)",
        "type": "E-VTTAE All-Mountain / Enduro",
        "weight_ref": "85 kg",
        "suspensions_recommended": {
            "fork": {
                "model": "RockShox ZEB Ultimate 3.2 (160mm)",
                "pressure": "152 - 154 psi (10.0 - 10.6 bar)",
                "sag": "15% - 20% (24 - 32 mm)",
                "lsr": "7 - 8 clics depuis ouvert (sens horaire)",
                "lsc": "Position Médiane (Middle)",
                "hsc": "Position Médiane (Middle)"
            },
            "shock": {
                "model": "RockShox Super Deluxe Ultimate (185x55mm)",
                "pressure": "237 psi (Calcul: 2.2 x 85kg + 50 psi)",
                "sag": "30% (16.5 mm)",
                "lsr": "7 - 8 clics depuis ouvert (sens horaire)",
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
        "schematic_info": "Vue éclatée disponible dans le manuel d'atelier '8.26-Shuttle-AMPD-Product-Manual-All-Languages.pdf' (Section Small Parts & Avinox System)."
    },
    "transition_patrol_2024": {
        "name": "Transition Patrol Carbone (2024/2025)",
        "type": "Enduro Musculaire (Mullet)",
        "weight_ref": "85 kg",
        "suspensions_recommended": {
            "fork": {
                "model": "Öhlins RXF 38 m.2 Kit Coil (160mm)",
                "pressure": "N/A (Ressort Helicoidal)",
                "spring_rate": "9.7 N/mm (Blanc / 82kg) à 10.6 N/mm (Noir / 91kg)",
                "sag": "15% - 20% (24 - 32 mm)",
                "preload": "0 - 2 tours max depuis contact",
                "lsr": "Selon sensation (0 = fermé, compter clics depuis ouvert)",
                "lsc": "Ajustement progressif au sommet",
                "hsc": "4 positions (1-3 descente, 0 blocage)"
            },
            "shock": {
                "model": "Öhlins TTX 22 Coil (205x65mm)",
                "pressure": "N/A (Ressort Helicoidal)",
                "spring_rate": "457 lbs",
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
            {"zone": "Cadre & Cinématique", "component": "Pivots de bases (Horst Link) [Réf #16]", "torque": "12 - 19 Nm", "notes": "Vis spécifiques au cadre carbone"},
            {"zone": "Cadre & Cinématique", "component": "Fixations d'amortisseur Haute/Basse [Réf #11, #19/#22]", "torque": "10 - 12 Nm", "notes": "Ne pas dépasser pour ne pas brider"},
            {"zone": "Transmission & Moteur", "component": "Vis de la patte UDH [Réf #35]", "torque": "25 Nm", "notes": "Attention: Filetage inversé (anti-horaire)"},
            {"zone": "Freins", "component": "Disques SRAM HS2 (Moyeux Hope Pro 5)", "torque": "6.2 Nm", "notes": "Torx T25 / Serrage en étoile"},
            {"zone": "Freins", "component": "Étriers SRAM Maven (Fixation Post Mount)", "torque": "9.5 Nm", "notes": "Centrer l'étrier levier serré"}
        ],
        "schematic_info": "Vue éclatée disponible dans le schéma officiel '2023.02.21_PatrolASM_Explode.jpg' et 'Transition Patrol Couples de serrage - Feuille 2'."
    },
    "santacruz_vala_2026": {
        "name": "Santa Cruz Vala GX AXS (2026)",
        "type": "E-VTTAE All-Mountain (Bosch Gen 5)",
        "weight_ref": "55-85 kg",
        "suspensions_recommended": {
            "fork": {
                "model": "FOX 38 Float Performance Elite, Grip X2 (160mm)",
                "pressure": "~89 - 93 psi (pour ~85kg)",
                "sag": "15% - 20% (24 - 32 mm)",
                "lsr": "9 - 10 clics depuis ouvert (6 clics depuis fermé)",
                "hsr": "3 clics depuis ouvert (5 clics depuis fermé)",
                "lsc": "6 clics depuis ouvert",
                "hsc": "4 clics depuis ouvert"
            },
            "shock": {
                "model": "FOX Float X Performance Elite (205x60mm)",
                "pressure": "~210 - 227 psi (pour ~85kg)",
                "sag": "30% (18 mm enfoncement)",
                "lsr": "8 clics depuis ouvert (4 clics depuis fermé)",
                "lsc": "5 - 6 clics depuis ouvert"
            }
        },
        "torques": [
            {"zone": "Cadre & Cinématique", "component": "Axe Pivot Principal M15x91 [Label C]", "torque": "20 Nm", "notes": "Loctite 242 sur filet / Graisser l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Trunnion Mount M10x10 [Label T]", "torque": "16 Nm", "notes": "Loctite 242"},
            {"zone": "Cadre & Cinématique", "component": "Ancrage Inférieur Amortisseur M8x45 [Label H]", "torque": "15.6 Nm", "notes": "Loctite 242"},
            {"zone": "Cadre & Cinématique", "component": "Pivot Horst Link / Bases [Label F]", "torque": "9 Nm", "notes": "Loctite 242"},
            {"zone": "Transmission & Moteur", "component": "Vis Moteur Bosch DU (BDU38) [Label N, O]", "torque": "30 Nm", "notes": "Réf Bosch EB11.200.15J"},
            {"zone": "Transmission & Moteur", "component": "Patte SRAM UDH [Label C]", "torque": "20 Nm", "notes": "Pas à gauche (reverse thread)"},
            {"zone": "Composants", "component": "Vis de Disque 6 Trous", "torque": "6 Nm", "notes": "Torx T25"},
            {"zone": "Composants", "component": "Étriers de Frein Post Mount", "torque": "9 - 10 Nm", "notes": "Alignement étrier"}
        ],
        "schematic_info": "Vues éclatées et fiches matériels disponibles dans 'Santa Cruz Vala 2026 - Couples de Serrage et Vues Eclatees'."
    },
    "norco_sight_2024": {
        "name": "Norco Sight Carbon Gen 5 (2024)",
        "type": "All-Mountain / Enduro",
        "weight_ref": "85 kg",
        "suspensions_recommended": {
            "fork": {
                "model": "Öhlins RXF 38 m.2 Air (170mm)",
                "pressure": "Main: 100-110 psi | Ramp Up: 190-200 psi",
                "sag": "10% - 15% (17 - 25.5 mm)",
                "lsr": "10 - 11 clics depuis ouvert",
                "lsc": "Molette bleue (maintien en virage)",
                "hsc": "3 positions descente + 1 blocage"
            },
            "shock": {
                "model": "Öhlins TTX Air 2 (205x60mm)",
                "pressure": "170 - 190 psi (pour ~85kg)",
                "sag": "25% - 35% (18 mm cible)",
                "lsr": "Compter clics depuis fermeture complète",
                "lsc": "Molette bleue",
                "hsc": "Positions I (Souple), II (Polyvalent), P (Pédalage)"
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
        "schematic_info": "Schémas de câblage et vues éclatées disponibles dans 'norco-sight-carbon-gen5-(nb-095)-assembler-document'."
    }
}

CSV_FILE = "vtt_setups_history.csv"
COLUMNS = ["Date", "Vélo", "Poids_Pilote_kg", "Terrain", "Météo", "Fourche_Réglage", "Amortisseur_Réglage", "Commentaires"]

# ---------------------------------------------------------
# FONCTIONS DE GESTION DU STOCKAGE (GOOGLE SHEETS / CSV / SESSION STATE)
# ---------------------------------------------------------

def get_gsheets_connection():
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        try:
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            return conn
        except Exception:
            pass
    return None

def load_history():
    conn = get_gsheets_connection()
    if conn is not None:
        try:
            df = conn.read(ttl="0")
            if df is not None and not df.empty:
                df = df.dropna(how="all")
                # Vérifier et aligner les colonnes
                for col in COLUMNS:
                    if col not in df.columns:
                        df[col] = ""
                return df[COLUMNS], conn
        except Exception as e:
            st.caption(f"ℹ️ Connexion Google Sheets en attente ou vide : {e}")

    # Fallback vers fichier CSV local
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            df = df.dropna(how="all")
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNS], None
        except Exception:
            pass

    # Fallback vers session_state
    if "settings_history" in st.session_state and st.session_state.settings_history:
        df = pd.DataFrame(st.session_state.settings_history)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS], None

    # Par défaut, tableau vide
    return pd.DataFrame(columns=COLUMNS), None

def save_history(df, conn=None):
    df = df.dropna(how="all")
    # Mettre à jour la session state
    st.session_state.settings_history = df.to_dict("records")
    
    # Sauvegarder en CSV local
    df.to_csv(CSV_FILE, index=False)
    
    # Sauvegarder dans Google Sheets si disponible
    if conn is None:
        conn = get_gsheets_connection()
    if conn is not None:
        try:
            conn.update(data=df)
            return True
        except Exception as e:
            st.error(f"Erreur lors de la synchronisation Google Sheets : {e}")
            return False
    return True

# ---------------------------------------------------------
# INTERFACE PRINCIPALE
# ---------------------------------------------------------

st.markdown('<div class="main-header">🚵 Prototypes Manager VTT - Réglages & Serrages</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Plateforme technique de gestion des suspensions et couples de serrage VTT</div>', unsafe_allow_html=True)

# Barre latérale : Sélection du vélo et du poids
st.sidebar.header("⚙️ Configuration")
selected_bike_key = st.sidebar.selectbox(
    "Choisissez votre vélo :",
    options=list(BIKES_DATA.keys()),
    format_func=lambda x: BIKES_DATA[x]["name"]
)

bike_info = BIKES_DATA[selected_bike_key]

st.sidebar.info(f"**Modèle** : {bike_info['name']}\n\n**Type** : {bike_info['type']}")

user_weight = st.sidebar.number_input("Poids du pilote équipé (kg) :", min_value=40, max_value=130, value=85)

# Choix de la rubrique
nav_option = st.radio(
    "Sélectionnez la rubrique :",
    ["🔧 Réglages Suspensions", "📚 Historique des Réglages", "🔩 Couples de Serrage & Schémas"],
    horizontal=True
)

st.divider()

# Charger l'historique
df_history, gconn = load_history()

# ---------------------------------------------------------
# RUBRIQUE 1 : RÉGLAGES SUSPENSIONS & FORMULAIRE
# ---------------------------------------------------------
if nav_option == "🔧 Réglages Suspensions":
    st.subheader(f"📊 Réglages de suspension préconisés - {bike_info['name']} ({user_weight} kg)")
    
    recom = bike_info["suspensions_recommended"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🍴 Fourche Avant")
        fork = recom["fork"]
        st.write(f"**Modèle** : {fork['model']}")
        if "pressure" in fork:
            st.write(f"**Pression recommandée** : `{fork['pressure']}`")
        if "spring_rate" in fork:
            st.write(f"**Raideur de ressort (Coil)** : `{fork['spring_rate']}`")
        st.write(f"**SAG Cible** : {fork['sag']}")
        if "preload" in fork:
            st.write(f"**Précontrainte** : {fork['preload']}")
        st.write(f"**Rebond (LSR/HSR)** : {fork.get('lsr', 'N/A')}")
        st.write(f"**Compression (LSC/HSC)** : LSC `{fork.get('lsc', 'N/A')}` | HSC `{fork.get('hsc', 'N/A')}`")

    with col2:
        st.markdown("### 🛞 Amortisseur Arrière")
        shock = recom["shock"]
        st.write(f"**Modèle** : {shock['model']}")
        if "pressure" in shock:
            st.write(f"**Pression recommandée** : `{shock['pressure']}`")
        if "spring_rate" in shock:
            st.write(f"**Raideur de ressort (Coil)** : `{shock['spring_rate']}`")
        st.write(f"**SAG Cible** : {shock['sag']}")
        if "preload" in shock:
            st.write(f"**Précontrainte** : {shock['preload']}")
        st.write(f"**Rebond (LSR/HSR)** : {shock.get('lsr', 'N/A')}")
        st.write(f"**Compression (LSC/HSC)** : LSC `{shock.get('lsc', 'N/A')}` | HSC `{shock.get('hsc', 'N/A')}`")

    st.divider()
    
    # FORMULAIRE DE SAISIE DE NOUVEAUX RÉGLAGES
    st.subheader(f"📝 Saisir et ajouter un nouveau réglage terrain ({bike_info['name']})")
    st.write("Enregistrez vos ajustements personnalisés : la nouvelle donnée sera **ajoutée à la suite de votre historique** sans rien écraser.")
    
    with st.form("custom_settings_form"):
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            date_ride = st.date_input("Date de la sortie", datetime.today())
            terrain_type = st.selectbox("Type de terrain", ["Flow / Smooth", "Sol cassant / Racine", "Bike Park / Gros impacts", "Boue / Glissant"])
            weather_cond = st.selectbox("Conditions météo", ["Sec / Ensoleillé", "Humide / Pluie légère", "Très humide / Boue"])
            
        with f_col2:
            st.markdown("**Ajustements Fourche**")
            fork_press_user = st.text_input("Pression / Ressort fourche", value=fork.get('pressure', 'Coil'))
            fork_lsr_user = st.text_input("Rebond fourche (clics)", value=fork.get('lsr', '7 clics'))
            fork_comp_user = st.text_input("Compression LSC/HSC fourche", value="Milieu")
            
        with f_col3:
            st.markdown("**Ajustements Amortisseur**")
            shock_press_user = st.text_input("Pression / Ressort amortisseur", value=shock.get('pressure', 'Coil'))
            shock_lsr_user = st.text_input("Rebond amortisseur (clics)", value=shock.get('lsr', '8 clics'))
            shock_comp_user = st.text_input("Compression LSC/HSC amortisseur", value="Milieu")

        comments = st.text_area("Remarques / Sensation de pilotage :", placeholder="Ex: -5 psi en fourche pour gagner du grip sur le mouillé. Vélo très stable dans le rapide.")
        
        submit_button = st.form_submit_button("➕ Ajouter ce réglage à l'historique")
        
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
            new_df = pd.DataFrame([new_entry])
            updated_df = pd.concat([df_history, new_df], ignore_index=True)
            if save_history(updated_df, gconn):
                st.success(f"✅ Nouveau réglage ajouté avec succès pour le **{bike_info['name']}** !")
                st.rerun()

# ---------------------------------------------------------
# RUBRIQUE 2 : HISTORIQUE DES RÉGLAGES ET SUPPRESSION
# ---------------------------------------------------------
elif nav_option == "📚 Historique des Réglages":
    st.subheader("📚 Historique complet de vos réglages terrain")
    
    if df_history.empty:
        st.info("Aucun réglage enregistré pour l'instant. Rendez-vous dans l'onglet '🔧 Réglages Suspensions' pour ajouter votre premier réglage !")
    else:
        # Filtre par Vélo
        all_bikes = ["Tous les vélos"] + list(BIKES_DATA[k]["name"] for k in BIKES_DATA)
        # Trouver l'index par défaut pour le vélo actuellement sélectionné
        default_index = 0
        if bike_info["name"] in all_bikes:
            default_index = all_bikes.index(bike_info["name"])

        selected_filter_bike = st.selectbox("🔍 Filtrer l'historique par vélo :", all_bikes, index=default_index)

        if selected_filter_bike != "Tous les vélos":
            view_df = df_history[df_history["Vélo"] == selected_filter_bike]
        else:
            view_df = df_history

        st.dataframe(view_df, use_container_width=True, hide_index=True)

        # Bouton d'export CSV
        csv_data = view_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger cet historique (.csv)",
            data=csv_data,
            file_name=f"vtt_setups_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        st.divider()

        # SUPPRESSION D'UN RÉGLAGE
        st.subheader("🗑️ Supprimer un réglage de l'historique")
        st.write("Sélectionnez la ligne de réglage à supprimer de votre base de données :")

        options_to_delete = {}
        for idx, row in df_history.iterrows():
            label = f"Ligne #{idx+1} | {row['Date']} | {row['Vélo']} | {row['Terrain']} | {str(row['Commentaires'])[:30]}"
            options_to_delete[label] = idx

        selected_label = st.selectbox("Réglage à supprimer :", list(options_to_delete.keys()))

        if st.button("❌ Supprimer définitivement ce réglage"):
            idx_to_remove = options_to_delete[selected_label]
            updated_df = df_history.drop(index=idx_to_remove).reset_index(drop=True)
            if save_history(updated_df, gconn):
                st.success("✅ Le réglage a été supprimé avec succès de votre historique !")
                st.rerun()

# ---------------------------------------------------------
# RUBRIQUE 3 : COUPLES DE SERRAGE & SCHÉMAS
# ---------------------------------------------------------
else:
    st.subheader(f"🔩 Fiche technique & Couples de serrage - {bike_info['name']}")
    
    st.info(f"ℹ️ **Documentation Schémas** : {bike_info['schematic_info']}")
    
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
            "component": "Composant / Axe (Réf#)",
            "torque": "Couple préconisé (Nm)",
            "notes": "Recommandations (Frein filet / Graisse)"
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("""
    ---
    ### 💡 Rappels de montage & Sécurité :
    * **Patte de dérailleur SRAM UDH** : Attention, la vis de blocage UDH possède un **filetage inversé** (serrage dans le sens anti-horaire) à **25 Nm**.
    * **Frein filet** : Utilisez du frein filet moyen (ex: Loctite 242/243) sur les filetages indiqués.
    * **Graissage des axes** : Appliquez une fine couche de graisse uniquement sur le corps/fût de l'axe, jamais sur les filetages destinés au frein filet.
    * **Étriers de frein Post Mount** : Serrage préconisé à **9.5 Nm**. Centrer l'étrier en maintenant le levier enfoncé.
    * **Disques 6 trous (SRAM HS2 / Hope)** : Serrage à **6.2 Nm** en étoile croisée avec clé Torx T25.
    """)

# Footer
st.divider()
st.caption("Gemini Notebook Studio - Application de gestion VTT & Réglages Atelier grounded from source materials.")
