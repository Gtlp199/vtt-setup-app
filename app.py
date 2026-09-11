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

# ---------------------------------------------------------
# DONNÉES EXHAUSTIVES ET GROUNDÉES DES VÉLOS
# ---------------------------------------------------------

BIKES_DATA = {
    "transition_patrol_2024": {
        "name": "Transition Patrol Carbone (2024/2025)",
        "type": "Enduro Musculaire (Mullet)",
        "weight_ref": "85 kg",
        "images": ["2023.02.21_PatrolASM_Explode.jpg", "images/2023.02.21_PatrolASM_Explode.jpg", "Patrol_Torque.jpg"],
        "suspensions_recommended": {
            "fork": {
                "model": "Öhlins RXF 38 m.2 Kit Coil (160mm)",
                "pressure": "N/A (Ressort Hélicoïdal)",
                "spring_rate": "9.7 N/mm (Blanc / ~82kg) à 10.6 N/mm (Noir / ~91kg)",
                "sag": "15% - 20% (24 - 32 mm)",
                "preload": "0 - 2 tours max depuis contact",
                "lsr": "Selon sensation (compter clics depuis ouvert)",
                "lsc": "Ajustement progressif au sommet",
                "hsc": "4 positions (1-3 descente, 0 blocage)"
            },
            "shock": {
                "model": "Öhlins TTX 22 Coil (205x65mm)",
                "pressure": "N/A (Ressort Hélicoïdal)",
                "spring_rate": "457 lbs",
                "sag": "25% - 35% (16.25 - 22.75 mm)",
                "preload": "2 tours complets maximum après contact",
                "lsr": "Compter clics depuis fermeture complète (Pos 0)",
                "lsc": "Molette bleue (Ajuster selon motricité)",
                "hsc": "3 positions (I: Souple, II: Polyvalent, III: Pédalage)"
            }
        },
        "torques": [
            {"zone": "Cadre & Cinématique", "component": "Réf #5 / #8 - Main Pivot Axle 17x80mm", "torque": "19 Nm", "notes": "Graisse sur corps / Loctite 243 sur filet"},
            {"zone": "Cadre & Cinématique", "component": "Réf #9 - Main Pivot Taper Nut", "torque": "Serrage guidé", "notes": "Graisser la surface extérieure"},
            {"zone": "Cadre & Cinématique", "component": "Réf #11 - Main Pivot Screw (M6-25L)", "torque": "10 Nm", "notes": "Loctite 243 (Bleu)"},
            {"zone": "Cadre & Cinématique", "component": "Réf #15 - Chainstay Pivot Axle 15x26mm V2", "torque": "Axe guidé", "notes": "Graisser le corps de l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Réf #16 - Chainstay Pivot Screw 12x15mm V2 (Horst Link)", "torque": "12 Nm", "notes": "Loctite 243 (Bleu)"},
            {"zone": "Cadre & Cinématique", "component": "Réf #17 - Seatstay Pivot Axle 15x20mm", "torque": "Axe guidé", "notes": "Graisser le corps de l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Réf #18 - Seatstay Pivot Screw 12x12mm", "torque": "12 Nm", "notes": "Loctite 243 (Bleu)"},
            {"zone": "Cadre & Cinématique", "component": "Réf #21 - Rocker Pivot Screw 8x40mm", "torque": "Serrage guidé", "notes": "Loctite 243 (Bleu)"},
            {"zone": "Cadre & Cinématique", "component": "Réf #22 - Rocker Pivot Axle 15x38mm", "torque": "15 Nm", "notes": "Graisser le corps de l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Réf #25 - Trunnion Shock Bolt V2 10x24mm (Ancrage Haut)", "torque": "12 Nm", "notes": "Loctite 243 (Bleu)"},
            {"zone": "Cadre & Cinématique", "component": "Réf #29 - Shock Bolt 8x55mm (Ancrage Bas)", "torque": "10 Nm", "notes": "Graisse axe / Loctite 243 filet"},
            {"zone": "Cadre & Cinématique", "component": "Réf #33 - 12x148 Rear Thru-Axle (Axe de roue arrière UDH)", "torque": "10 - 12 Nm", "notes": "Graisser le filetage et l'axe"},
            {"zone": "Transmission", "component": "Réf #35 - Universal Derailleur Hanger (SRAM UDH Bolt)", "torque": "25 Nm", "notes": "Attention: Filetage inversé / Pas à gauche"},
            {"zone": "Freins", "component": "Disques SRAM HS2 (Moyeux Hope Pro 5)", "torque": "6.2 Nm", "notes": "Torx T25 / Serrage croisé en étoile"},
            {"zone": "Freins", "component": "Étriers SRAM Maven (Post Mount)", "torque": "9.5 Nm", "notes": "Centrer l'étrier levier enfoncé"},
            {"zone": "Freins", "component": "Écrou de compression durite Stealth-a-majig", "torque": "8 Nm", "notes": "Clé dynamométrique à fourche 8mm"}
        ],
        "schematic_info": "Vue éclatée complète issue de '2023.02.21_PatrolASM_Explode.jpg' et 'Transition Patrol Couples de serrage - Feuille 2'."
    },
    "pivot_ampd_2026": {
        "name": "Pivot Shuttle AMP'd (2026)",
        "type": "E-VTTAE All-Mountain / Enduro",
        "weight_ref": "85 kg",
        "images": ["Ampd_Torque.jpg", "images/Ampd_Torque.jpg", "Suspension Calculator Pivot AMPD.jpg", "images/Suspension Calculator Pivot AMPD.jpg"],
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
            {"zone": "Cadre & Cinématique", "component": "Réf #5 - Universal Rear Derailleur Hanger Bolt (UDH)", "torque": "25 Nm", "notes": "Pas à droite / UDH Bolt"},
            {"zone": "Cadre & Cinématique", "component": "Réf #12 - M8 Front Shock Bolt (Spacing 30.1mm)", "torque": "13 Nm", "notes": "Graisse axe / Loctite 243 filet"},
            {"zone": "Cadre & Cinématique", "component": "Réf #13 - M14x20 Link Bolt (Main Link)", "torque": "35 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Réf #14 - M10 Trunnion Mount Bolt", "torque": "13 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Réf #15 - M14x20 Flip Chip Bolt", "torque": "35 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "157mm UDH Rear Axle (Axe de roue arrière)", "torque": "15 Nm", "notes": "Graisser le filetage"},
            {"zone": "Moteur & Batterie", "component": "Avinox Label I - 800Wh Battery Mounting Hardware", "torque": "5 Nm", "notes": "Loctite 243"},
            {"zone": "Moteur & Batterie", "component": "Avinox Label J - Avinox M2S Drive Unit Mounting Bolts", "torque": "25 Nm", "notes": "Loctite 243 / Rondelles dentelées"},
            {"zone": "Moteur & Batterie", "component": "Avinox Label K - Chainring Spider Lockring", "torque": "35 Nm", "notes": "Graisser"},
            {"zone": "Composants", "component": "Réf #23 - M6x12 Skid Plate Mounting Screws (Sabot)", "torque": "6 Nm", "notes": "Loctite 243"},
            {"zone": "Composants", "component": "Réf #25 - M5x12 Button Head Screw", "torque": "5 Nm", "notes": "Loctite 243"},
            {"zone": "Composants", "component": "Réf #30 - M2.5x10 Flat Head Bolt Black", "torque": "1 Nm", "notes": "Serrage délicat"},
            {"zone": "Composants", "component": "Réf #35 - M5x12 Flat Head Chain Guide Mounting Screw", "torque": "5 Nm", "notes": "Loctite 243"},
            {"zone": "Composants", "component": "Réf #37 - Internal Routing Plate Bolt M10x8.5", "torque": "2 Nm", "notes": "Graisser"},
            {"zone": "Composants", "component": "Collier de selle (Seatpost Clamp Bolt)", "torque": "5 Nm", "notes": "Clé Allen 4mm"},
            {"zone": "Composants", "component": "Vis de carte SIM / Écran Control Display", "torque": "< 0.1 Nm / < 0.6 Nm", "notes": "Vis M2 / M2.5"}
        ],
        "schematic_info": "Vue éclatée issue de 'Shuttle-AMPD-SPS-Avinox-Parts-1.pdf' et manuel d'atelier '8.26-Shuttle-AMPD-Product-Manual'."
    },
    "santacruz_vala_2026": {
        "name": "Santa Cruz Vala GX AXS (2026)",
        "type": "E-VTTAE All-Mountain (Bosch Gen 5)",
        "weight_ref": "55-85 kg",
        "images": ["01_Carbon_Linkage_Hardware.jpg", "02_Carbon_Rear_Triangle_Hardware.jpg", "03_Carbon_Controller_Motor_Guards.png", "04_Carbon_Battery.png", "images/01_Carbon_Linkage_Hardware.jpg"],
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
            {"zone": "Linkage (Biellette)", "component": "Label C - Pivot Axle M15x91", "torque": "20 Nm", "notes": "Loctite 242 sur filet / Graisse sur axe"},
            {"zone": "Linkage (Biellette)", "component": "Label N - Bosch DU screw wide V2 (EB11.200.15J)", "torque": "30 Nm", "notes": "Vis Moteur Bosch"},
            {"zone": "Linkage (Biellette)", "component": "Label O - Bosch DU screw V2 (EB11.200.12G)", "torque": "30 Nm", "notes": "Vis Moteur Bosch"},
            {"zone": "Linkage (Biellette)", "component": "Label T - M10x10 Trunnion Screw", "torque": "16 Nm", "notes": "Loctite 242 sur filet / Graisse sur axe"},
            {"zone": "Linkage (Biellette)", "component": "Label W - M10x20 Bolt", "torque": "16 Nm", "notes": "Loctite 242"},
            {"zone": "Linkage (Biellette)", "component": "Label H - M8x45 Lowhead SHCS (Ancrage Bas / Flip-Chip)", "torque": "15.6 Nm", "notes": "Loctite 242"},
            {"zone": "Linkage (Biellette)", "component": "Label F - M6x20 SHCS (Pivot Horst Link / Bases)", "torque": "9 Nm", "notes": "Loctite 242"},
            {"zone": "Linkage (Biellette)", "component": "Label R - M4x12 BHCS", "torque": "0.65 Nm", "notes": "Graisser le filetage"},
            {"zone": "Linkage (Biellette)", "component": "Label A - M5x5 Set Screw", "torque": "0.5 Nm", "notes": "Loctite 242 à effleurement"},
            {"zone": "Linkage (Biellette)", "component": "Label BB - M3x12 BHCS", "torque": "0.1 Nm", "notes": "Loctite 242"},
            {"zone": "Triangle Arrière", "component": "Label C - SCB UDH Screw (Vis de patte SRAM UDH)", "torque": "20 Nm", "notes": "Attention: Pas à gauche (Reverse Thread)"},
            {"zone": "Triangle Arrière", "component": "Label D - M10x26 Bolt", "torque": "16 Nm", "notes": "Loctite 242 sur filet / Graisse sur axe"},
            {"zone": "Triangle Arrière", "component": "Label P - M5x12 HHS", "torque": "2 Nm", "notes": "Loctite 242"},
            {"zone": "Triangle Arrière", "component": "Label K - M4x10 FHCS", "torque": "0.65 Nm", "notes": "Loctite 242"},
            {"zone": "Triangle Arrière", "component": "Label O - M3x6 Screw", "torque": "0.6 Nm", "notes": "Loctite 242"},
            {"zone": "Triangle Arrière", "component": "Label J - M3x12 BHCS", "torque": "0.1 Nm", "notes": "Loctite 242"},
            {"zone": "Moteur & Carter", "component": "Label B - M5x10 BHCS (Fixations carter)", "torque": "9 Nm", "notes": "Loctite 242"},
            {"zone": "Moteur & Carter", "component": "Label G - M6x10 BHCS", "torque": "3 Nm", "notes": "Loctite"},
            {"zone": "Moteur & Carter", "component": "Label E - M4x16 BHCS", "torque": "0.65 Nm", "notes": "Graisser le filetage"},
            {"zone": "Batterie", "component": "Label B - M4x10 SHCS (Fixation Batterie PT600)", "torque": "1.2 Nm", "notes": "Loctite 242"},
            {"zone": "Composants", "component": "Collier de selle (36.4mm Seat Collar)", "torque": "5 Nm", "notes": "Serrage cintre/potence 5 Nm"},
            {"zone": "Freins", "component": "Étriers de Frein Post Mount / Disques 6 trous", "torque": "9 - 10 Nm / 6 Nm", "notes": "Torx T25 disques"}
        ],
        "schematic_info": "Vues éclatées et fiches matériels officielles 'Santa Cruz Vala 2026 - Couples de Serrage et Vues Eclatees'."
    },
    "norco_sight_2024": {
        "name": "Norco Sight Carbon Gen 5 (2024)",
        "type": "All-Mountain / Enduro",
        "weight_ref": "Standard",
        "images": ["Norco_Torque.jpg", "images/Norco_Torque.jpg", "norco_sight_exploded.jpg"],
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
            {"zone": "Cadre & Cinématique", "component": "Réf #15 - Main Pivot Shaft OD15 L92 (Axe Pivot Principal)", "torque": "21 Nm", "notes": "Graisser le corps de l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Réf #25 - Main Pivot Shaft Retainer (LSM/Shock Bolt 56mm M8)", "torque": "3 Nm", "notes": "Retient l'axe principal"},
            {"zone": "Cadre & Cinématique", "component": "Réf #17 - Chain Stay to Seat Stays Shaft Dia12 L32 M12x1.25", "torque": "14 Nm", "notes": "Graisser / Placer réf #29 entre roulements"},
            {"zone": "Cadre & Cinématique", "component": "Réf #18 - Linkarm to Seat Stays Shaft Dia12 L27.5 M12x1.25", "torque": "14 Nm", "notes": "Graisser le corps de l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Réf #19 - Linkarm to Front Triangle Bolt OD15 L32 M12x1.25", "torque": "16 Nm", "notes": "Graisser le corps de l'axe"},
            {"zone": "Cadre & Cinématique", "component": "Réf #20 - Trunnion Shock Mounts Bolt M10x1 L17", "torque": "14 Nm", "notes": "Graisser le corps de la vis"},
            {"zone": "Cadre & Cinématique", "component": "Réf #21 - Main Pivot Nut Bolt M10x1.25 L14", "torque": "19 Nm", "notes": "Écrou de pivot principal"},
            {"zone": "Cadre & Cinématique", "component": "Réf #22 - LSM Bolt 60mm M6", "torque": "12 Nm", "notes": "Loctite 243"},
            {"zone": "Cadre & Cinématique", "component": "Réf #23 - Shock Bolt 56mm M8", "torque": "12 Nm", "notes": "Ancrage d'amortisseur"},
            {"zone": "Cadre & Cinématique", "component": "Réf #26 - Idler to Chain Stay (Galet de chaîne)", "torque": "16 Nm", "notes": "Graisser le corps"},
            {"zone": "Transmission", "component": "Réf #38/#39 - UDH Derailleur Hanger Bolt V2 M12x1.75", "torque": "20 Nm", "notes": "Attention: Pas à gauche (Left Hand Thread)"},
            {"zone": "Cadre & Cinématique", "component": "Réf #40 - Norco Rear Axle L174 TL13 M12x1 (Axe arrière)", "torque": "10 Nm", "notes": "Graisser le filetage"},
            {"zone": "Composants", "component": "Réf #41 - Seat Clamp Norco Post 34.9", "torque": "5 Nm", "notes": "Collier de selle"}
        ],
        "schematic_info": "Nomenclature et schémas d'assemblage complets 'norco-sight-carbon-gen5-assembler-document-revb'."
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
    
    # AFFICHAGE DU SCHÉMA / IMAGE SI PRÉSENT
    st.markdown("### 🖼️ Schémas & Vues Éclatées du Cadre")
    
    found_image = False
    for img_name in bike_info.get("images", []):
        if os.path.exists(img_name):
            try:
                st.image(img_name, caption=f"Schéma technique : {os.path.basename(img_name)}", use_container_width=True)
                found_image = True
            except Exception as e:
                pass
                
    if not found_image:
        st.warning("💡 *Conseil visuel* : Placez vos images JPG/PNG (ex: Ampd_Torque.jpg, Patrol_Torque.jpg, Norco_Torque.jpg) dans votre dépôt GitHub pour qu'elles s'affichent automatiquement ci-dessus.")

    st.divider()

    st.markdown("### 📋 Tableau complet des couples de serrage (Nm)")
    
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
            "zone": "Zone / Section",
            "component": "Composant / Axe (Réf# / Label)",
            "torque": "Couple préconisé (Nm)",
            "notes": "Consignes (Frein filet / Graisse)"
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("""
    ---
    ### 💡 Rappels de montage & Sécurité :
    * **Patte de dérailleur SRAM UDH** : Attention, la vis de blocage UDH possède un **filetage inversé** (serrage dans le sens anti-horaire) à **20-25 Nm**.
    * **Frein filet** : Utilisez du frein filet moyen (ex: Loctite 242/243) sur les filetages indiqués.
    * **Graissage des axes** : Appliquez une fine couche de graisse uniquement sur le corps/fût de l'axe, jamais sur les filetages destinés au frein filet.
    * **Étriers de frein Post Mount** : Serrage préconisé à **9.5 Nm**. Centrer l'étrier en maintenant le levier enfoncé.
    * **Disques 6 trous (SRAM HS2 / Hope)** : Serrage à **6.2 Nm** en étoile croisée avec clé Torx T25.
    """)

# Footer
st.divider()
st.caption("Gemini Notebook Studio - Application de gestion VTT & Réglages Atelier grounded from source materials.")
