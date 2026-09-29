import re
import pandas as pd
import streamlit as stl
import plotly.express as px

stl.set_page_config(
    page_title="Dashboard Titanic", page_icon="🚢", layout="wide"
)

# ==========================================
# 1. CHARGEMENT ET PRÉPARATION DES DONNÉES
# ==========================================


@stl.cache_data
def load_data():
    df = pd.read_csv("./data/titanic_dataset.csv")

    df["taille_famille"] = df["SibSp"] + df["Parch"] + 1

    def dev_type_famille(taille):
        if taille == 1:
            return "Seul"
        elif 2 <= taille <= 4:
            return "Petite famille"
        else:
            return "Grande famille"

    df["type_famille"] = df["taille_famille"].apply(dev_type_famille)


    def get_title(name):
        match = re.search(r",\s*([^\.]+)\.", str(name))
        if match:
            return match.group(1).strip()
        return "Autre"

    df["titre"] = df["Name"].apply(get_title)


    df["age_impute"] = df["Age"].isna()
    medianes_titre = df.groupby("titre")["Age"].transform("median")
    df["Age"] = df["Age"].fillna(medianes_titre)

 
    df["Sex"] = df["Sex"].map({"male": "Homme", "female": "Femme"})
    df["Survived_code"] = df["Survived"]  
    df["Survived"] = df["Survived"].map({0: "Décédé", 1: "Survivant"})
    df["Pclass"] = df["Pclass"].map({1: "1ère", 2: "2ième", 3: "3ième"})
    df["Embarked"] = df["Embarked"].map(
        {"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"}
    )
    
    # il y'a deux passagers sans port d'embarquement
    df = df.dropna(subset=["Embarked"])
    
    return df


df = load_data()

# ==========================================
# FONCTION GÉNÉRIQUE D'AGRÉGATION
# ==========================================


# Fonction générique de group by Retourne un DataFrame avec Total, Survivants et Taux (%)
def taux_par(group_col):

    if df_filtre.empty:
        return pd.DataFrame(columns=[group_col, "Total", "Survivants", "Taux"])

    res = (
        df_filtre.groupby(group_col, observed=False)["Survived_code"]
        .agg(Total="count", Survivants="sum")
        .reset_index()
    )
    res["Taux"] = (res["Survivants"] / res["Total"])
    return res


# ==========================================
# FONCTION TRANCHE D'AGE
# ==========================================
def tranche_age(age):
    if pd.isna(age):
        return "Inconnu"
    elif age<=12:
        return "Enfant"
    elif age<=18:
        return "Adolescent"
    elif age<=35:
        return "Jeune Adulte"
    else :
        return "Adulte"
        


# ==========================================
# BARRE LATÉRALE - FILTRES GLOBAUX
# ==========================================

# Standards visuels
types_famille_ordre = ["Seul", "Petite famille", "Grande famille"]
sex_ordre = ["Femme", "Homme"]

# Reload filtres
def reload_filtres():
    stl.session_state.classes_selectionnees = ["1ère", "2ième", "3ième"]
    stl.session_state.sexes_selectionnes = ["Homme", "Femme"]
    stl.session_state.ports_selectionnes = ["Cherbourg", "Queenstown", "Southampton"]
    stl.session_state.types_familles_selectionnes = ["Seul", "Petite famille", "Grande famille"]
    stl.session_state.tranche_age_seletionnee = (0, 80)
    

with stl.sidebar:
    b1,b2=stl.columns([2,1])
    with b1:
        stl.subheader("Filtres")
    with b2:
        if stl.button("reload") : 
            reload_filtres()
            

    # Filtre de Classes
    classes = stl.multiselect(
        "Pclass",
        options=["1ère", "2ième", "3ième"],
        default=["1ère", "2ième", "3ième"],
        key="classes_selectionnees"
    )

    # Filtre de Sexe
    sexes = stl.multiselect(
        "Sex", 
        options=["Homme", "Femme"], 
        default=["Homme", "Femme"],
        key="sexes_selectionnes"
    )

    # Filtre de Ports
    ports = stl.multiselect(
        "Port d'embarquement",
        options=["Cherbourg", "Queenstown", "Southampton"],
        default=["Cherbourg", "Queenstown", "Southampton"],
        key="ports_selectionnes"
    )

    #  Filtre de Type de famille
    familles = stl.multiselect(
        "Type de famille",
        options=types_famille_ordre,
        default=types_famille_ordre,
        key="types_familles_selectionnes"
    )

    # Gestion de la tranche d'âge minimale 
    min_age_val = int(df["Age"].min()) if not df["Age"].isna().all() else 0
    max_age_val = int(df["Age"].max()) if not df["Age"].isna().all() else 80

    age_min, age_max = stl.slider(
        "Tranche d'age", 
        min_age_val, max_age_val, 
        (min_age_val, max_age_val),
        key="tranche_age_seletionnee"
    )

    # Condition globale de filtre
    condition = (
        df["Pclass"].isin(classes)
        & df["Sex"].isin(sexes)
        & df["Embarked"].isin(ports)
        & df["type_famille"].isin(familles)
        & df["Age"].between(age_min, age_max)
    )

df_filtre = df[condition]
df_filtre["Tranche d'age"]=df_filtre['Age'].apply(tranche_age)

# ==========================================
# APPLICATION PRINCIPALE ET ONGLETS
# ==========================================
stl.title("🚢 Titanic - Tableau de bord des passagers")
stl.caption("Explorez les passagers du Titanic : qui étaient-ils, et qui a survécu")
c1,c2,c3,c4,c5=stl.columns(5)

#nombre de passagerss
taux_survie=0
taux_survie_total=0
if not df_filtre.empty:
    taux_survie = (
                len(df_filtre[df_filtre["Survived"] == "Survivant"])
                / len(df_filtre)
            ) * 100
    taux_survie_total = (
                len(df[df["Survived"] == "Survivant"]) / len(df)
            ) * 100

c1.metric('Nombre de passagers',f'{len(df_filtre)}')

c2.metric("Âge moyen" , f"{df_filtre['Age'].mean() if not df_filtre.empty else 0 : .1f} ans")

c3.metric("Tarif moyen" , f"{df_filtre['Fare'].mean() if not df_filtre.empty else 0 : .2f} USD")

c4.metric("Taux de survie",f"{taux_survie if not df_filtre.empty else 0:.2f}%",delta=f"{(taux_survie - taux_survie_total):.2f}%")

c5.metric("Âge moyen de personnes survivants" , f"{df_filtre[df_filtre["Survived"]=="Survivant"]['Age'].mean()if not df_filtre.empty else 0 : .1f} ans")
tab_survie, tab_demo, tab_familles, tab_brut = stl.tabs(
    ["Survie", "Démographie", "Familles", "Données brutes"]
)

# ------------------------------------------
# ONGLET 1 : SURVIE 
# ------------------------------------------
with tab_survie:
    stl.header("Vue globale de la survie")

    if df_filtre.empty:
        stl.warning("Aucun passager ne correspond aux filtres sélectionnés.")
    else:       
        # les graphes
        g1, g2, g3 = stl.columns(3)

        #g1 : taux de survivant par sexe
        taux_sexe=taux_par(["Sex"])

        fig = px.bar(
            taux_sexe,
            x="Sex",
            y="Taux",
            text_auto=".0%",
            title="Par sexe"
        )

        g1.plotly_chart(fig)

        # g2 : taux de survivant par classe 
        taux_class = taux_par(["Pclass"])

        fig2 = px.bar(
            taux_class,
            x="Pclass",
            y="Taux",
            text_auto=".0%",
            title="Par classe"
        )

        g2.plotly_chart(fig2)
        
        # g3 : taux de survivant par sexe et classe
        taux_sexe_class=taux_par(["Sex","Pclass"])

        fig3 = px.bar(
            taux_sexe_class,
            x="Pclass",
            y="Taux",
            # text_auto=".0%",
            title="Par classe et Sexe",
            color="Sex",
            barmode="group"
        )
        
        g3.plotly_chart(fig3)

# ------------------------------------------
# ONGLET 2 : DÉMOGRAPHIE
# ------------------------------------------

with tab_demo:
    stl.header("Profil démographique des passagers")

    if df_filtre.empty:
        stl.warning("Aucun passager ne correspond aux filtres sélectionnés.")
    else:
        pyramide_age = (
            df_filtre.groupby(["Tranche d'age", "Sex"], observed=False)
            .size()
            .reset_index(name="Valeur")
        )
        order = ["Enfant", "Adolescent", "Jeune Adulte", "Adulte"]

        pyramide_age.loc[pyramide_age["Sex"] == "Homme", "Valeur"] *= -1

        fig = px.bar(
            pyramide_age,
            x="Valeur",
            y="Tranche d'age",
            color="Sex",
            orientation="h",
            title="Pyramide des tranches d'âges par Sexe",
            category_orders={
                "Tranche d'age": order,
                "Sex": sex_ordre,
            },
            # text_auto=True,
        )

        fig.update_layout(
            xaxis=dict(
                title="Nombre de passagers",
                tickmode="array",
                tickvals=[-150, -100, -50, 0, 50, 100, 150],
                ticktext=["150", "100", "50", "0", "50", "100", "150"],
            ),
            yaxis_title="Tranche d'âge",
        )

        stl.plotly_chart(fig, use_container_width=True)
        

# ------------------------------------------
# ONGLET 3 : FAMILLES 
# ------------------------------------------
with tab_familles:
    stl.header("Analyse de la survie selon la structure familiale")

    if df_filtre.empty:
        stl.warning(
            "Veuillez sélectionner au moins une option dans la barre latérale pour afficher l'analyse des familles."
        )
    else:
        # Indicateurs en tête d'onglet
        passagers_seuls_filtre = len(
            df_filtre[df_filtre["type_famille"] == "Seul"]
        )
        passagers_seuls_total = len(df[df["type_famille"] == "Seul"])

        gf_filtre = df_filtre[df_filtre["type_famille"] == "Grande famille"]
        gf_total = df[df["type_famille"] == "Grande famille"]

        taux_gf_f = (
            (gf_filtre["Survived_code"].sum() / len(gf_filtre) * 100)
            if len(gf_filtre) > 0
            else 0.0
        )
        taux_gf_tot = (
            (gf_total["Survived_code"].sum() / len(gf_total) * 100)
            if len(gf_total) > 0
            else 0.0
        )

        ind1, ind2 = stl.columns(2)
        
        ind1.metric(
            label="Passagers voyageant seuls",
            value=f"{passagers_seuls_filtre}",
            delta=f"{passagers_seuls_filtre - passagers_seuls_total} vs total",
        )
        ind2.metric(
            label="Taux de survie (Grandes familles)",
            value=f"{taux_gf_f:.1f}%",
            delta=f"{taux_gf_f - taux_gf_tot:.1f}% vs ensemble",
        )

        c1,c2=stl.columns(2)
        
        #  Graphique 1 : Taux de survie par type de famille
        with c1 :      
            taux_famille = taux_par("type_famille")
            fig1 = px.bar(
                taux_famille,
                x="type_famille",
                y="Taux",
                text_auto=".0%",
                title="Taux de survie par type de famille",
                category_orders={"type_famille": types_famille_ordre},
            )
            fig1.update_yaxes(range=[0, 1], tickformat=".0%")
            stl.plotly_chart(fig1, use_container_width=True)

        # Graphique 2 : Taux de survie par type de famille et par sexe 
        with c2:
            taux_famille_sexe=taux_par(["type_famille","Sex"])
            fig2 = px.bar(
                taux_famille_sexe,
                x="type_famille",
                y="Taux",
                text_auto=".0%",
                title="Taux de survie par type de famille et par Sexe",
                color="Sex",
                barmode="group",
                category_orders={
                    "type_famille": types_famille_ordre,
                    "Sex": sex_ordre,
                },
            )
            fig2.update_yaxes(range=[0, 1], tickformat=".0%")
            stl.plotly_chart(fig2, use_container_width=True)

        # Tableau croisé : Type de famille vs Classe 
        stl.subheader("Tableau croisé : Type de famille vs Classe")
        ct = pd.crosstab(
            df_filtre["type_famille"],
            df_filtre["Pclass"],
            margins=True,
            margins_name="Total",
        )
        ct = ct.reindex(
            [f for f in types_famille_ordre if f in ct.index] + ["Total"]
        )
        stl.dataframe(ct, use_container_width=True)

        # INTERPRÉTATION 
        stl.subheader("Interprétation des résultats")
        stl.markdown(
            """
        Voyager en **petite famille (2 à 4 personnes)** offrait les meilleures chances de survie (**56%**, *100/180 passagers*), 
        nettement supérieures à celles des passagers **seuls** (**30%**, *163/537 passagers*). En revanche, le taux de survie s'effondre 
        à **16%** (*10/62 passagers*) pour les **grandes familles (5 personnes et plus)**.
        
        En examinant l'explication concurrente de la classe, le tableau croisé révèle que **76% des grandes familles (47/62)** 
        voyageaient en 3ᵉ classe, contre seulement **8% en 1ère classe (5/62)**. La faible survie des grandes familles s'explique donc 
        principalement par leur surreprésentation en 3ᵉ classe et par la difficulté logistique de regrouper un grand nombre de personnes lors du naufrage.
        """
        )

        # SECTION REPLIABLE : LIMITES DES DONNÉES
        with stl.expander("Limites des données"):
            nb_gf = len(df[df["type_famille"] == "Grande famille"])
            nb_imp = df["age_impute"].sum()
            pct_imp = (nb_imp / len(df)) * 100

            stl.write(
                f"- **Effectif des grandes familles :** {nb_gf} passagers seulement (soit {nb_gf/len(df)*100:.1f}% de la base globale)."
            )
            stl.write(
                f"- **Part des âges imputés :** {nb_imp} âges imputés sur l'ensemble du dataset, soit **{pct_imp:.1f}%** des lignes."
            )
            stl.write(
                "- **Limites d'interprétation :** La base reconstitue les familles à partir des liens directs déclarés (`SibSp` et `Parch`). Elle ignore les liens de parenté sous des noms différents, les accompagnants, ainsi que la localisation exacte des cabines au moment de la collision."
            )
            
# ------------------------------------------
# ONGLET 4 : DONNÉES BRUTES
# ------------------------------------------
with tab_brut:
    stl.header("Aperçu des données brutes filtrées")
    stl.dataframe(df_filtre)
    
    