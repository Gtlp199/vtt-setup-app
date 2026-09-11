import streamlit as st
import pandas as pd
import json
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
    .schematic-box {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1.5rem;
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
        "schematic_guide": {
            "source_doc": "Manuel Pivot Shuttle AMP'd - Section 5 (Small Parts & Avinox System)",
            "repere_map": [
                {"zone": "Triangle Avant & Amortisseur", "details": "Vis avant d'amortisseur (#12 - 13 Nm), Ancrage Trunnion (#14 - 13 Nm), Fixation Batterie (#I - 5 Nm)"},
                {"zone": "Biellette & Cinématique", "details": "Axe de biellette principale (#13 - 35 Nm), Flip Chip (#15 - 35 Nm)"},
                {"zone": "Moteur Avinox & Pédalier", "details": "Vis de bloc moteur (#J - 25 Nm), Ecrou Spider Plateau (#K - 35 Nm), Sabot Moteur (#23 - 6 Nm)"},
                {"zone": "Triangle Arrière & Roue", "details": "Vis de patte UDH (#5 - 25 Nm), Axe traversant 157mm (#157mm - 15 Nm)"}
            ]
        }
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
        "schematic_guide": {
            "source_doc": "Vue éclatée Transition Patrol ASM Explode (2023.02.21_PatrolASM_Explode.jpg & Feuille 2)",
            "repere_map": [
                {"zone": "Boîtier & Pivot Principal", "details": "Axe principal (#5/#7 - 19 Nm), Pivot de bases Horst Link (#16 - 19 Nm)"},
                {"zone": "Biellette Rocker Link", "details": "Axe central de biellette (#27/#29 - 19 Nm), Ancrage haut amortisseur (#19/#22 - 10-12 Nm)"},
                {"zone": "Haubans & Amortisseur", "details": "Pivots de haubans (#25 - 19 Nm), Ancrage bas amortisseur (#11 - 10-12 Nm)"},
                {"zone": "Axe Arrière & UDH", "details": "Axe traversant arrière (#33 - 10-12 Nm), Vis de patte UDH (#35 - 25 Nm pas inversé)"}
            ]
        }
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
        "schematic_guide": {
            "source_doc": "Fiches Vues Éclatées Santa Cruz Vala 2026 (Carbon Linkage & Rear Triangle Hardware)",
            "repere_map": [
                {"zone": "Linkage & Triangle Avant", "details": "Pivot Axle M15x91 (Label C - 20 Nm), Ancrage Trunnion (Label T - 16 Nm), Ancrage Bas (Label H - 15.6 Nm)"},
                {"zone": "Moteur Bosch Gen 5", "details": "Vis de fixation moteur BDU38 (Label N & O - 30 Nm), Protection carter (Label B - 9 Nm / Label G - 3 Nm)"},
                {"zone": "Triangle Arrière & Bases", "details": "Pivot Horst Link (Label F - 9 Nm), Axe de triangle arrière M10x26 (Label D - 16 Nm)"},
                {"zone": "Patte UDH & Axe", "details": "Vis de patte UDH (Label C - 20 Nm pas à gauche), Axe arrière 12x173.7 (Label A)"}
            ]
        }
    },
    "norco_sight_2024": {
        "name": "Norco Sight Carbon Gen 5 (2024)",
        "type": "All-Mountain / Enduro",
        "weight_ref": "Standard",
        "suspensions_recommended": {
            "fork": {
                "model": "Öhlins RXF 38 m.2 (170mm)",
                "pressure": "Selon abaque Öhlins / SAG 15-20%",
                "sag": "25.5 - 34 mm",
                "lsr": "Ajustement Öhlins TTX18",
                "lsc": "Ajustement Öhlins TTX18",
                "hsc": "3 positions descente + 1 blocage"
            },
            "shock": {
                "model": "Öhlins TTX Air 2 (205x60mm)",
                "pressure": "Selon abaque Öhlins / SAG 30%",
                "sag": "18 mm enfoncement",
                "lsr": "Ajustement Öhlins TTX",
                "lsc": "Ajustement Öhlins TTX"
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
        "schematic_guide": {
            "source_doc": "Manuel d'assemblage Norco Sight Carbon Gen 5 (Sheets 1 to 6)",
            "repere_map": [
                {"zone": "Pivot Principal & Cadre", "details": "Main Pivot Shaft (Item 15/21 - 21 Nm), Retainer (Item 25 - 3 Nm)"},
                {"zone": "Biellette & Ancrages", "details": "Linkarm to Front Triangle / Trunnion (Item 19 - 16 Nm), Shock Mounts (20 Nm)"},
                {"zone": "Triangle Arrière & Galet Idler", "details": "Chain Stay to Seat Stays (Item 17 - 14 Nm), Linkarm to Seat Stays (Item 18 - 14 Nm), Idler Assembly (Item 26 - 16 Nm)"},
                {"zone": "Axe Arrière & UDH", "details": "Axe arrière L174 (Item 40 - 10 Nm), UDH Hanger Bolt (Item 39 - 20 Nm pas à gauche)"}
            ]
        }
    }
}

# Initialisation du State pour l'historique des Réglages Utilisateur
if "settings_history" not in st.session_state:
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
    ["🔧 Réglages Suspensions", "🔩 Couples de Serrage & Schémas", "📚 Historique des Réglages"],
    horizontal=True
)

st.divider()

# ---------------------------------------------------------
# RUBRIQUE 1 : RÉGLAGES SUSPENSIONS
# ---------------------------------------------------------
if nav_option == "🔧 Réglages Suspensions":
    st.subheader(f"📊 Réglages de suspension pour {bike_info['name']} ({user_weight} kg)")
    
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
    st.subheader("📝 Saisie de vos réglages personnalisés du jour")
    st.write("Enregistrez vos ajustements personnalisés selon les conditions de votre sortie.")
    
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
        
        submit_button = st.form_submit_button("💾 Enregistrer ces réglages")
        
        if submit_button:
            entry = {
                "date": str(date_ride),
                "bike": bike_info["name"],
                "rider_weight_kg": user_weight,
                "terrain": terrain_type,
                "weather": weather_cond,
                "fork_setup": f"{fork_press_user} | Rebond: {fork_lsr_user} | Comp: {fork_comp_user}",
                "shock_setup": f"{shock_press_user} | Rebond: {shock_lsr_user} | Comp: {shock_comp_user}",
                "comments": comments
            }
            
            # Essai de sauvegarde Google Sheets si configuré
            saved_to_gsheets = False
            try:
                from streamlit_gsheets import GSheetsConnection
                conn = st.connection("gsheets", type=GSheetsConnection)
                existing_data = conn.read()
                new_df = pd.concat([existing_data, pd.DataFrame([entry])], ignore_index=True)
                conn.update(data=new_df)
                saved_to_gsheets = True
                st.success("✅ Vos réglages ont été synchronisés avec succès sur votre Google Sheet !")
            except Exception:
                pass
                
            if not saved_to_gsheets:
                st.session_state.settings_history.append(entry)
                st.success("✅ Vos réglages ont été enregistrés localement dans la session !")

# ---------------------------------------------------------
# RUBRIQUE 2 : COUPLES DE SERRAGE & SCHÉMAS
# ---------------------------------------------------------
elif nav_option == "🔩 Couples de Serrage & Schémas":
    st.subheader(f"🔩 Fiche technique & Couples de serrage - {bike_info['name']}")
    
    # Guide Visuel de repérage sur les schémas
    st.markdown('<div class="schematic-box">', unsafe_allow_html=True)
    st.markdown("### 🗺️ Guide de repérage et carte d'implantation sur les schémas")
    schem = bike_info.get("schematic_guide", {})
    st.write(f"**Document source associé** : `{schem.get('source_doc', 'Manuel constructeur')}`")
    
    st.write("Retrouvez la position exacte de chaque vis et axe grâce aux repères / numéros des vues éclatées :")
    for rmap in schem.get("repere_map", []):
        st.markdown(f"* **{rmap['zone']}** : {rmap['details']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
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
            "zone": "Zone du cadre",
            "component": "Composant / Axe (Repère / Réf#)",
            "torque": "Couple préconisé (Nm)",
            "notes": "Recommandations (Frein filet / Graisse)"
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("""
    ---
    ### 💡 Rappels de montage & Sécurité :
    * **Patte de dérailleur SRAM UDH** : Attention, la vis de blocage UDH possède un **filetage inversé** (serrage dans le sens anti-horaire) à **25 Nm** (ou 20 Nm selon le fabricant de cadre).
    * **Frein filet** : Utilisez du frein filet moyen (ex: Loctite 242/243) sur les filetages indiqués.
    * **Graissage des axes** : Appliquez une fine couche de graisse uniquement sur le corps/fût de l'axe, jamais sur les filetages destinés au frein filet.
    * **Étriers de frein Post Mount** : Serrage préconisé à **9.5 Nm**. Centrer l'étrier en maintenant le levier enfoncé.
    * **Disques 6 trous (SRAM HS2 / Hope)** : Serrage à **6.2 Nm** en étoile croisée avec clé Torx T25.
    """)

# ---------------------------------------------------------
# RUBRIQUE 3 : HISTORIQUE & SUPPRESSION DE RÉGLAGES
# ---------------------------------------------------------
else:
    st.subheader("📚 Historique complet de vos réglages")
    
    history_data = []
    # Vérification Google Sheets d'abord
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_gsheets = conn.read()
        if not df_gsheets.empty:
            history_data = df_gsheets.to_dict('records')
    except Exception:
        history_data = st.session_state.settings_history

    if history_data:
        df_all = pd.DataFrame(history_data)
        
        # Filtre par vélo
        bike_options = ["Tous les vélos"] + list(df_all["bike"].unique()) if "bike" in df_all.columns else ["Tous les vélos"]
        selected_hist_bike = st.selectbox("Afficher l'historique pour :", bike_options, index=0)
        
        if selected_hist_bike != "Tous les vélos" and "bike" in df_all.columns:
            df_filtered = df_all[df_all["bike"] == selected_hist_bike]
        else:
            df_filtered = df_all
            
        st.dataframe(df_filtered, use_container_width=True)
        
        # Bouton d'export CSV pour garder une copie sur mobile
        csv_buffer = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger cet historique (.csv)",
            data=csv_buffer,
            file_name=f"vtt_setups_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        st.divider()
        # Suppression d'un réglage
        st.subheader("🗑️ Supprimer un réglage de l'historique")
        
        delete_options = [f"Ligne {i+1}: {row.get('date', '')} - {row.get('bike', '')} ({row.get('terrain', '')}) | {row.get('comments', '')[:30]}..." for i, row in enumerate(history_data)]
        selected_to_delete = st.selectbox("Choisissez le réglage à supprimer :", ["Aucun"] + delete_options)
        
        if selected_to_delete != "Aucun":
            idx = delete_options.index(selected_to_delete)
            if st.button("❌ Supprimer définitivement ce réglage"):
                del history_data[idx]
                
                # Mise à jour Google Sheets
                try:
                    from streamlit_gsheets import GSheetsConnection
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    conn.update(data=pd.DataFrame(history_data))
                    st.success("✅ Réglage supprimé de votre Google Sheet !")
                except Exception:
                    st.session_state.settings_history = history_data
                    st.success("✅ Réglage supprimé de la session !")
                st.rerun()
    else:
        st.info("Aucun réglage n'a encore été enregistré. Utilisez l'onglet '🔧 Réglages Suspensions' pour enregistrer votre première sortie !")

# Footer
st.divider()
st.caption("Gemini Notebook Studio - Application de gestion VTT & Réglages Atelier grounded from source materials.")
