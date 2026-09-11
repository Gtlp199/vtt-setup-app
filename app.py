import streamlit as st
import pandas as pd
import json
import os
import re
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
# FONCTIONS GOOGLE SHEETS / DATA PERSISTENCE
# ---------------------------------------------------------

def load_data_from_gsheets():
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        return conn, df
    except Exception as e:
        return None, None

def save_data_to_gsheets(conn, existing_df, new_entry):
    try:
        new_df = pd.DataFrame([new_entry])
        if existing_df is not None and not existing_df.empty:
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            updated_df = new_df
        conn.update(data=updated_df)
        return updated_df, True
    except Exception as e:
        return existing_df, False

def delete_row_from_gsheets(conn, existing_df, index_to_delete):
    try:
        updated_df = existing_df.drop(index=index_to_delete).reset_index(drop=True)
        conn.update(data=updated_df)
        return updated_df, True
    except Exception as e:
        return existing_df, False

# Helper pour affichage d'image sécurisé (compatibilité Streamlit)
def display_image_safely(image_path, caption=""):
    try:
        st.image(image_path, caption=caption, use_container_width=True)
    except TypeError:
        try:
            st.image(image_path, caption=caption, use_column_width=True)
        except Exception:
            st.image(image_path, caption=caption)
    except Exception as e:
        st.warning(f"Impossible d'afficher l'image {caption} : {e}")

# Helper pour rechercher dynamiquement les images d'un vélo
def get_bike_images(bike_key):
    search_dirs = [".", "images", "img", "assets", "schematics"]
    all_files = []
    for d in search_dirs:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        all_files.append(os.path.join(root, f))
    
    bike_files = []
    if bike_key == "pivot_ampd_2026":
        keywords = ["ampd", "shuttle", "pivot"]
    elif bike_key == "transition_patrol_2024":
        keywords = ["patrol", "transition", "explode"]
    elif bike_key == "santacruz_vala_2026":
        keywords = ["vala", "santacruz", "01_carbon", "02_carbon", "03_carbon", "04_carbon", "linkage", "rear_triangle", "controller", "battery"]
    elif bike_key == "norco_sight_2024":
        keywords = ["norco", "sight"]
    else:
        keywords = []

    for path in sorted(all_files):
        filename = os.path.basename(path).lower()
        if any(kw in filename for kw in keywords):
            bike_files.append(path)
            
    return bike_files

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
            {"zone": "Composants", "component": "Vis Anti-dérailleur M5x12 [Réf #35]", "torque": "5 Nm", "notes": "Loctite 243"},
            {"zone": "Composants", "component": "Collier de selle [Seatpost Clamp]", "torque": "5 Nm", "notes": "Clé Allen 4mm"},
            {"zone": "Composants", "component": "Vis Capot SIM / Écran Display [Réf #30]", "torque": "0.1 - 0.6 Nm", "notes": "Ne pas trop serrer"}
        ],
        "schematic_info": "Vue éclatée disponible dans '8.26-Shuttle-AMPD-Product-Manual-All-Languages.pdf' et image 'Ampd_Torque.jpg'."
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
            {"zone": "Cadre & Cinématique", "component": "Axe de roue arrière 12x148 UDH [Réf #33]", "torque": "10 - 12 Nm", "notes": "Graisser axe et filetages"},
            {"zone": "Cadre & Cinématique", "component": "Axe Main Pivot 17x80mm [Réf #8]", "torque": "19 Nm", "notes": "Graisse sur axe / Loctite bleu sur filets"},
            {"zone": "Cadre & Cinématique", "component": "Main Pivot Screw M6-25L [Réf #11]", "torque": "10 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Chainstay Pivot Screw 12x15mm [Réf #16]", "torque": "12 Nm", "notes": "Loctite 243 / Vis large carbone"},
            {"zone": "Cadre & Cinématique", "component": "Seatstay Pivot Screw 12x12mm [Réf #18]", "torque": "12 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Rocker Pivot Axle 15x38mm [Réf #22]", "torque": "15 Nm", "notes": "Graisser le fût de l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Trunnion Shock Bolt V2 M10x24 [Réf #25]", "torque": "12 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Shock Bolt M8x55mm [Réf #29]", "torque": "10 Nm", "notes": "Graisse axe / Loctite filets"},
            {"zone": "Transmission & Moteur", "component": "Vis de la patte SRAM UDH [Réf #35]", "torque": "25 Nm", "notes": "Attention: Filetage inversé (anti-horaire)"},
            {"zone": "Freins", "component": "Disques SRAM HS2 (Moyeux Hope Pro 5)", "torque": "6.2 Nm", "notes": "Torx T25 / Serrage en étoile"},
            {"zone": "Freins", "component": "Étriers SRAM Maven (Fixation Post Mount)", "torque": "9.5 Nm", "notes": "Centrer l'étrier levier serré"}
        ],
        "schematic_info": "Vue éclatée disponible dans '2023.02.21_PatrolASM_Explode.jpg' et 'Transition Patrol Couples de serrage - Feuille 2'."
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
            {"zone": "Cadre & Cinématique", "component": "Pivot Axle M15x91 [Linkage Label C]", "torque": "20 Nm", "notes": "Loctite 242 sur filet / Graisser l'axe"},
            {"zone": "Cadre & Cinématique", "component": "M10x10 Trunnion Screw [Linkage Label T]", "torque": "16 Nm", "notes": "Loctite 242"},
            {"zone": "Cadre & Cinématique", "component": "M10x20 Bolt [Linkage Label W]", "torque": "16 Nm", "notes": "Loctite 242"},
            {"zone": "Cadre & Cinématique", "component": "M8x45 Lowhead SHCS [Linkage Label H]", "torque": "15.6 Nm", "notes": "Loctite 242"},
            {"zone": "Cadre & Cinématique", "component": "M6x20 SHCS [Linkage Label F]", "torque": "9 Nm", "notes": "Loctite 242"},
            {"zone": "Cadre & Cinématique", "component": "M10x26 Bolt [Rear Triangle Label D]", "torque": "16 Nm", "notes": "Loctite 242 sur filet / Graisse axe"},
            {"zone": "Transmission & Moteur", "component": "Bosch DU Screw Wide V2 [Label N, O]", "torque": "30 Nm", "notes": "Réf Bosch EB11.200.15J"},
            {"zone": "Transmission & Moteur", "component": "SCB UDH Screw [Rear Triangle Label C]", "torque": "20 Nm", "notes": "Pas à gauche (Reverse thread)"},
            {"zone": "Composants", "component": "M5x10 BHCS Motor/Controller [Label B]", "torque": "9 Nm", "notes": "Loctite 242"},
            {"zone": "Composants", "component": "M4x10 Battery Screw [Battery Label B]", "torque": "1.2 Nm", "notes": "Loctite 242"},
            {"zone": "Composants", "component": "Vis de Disque 6 Trous", "torque": "6 Nm", "notes": "Torx T25"},
            {"zone": "Composants", "component": "Étriers de Frein Post Mount", "torque": "9 - 10 Nm", "notes": "Alignement étrier"}
        ],
        "schematic_info": "Vues éclatées disponibles dans les fiches 'Santa Cruz Vala 2026 - Couples de Serrage et Vues Eclatees'."
    },
    "norco_sight_2024": {
        "name": "Norco Sight Carbon Gen 5 (2024)",
        "type": "All-Mountain / Enduro",
        "weight_ref": "Standard",
        "suspensions_recommended": {
            "fork": {
                "model": "Öhlins RXF 38 m.2 Air (170mm)",
                "pressure": "Main: 100-110 psi | Ramp Up: 190-200 psi",
                "sag": "10% - 15% (17 - 25.5 mm)",
                "lsr": "10 - 11 clics depuis ouvert",
                "lsc": "Ajustement au sommet",
                "hsc": "3 positions descente + 1 blocage"
            },
            "shock": {
                "model": "Öhlins TTX Air 2 (205x60mm)",
                "pressure": "~170 - 190 psi (pour ~85kg)",
                "sag": "25% - 35% (cible: 30% / 18 mm)",
                "lsr": "Compter clics depuis fermé (Pos 0)",
                "lsc": "Molette bleue",
                "hsc": "Position 1 (Soft), 2 (Medium), P (Pedal)"
            }
        },
        "torques": [
            {"zone": "Cadre & Cinématique", "component": "Main Pivot Shaft Dia15 [Réf #15]", "torque": "21 Nm", "notes": "Graisser l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Linkarm to Front Triangle (Trunnion) [Réf #20]", "torque": "16 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Linkarm to Seat Stays [Réf #18]", "torque": "14 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Chain Stay to Seat Stays [Réf #17]", "torque": "14 Nm", "notes": "Loctite 243"},
            {"zone": "Transmission & Moteur", "component": "UDH Derailleur Hanger Bolt [Réf #39]", "torque": "20 Nm", "notes": "Pas à gauche (Left hand thread)"},
            {"zone": "Cadre & Cinématique", "component": "Axe de roue arrière 12x148mm [Réf #40]", "torque": "10 Nm", "notes": "Graisser le filetage"}
        ],
        "schematic_info": "Vues éclatées disponibles dans 'Norco_Sight_view_1.jpg' à 'Norco_Sight_view5.jpg'."
    }
}

# Initialisation des données Google Sheets
gsheets_conn, df_gsheets = load_data_from_gsheets()

if "settings_history" not in st.session_state:
    if df_gsheets is not None and not df_gsheets.empty:
        st.session_state.settings_history = df_gsheets.to_dict(orient="records")
    else:
        st.session_state.settings_history = []

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

# ---------------------------------------------------------
# RUBRIQUE 1 : RÉGLAGES SUSPENSIONS
# ---------------------------------------------------------
if nav_option == "🔧 Réglages Suspensions":
    st.subheader(f"📊 Réglages de suspension préconisés pour {bike_info['name']} ({user_weight} kg)")
    
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
    st.subheader("📝 Saisie de vos nouveaux réglages du jour")
    st.write("Enregistrez vos ajustements personnalisés. La donnée sera ajoutée à votre historique sans écraser les précédentes.")
    
    with st.form("custom_settings_form"):
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            date_ride = st.date_input("Date de la sortie", datetime.today())
            terrain_type = st.selectbox("Type de terrain", ["Flow / Smooth", "Sol cassant / Racine", "Bike Park / Gros impacts", "Boue / Glissant"])
            weather_cond = st.selectbox("Conditions météo", ["Sec / Ensoleillé", "Humide / Pluie légère", "Très humide / Boue"])
            
        with f_col2:
            st.markdown("**Ajustements Fourche**")
            fork_press_user = st.text_input("Pression / Ressort fourche", value=fork.get('pressure', 'Coil'))
            fork_lsr_user = st.text_input("Rebond fourche (clics)", value="7 clics")
            fork_comp_user = st.text_input("Compression LSC/HSC fourche", value="Milieu")
            
        with f_col3:
            st.markdown("**Ajustements Amortisseur**")
            shock_press_user = st.text_input("Pression / Ressort amortisseur", value=shock.get('pressure', 'Coil'))
            shock_lsr_user = st.text_input("Rebond amortisseur (clics)", value="8 clics")
            shock_comp_user = st.text_input("Compression LSC/HSC amortisseur", value="Milieu")

        comments = st.text_area("Remarques / Sensation de pilotage :", placeholder="Ex: -5 psi en fourche pour gagner du grip sur le mouillé. Vélo très stable dans le rapide.")
        
        submit_button = st.form_submit_button("💾 Enregistrer ce réglage dans l'historique")
        
        if submit_button:
            entry = {
                "Date": str(date_ride),
                "Vélo": bike_info["name"],
                "Poids_Pilote_kg": user_weight,
                "Terrain": terrain_type,
                "Météo": weather_cond,
                "Fourche_Réglage": f"{fork_press_user} | Rebond: {fork_lsr_user} | Comp: {fork_comp_user}",
                "Amortisseur_Réglage": f"{shock_press_user} | Rebond: {shock_lsr_user} | Comp: {shock_comp_user}",
                "Commentaires": comments
            }
            st.session_state.settings_history.append(entry)
            
            if gsheets_conn is not None:
                updated_df, success = save_data_to_gsheets(gsheets_conn, pd.DataFrame(st.session_state.settings_history[:-1]), entry)
                if success:
                    st.success("✅ Votre nouveau réglage a été synchronisé avec succès sur Google Sheets !")
                else:
                    st.warning("⚠️ Réglage sauvegardé localement (Échec de synchronisation Google Sheets).")
            else:
                st.success("✅ Votre réglage a été sauvegardé localement pour la session !")

# ---------------------------------------------------------
# RUBRIQUE 2 : HISTORIQUE DES RÉGLAGES
# ---------------------------------------------------------
elif nav_option == "📚 Historique des Réglages":
    st.subheader("📚 Historique de vos essais et réglages enregistrés")
    
    if not st.session_state.settings_history:
        st.info("Aucun réglage n'a encore été enregistré dans l'historique.")
    else:
        df_history = pd.DataFrame(st.session_state.settings_history)
        
        # Filtre par vélo
        all_bikes = ["Tous les vélos"] + list(df_history["Vélo"].unique())
        default_idx = all_bikes.index(bike_info["name"]) if bike_info["name"] in all_bikes else 0
        selected_filter_bike = st.selectbox("Filtrer l'historique par vélo :", all_bikes, index=default_idx)
        
        if selected_filter_bike != "Tous les vélos":
            filtered_history = df_history[df_history["Vélo"] == selected_filter_bike]
        else:
            filtered_history = df_history
            
        st.dataframe(filtered_history, use_container_width=True)
        
        # Export CSV
        csv = filtered_history.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger cet historique (.csv)",
            data=csv,
            file_name=f"vtt_setups_{selected_filter_bike.replace(' ', '_')}.csv",
            mime="text/csv"
        )
        
        st.divider()
        
        # SUPPRESSION D'UNE LIGNE
        st.markdown("### 🗑️ Supprimer un réglage de l'historique")
        delete_options = []
        for idx, row in filtered_history.iterrows():
            delete_options.append(f"Ligne {idx+1} | {row['Date']} - {row['Vélo']} ({row['Terrain']} / {row['Météo']}) - {str(row['Commentaires'])[:30]}...")
            
        if delete_options:
            selected_to_delete = st.selectbox("Choisissez la ligne à supprimer :", delete_options)
            if st.button("❌ Supprimer définitivement ce réglage"):
                selected_idx = int(selected_to_delete.split("|")[0].replace("Ligne", "").strip()) - 1
                
                del st.session_state.settings_history[selected_idx]
                
                if gsheets_conn is not None:
                    updated_df, success = delete_row_from_gsheets(gsheets_conn, df_history, selected_idx)
                    if success:
                        st.success("✅ La ligne a été supprimée de Google Sheets !")
                    else:
                        st.warning("⚠️ Suppression locale effectuée (Échec Google Sheets).")
                else:
                    st.success("✅ La ligne a été supprimée de la mémoire locale.")
                st.rerun()

# ---------------------------------------------------------
# RUBRIQUE 3 : COUPLES DE SERRAGE & SCHÉMAS
# ---------------------------------------------------------
else:
    st.subheader(f"🔩 Fiche technique & Couples de serrage - {bike_info['name']}")
    
    st.info(f"ℹ️ **Documentation Schémas** : {bike_info['schematic_info']}")
    
    # RECHERCHE ET AFFICHAGE DES SCHÉMAS
    bike_imgs = get_bike_images(selected_bike_key)
    
    if bike_imgs:
        st.markdown("### 🖼️ Schémas & Vues Éclatées du Cadre")
        if len(bike_imgs) == 1:
            display_image_safely(bike_imgs[0], caption=f"Schéma technique : {os.path.basename(bike_imgs[0])}")
        else:
            # Affichage avec des onglets pour chaque vue
            tab_titles = [f"Vue {i+1} : {os.path.basename(path)}" for i, path in enumerate(bike_imgs)]
            tabs = st.tabs(tab_titles)
            for idx, tab in enumerate(tabs):
                with tab:
                    display_image_safely(bike_imgs[idx], caption=os.path.basename(bike_imgs[idx]))
            
            # Option pour défiler toutes les vues à la suite
            with st.expander("🔍 Afficher toutes les vues en défilement continu"):
                for path in bike_imgs:
                    st.markdown(f"**{os.path.basename(path)}**")
                    display_image_safely(path, caption=os.path.basename(path))
                    st.divider()
    else:
        st.info("💡 **Astuce Schémas** : Ajoutez les fichiers images `.jpg` / `.png` dans votre dépôt GitHub (ex: dossier `/images/` ou à la racine) pour afficher automatiquement la vue éclatée de ce vélo.")
        uploaded_file = st.file_uploader(f"Chargez un schéma visuel pour {bike_info['name']}", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            display_image_safely(uploaded_file, caption=f"Schéma importé : {uploaded_file.name}")

    st.divider()
    
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
    * **Patte de dérailleur SRAM UDH** : Attention, la vis de blocage UDH possède un **filetage inversé** (serrage dans le sens anti-horaire) à **25 Nm** / **20 Nm**.
    * **Frein filet** : Utilisez du frein filet moyen (ex: Loctite 242/243) sur les filetages indiqués.
    * **Graissage des axes** : Appliquez une fine couche de graisse uniquement sur le corps/fût de l'axe, jamais sur les filetages destinés au frein filet.
    * **Étriers de frein Post Mount** : Serrage préconisé à **9.5 Nm**. Centrer l'étrier en maintenant le levier enfoncé.
    * **Disques 6 trous (SRAM HS2 / Hope)** : Serrage à **6.2 Nm** en étoile croisée avec clé Torx T25.
    """)

# Footer
st.divider()
st.caption("Gemini Notebook Studio - Application de gestion VTT & Réglages Atelier grounded from source materials.")
