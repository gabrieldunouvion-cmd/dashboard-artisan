import streamlit as st
import pandas as pd

# 1. Configuration de la page
st.set_page_config(
    page_title="Tableau de Bord Artisan",
    page_icon="📊",
    layout="wide"
)

# --- SÉCURITÉ ---
st.title("🔒 Accès Sécurisé")
mot_de_passe = st.text_input("Veuillez entrer le mot de passe :", type="password")

if mot_de_passe != "artisan2026":
    st.warning("En attente de l'authentification...")
    st.stop() 

# --- INTERFACE ---
st.title("📊 Tableau de Bord Financier")
st.markdown("---")

# --- ROUTAGE MULTI-CLIENTS ---
# 1. On cherche si un paramètre "client" est présent dans l'URL
client_id = st.query_params.get("client", None)

# 2. Sécurité : Si aucun client n'est précisé dans l'URL
if not client_id:
    st.error("⚠️ URL invalide : Aucun identifiant client détecté. Veuillez utiliser votre lien personnalisé.")
    st.stop()

# 3. Sécurité : On cherche le lien Google Sheets du client dans le coffre-fort Streamlit
try:
    SHEET_URL = st.secrets["clients"][client_id]
except KeyError:
    st.error(f"⚠️ Accès refusé : L'identifiant '{client_id}' n'est pas reconnu dans notre base.")
    st.stop()
@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(SHEET_URL)

try:
    donnees = load_data()
    
    # 1. NETTOYAGE
    colonnes_montants = ['Montant HT', 'Montant TVA', 'Montant TTC']
    for col in colonnes_montants:
        donnees[col] = donnees[col].astype(str).str.replace(',', '.', regex=False)
        donnees[col] = pd.to_numeric(donnees[col], errors='coerce').fillna(0)

    donnees['Date'] = pd.to_datetime(donnees['Date'], format='%d/%m/%Y', errors='coerce')
    donnees = donnees.dropna(subset=['Date'])
    
    # Sécurité au cas où la colonne Catégorie ne serait pas encore bien lue
    if 'Catégorie' not in donnees.columns:
        donnees['Catégorie'] = "Non catégorisé"


    # 2. CENTRE DE CONTRÔLE (SIDEBAR)
    st.sidebar.header("🕹️ Centre de contrôle")
    st.sidebar.markdown("Filtrez vos données en direct.")

    # Filtre Date
    date_min = donnees['Date'].min().date()
    date_max = donnees['Date'].max().date()
    
    dates_selectionnees = st.sidebar.date_input(
        "Période",
        value=[date_min, date_max],
        min_value=date_min,
        max_value=date_max
    )
    
    if len(dates_selectionnees) == 2:
        date_debut, date_fin = dates_selectionnees
    else:
        date_debut, date_fin = dates_selectionnees[0], dates_selectionnees[0]

    # NOUVEAU : Filtre Catégorie
    liste_categories = donnees['Catégorie'].unique().tolist()
    categories_selectionnees = st.sidebar.multiselect(
        "Catégories d'achats",
        options=liste_categories,
        default=liste_categories 
    )

    # Filtre Fournisseur
    liste_fournisseurs = donnees['Fournisseur'].unique().tolist()
    fournisseurs_selectionnes = st.sidebar.multiselect(
        "Fournisseurs",
        options=liste_fournisseurs,
        default=liste_fournisseurs 
    )


    # 3. FILTRAGE DES DONNÉES
    masque = (
        (donnees['Date'].dt.date >= date_debut) &
        (donnees['Date'].dt.date <= date_fin) &
        (donnees['Fournisseur'].isin(fournisseurs_selectionnes)) &
        (donnees['Catégorie'].isin(categories_selectionnees))
    )
    donnees_filtrees = donnees[masque]


    # 4. KPIS ET GRAPHIQUES
    st.success("✅ Données synchronisées et filtrées !")
    
    total_ht = donnees_filtrees['Montant HT'].sum()
    total_tva = donnees_filtrees['Montant TVA'].sum()
    total_ttc = donnees_filtrees['Montant TTC'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Dépenses HT", value=f"{total_ht:.2f} €")
    with col2:
        st.metric(label="TVA à récupérer", value=f"{total_tva:.2f} €")
    with col3:
        st.metric(label="Sortie de Trésorerie TTC", value=f"{total_ttc:.2f} €")
        
    st.markdown("---")
    
  if not donnees_filtrees.empty:
        # NOUVEAU : Graphique par Catégorie
        st.subheader("🎯 Répartition par Catégorie de dépenses")
        depenses_categorie = donnees_filtrees.groupby("Catégorie")["Montant TTC"].sum().sort_values(ascending=False)
        st.bar_chart(depenses_categorie)
        
        st.subheader("Détail des factures")
        donnees_filtrees['Date'] = donnees_filtrees['Date'].dt.strftime('%d/%m/%Y')
        st.dataframe(donnees_filtrees, use_container_width=True)

        # --- EXPORT DES DONNÉES (COMPTABILITÉ) ---
        st.markdown("---")
        st.subheader("📥 Exporter le Bilan")

        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8-sig')

        # On utilise bien donnees_filtrees ici !
        csv_export = convert_df(donnees_filtrees)

        st.download_button(
            label="Télécharger les données filtrées (Format Excel/CSV)",
            data=csv_export,
            file_name="bilan_financier_artisan.csv",
            mime="text/csv",
        )

    else:
        st.warning("⚠️ Aucune facture ne correspond à ces critères de recherche.")

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")