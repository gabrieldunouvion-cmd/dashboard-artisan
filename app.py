import streamlit as st
import pandas as pd

# 1. Configuration de la page
st.set_page_config(
    page_title="Tableau de Bord Artisan",
    page_icon="📊",
    layout="wide"
)

# --- SYSTÈME DE SÉCURITÉ (prototype) ---
st.title("🔒 Accès Sécurisé")
mot_de_passe = st.text_input("Veuillez entrer le mot de passe :", type="password")

if mot_de_passe != "artisan2026":
    st.warning("En attente de l'authentification...")
    st.stop()

st.title("📊 Tableau de Bord Financier")
st.markdown("---")

SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2NWBRr9QH7VIHfPHHwGRXXvQaRhDZ9ecfdm0cxiM-cKRn8tNjBNgX8tXQTVhq4_y0BEEMsabBAnB6/pub?gid=746055985&single=true&output=csv"
)

COLONNES_MONTANTS = ["Montant HT", "Montant TVA", "Montant TTC"]


@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(SHEET_URL)


try:
    donnees = load_data()

    # --- 1. NETTOYAGE ET PRÉPARATION DES DONNÉES ---
    for col in COLONNES_MONTANTS:
        donnees[col] = donnees[col].astype(str).str.replace(",", ".", regex=False)
        donnees[col] = pd.to_numeric(donnees[col], errors="coerce").fillna(0)

    donnees["Date"] = pd.to_datetime(donnees["Date"], format="%d/%m/%Y", errors="coerce")
    donnees = donnees.dropna(subset=["Date"])

    # --- 2. LA BARRE LATÉRALE (SIDEBAR) ---
    st.sidebar.header("🕹️ Centre de contrôle")
    st.sidebar.markdown("Filtrez vos données en direct.")

    date_min = donnees["Date"].min().date()
    date_max = donnees["Date"].max().date()

    dates_selectionnees = st.sidebar.date_input(
        "Période",
        value=[date_min, date_max],
        min_value=date_min,
        max_value=date_max,
    )

    if len(dates_selectionnees) == 2:
        date_debut, date_fin = dates_selectionnees
    else:
        date_debut = date_fin = dates_selectionnees[0]

    liste_fournisseurs = donnees["Fournisseur"].unique().tolist()
    fournisseurs_selectionnes = st.sidebar.multiselect(
        "Fournisseurs",
        options=liste_fournisseurs,
        default=liste_fournisseurs,
    )

    # --- 3. APPLICATION DES FILTRES ---
    masque = (
        (donnees["Date"].dt.date >= date_debut)
        & (donnees["Date"].dt.date <= date_fin)
        & (donnees["Fournisseur"].isin(fournisseurs_selectionnes))
    )
    donnees_filtrees = donnees[masque].copy()

    # --- 4. AFFICHAGE DES KPIS DYNAMIQUES ---
    st.success("✅ Données synchronisées et filtrées !")

    total_ht = donnees_filtrees["Montant HT"].sum()
    total_tva = donnees_filtrees["Montant TVA"].sum()
    total_ttc = donnees_filtrees["Montant TTC"].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Dépenses HT", value=f"{total_ht:.2f} €")
    with col2:
        st.metric(label="TVA à récupérer", value=f"{total_tva:.2f} €")
    with col3:
        st.metric(label="Sortie de Trésorerie TTC", value=f"{total_ttc:.2f} €")

    st.markdown("---")

    # --- 5. GRAPHIQUE ET TABLEAU DYNAMIQUES ---
    if not donnees_filtrees.empty:
        st.subheader("📈 Répartition des dépenses")
        depenses_fournisseur = (
            donnees_filtrees.groupby("Fournisseur")["Montant TTC"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(depenses_fournisseur)

        st.subheader("Détail des factures")
        affichage = donnees_filtrees.copy()
        affichage["Date"] = affichage["Date"].dt.strftime("%d/%m/%Y")
        st.dataframe(affichage, use_container_width=True)
    else:
        st.warning("⚠️ Aucune facture ne correspond à ces critères de recherche.")

except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")
