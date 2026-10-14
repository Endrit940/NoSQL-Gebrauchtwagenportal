import pandas as pd
import streamlit as st
from pymongo import MongoClient, ASCENDING, DESCENDING
from pprint import pprint

st.set_page_config(
    page_title="Gebrauchtwagenportal",
    layout="wide"
)


@st.cache_resource
def get_autos():
    client = MongoClient("mongodb://localhost:27017/")
    return client["nosql"]["autos"]


autos = get_autos()


@st.cache_data
def lade_textwerte(feld):
    return sorted([
        x for x in autos.distinct(feld)
        if isinstance(x, str) and x.strip()
    ])


@st.cache_data
def lade_modelle(marke):
    return sorted([
        x for x in autos.distinct("model", {"brand": marke})
        if isinstance(x, str) and x.strip()
    ])


def formatiere_marke(marke):
    besondere_marken = {
        "alfa-romeo": "Alfa Romeo",
        "aston-martin": "Aston Martin",
        "bmw": "BMW",
        "mercedes-benz": "Mercedes-Benz",
        "land-rover": "Land Rover",
        "mini": "MINI",
        "volkswagen": "Volkswagen"
    }

    if marke in besondere_marken:
        return besondere_marken[marke]

    return marke.replace("-", " ").title()


def formatiere_modell(modell, marke):
    if not isinstance(modell, str):
        return modell

    modell_anzeige = modell.strip()

    varianten = sorted(
        {
            formatiere_marke(marke),
            marke.replace("-", " "),
            marke
        },
        key=len,
        reverse=True
    )

    for variante in varianten:
        if modell_anzeige.lower().startswith(variante.lower() + " "):
            modell_anzeige = modell_anzeige[len(variante):].strip()
            break

    return modell_anzeige


PREIS_MAX = 150000
KM_MAX = 300000
PS_MAX = 600
JAHR_MIN = 1990
JAHR_MAX = 2026

SORTIERUNGEN = {
    "Preis aufsteigend": ("price_in_euro", ASCENDING),
    "Preis absteigend": ("price_in_euro", DESCENDING),
    "Kilometer aufsteigend": ("mileage_in_km", ASCENDING),
    "Kilometer absteigend": ("mileage_in_km", DESCENDING),
    "PS aufsteigend": ("power_ps", ASCENDING),
    "PS absteigend": ("power_ps", DESCENDING),
    "Baujahr neueste zuerst": ("year", DESCENDING),
    "Baujahr älteste zuerst": ("year", ASCENDING)
}

kraftstoffe_erlaubt = [
    "CNG",
    "Diesel",
    "Diesel Hybrid",
    "Electric",
    "Ethanol",
    "Hybrid",
    "Hydrogen",
    "LPG",
    "Other",
    "Petrol",
    "Unknown"
]


with st.sidebar:
    st.title("Filter")

    st.divider()

    marke = st.selectbox(
        "Marke",
        ["Alle"] + lade_textwerte("brand"),
        format_func=lambda x:
            "Alle" if x == "Alle"
            else formatiere_marke(x)
    )

    modelle = lade_modelle(marke) if marke != "Alle" else []

    modell = st.selectbox(
        "Modell",
        ["Alle"] + modelle,
        disabled=(marke == "Alle"),
        format_func=lambda x:
            "Alle" if x == "Alle"
            else formatiere_modell(x, marke)
    )

    kraftstoff = st.selectbox(
        "Kraftstoff",
        ["Alle"] + [
            x for x in kraftstoffe_erlaubt
            if x in autos.distinct("fuel_type")
        ]
    )

    getriebe = st.selectbox(
        "Getriebe",
        ["Alle"] + lade_textwerte("transmission_type")
    )

    farbe = st.selectbox(
        "Farbe",
        ["Alle"] + lade_textwerte("color"),
        format_func=lambda x:
            "Alle" if x == "Alle"
            else x.capitalize()
    )

    st.divider()

    preis = st.slider(
        "Preis (€)",
        0,
        PREIS_MAX,
        (0, PREIS_MAX),
        step=1000
    )

    km = st.slider(
        "Kilometerstand",
        0,
        KM_MAX,
        (0, KM_MAX),
        step=5000
    )

    ps = st.slider(
        "Leistung (PS)",
        0,
        PS_MAX,
        (0, PS_MAX),
        step=10
    )

    jahr = st.slider(
        "Baujahr",
        JAHR_MIN,
        JAHR_MAX,
        (JAHR_MIN, JAHR_MAX)
    )

    st.divider()

    sortierung = st.selectbox(
        "Sortieren nach",
        list(SORTIERUNGEN)
    )


query = {}

if marke != "Alle":
    query["brand"] = marke

if modell != "Alle":
    query["model"] = modell

if kraftstoff != "Alle":
    query["fuel_type"] = kraftstoff

if getriebe != "Alle":
    query["transmission_type"] = getriebe

if farbe != "Alle":
    query["color"] = farbe


def bereich_hinzufuegen(feld, auswahl, minimum, maximum):
    bedingung = {
        "$type": "number"
    }

    if auswahl[0] > minimum:
        bedingung["$gte"] = auswahl[0]

    if auswahl[1] < maximum:
        bedingung["$lte"] = auswahl[1]

    query[feld] = bedingung


bereich_hinzufuegen(
    "price_in_euro",
    preis,
    0,
    PREIS_MAX
)

bereich_hinzufuegen(
    "mileage_in_km",
    km,
    0,
    KM_MAX
)

bereich_hinzufuegen(
    "power_ps",
    ps,
    0,
    PS_MAX
)

bereich_hinzufuegen(
    "year",
    jahr,
    JAHR_MIN,
    JAHR_MAX
)


print()
print("=" * 70)
print("MONGODB QUERY")
print("=" * 70)
pprint(query)
print("=" * 70)


st.title("Gebrauchtwagenportal")

tab_suche, tab_statistik = st.tabs([
    "Fahrzeuge",
    "Statistik"
])


with tab_suche:
    anzahl = autos.count_documents(query)

    sort_feld, sort_richtung = SORTIERUNGEN[sortierung]

    ergebnisse = list(
        autos.find(
            query,
            {
                "_id": 0,
                "brand": 1,
                "model": 1,
                "year": 1,
                "price_in_euro": 1,
                "mileage_in_km": 1,
                "power_ps": 1,
                "fuel_type": 1,
                "transmission_type": 1,
                "color": 1,
                "offer_description": 1
            }
        )
        .sort(sort_feld, sort_richtung)
        .limit(100)
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.metric(
                "Gefundene Fahrzeuge",
                f"{anzahl:,}"
            )

    with col2:
        with st.container(border=True):
            st.metric(
                "Angezeigt",
                f"{len(ergebnisse):,}"
            )

    with col3:
        with st.container(border=True):
            st.metric(
                "Im Portal gesamt",
                f"{autos.estimated_document_count():,}"
            )

    if anzahl > 100:
        st.info(
            "Zur Übersicht werden die ersten 100 Fahrzeuge angezeigt."
        )

    if not ergebnisse:
        st.warning(
            "Keine Fahrzeuge mit diesen Kriterien gefunden."
        )

    else:
        df = pd.DataFrame(ergebnisse)

        df["model"] = [
            formatiere_modell(m, b)
            for m, b in zip(
                df["model"],
                df["brand"]
            )
        ]

        df["brand"] = df["brand"].map(
            formatiere_marke
        )

        df["color"] = df["color"].map(
            lambda c:
                c.capitalize()
                if isinstance(c, str)
                else c
        )

        df = df.rename(
            columns={
                "brand": "Marke",
                "model": "Modell",
                "year": "Baujahr",
                "price_in_euro": "Preis (€)",
                "mileage_in_km": "Kilometer",
                "power_ps": "PS",
                "fuel_type": "Kraftstoff",
                "transmission_type": "Getriebe",
                "color": "Farbe",
                "offer_description": "Beschreibung"
            }
        )

        st.dataframe(
            df,
            hide_index=True,
            width="stretch",
            column_config={
                "Baujahr":
                    st.column_config.NumberColumn(
                        format="%d"
                    ),
                "Preis (€)":
                    st.column_config.NumberColumn(
                        format="%d €"
                    ),
                "Kilometer":
                    st.column_config.NumberColumn(
                        format="%d km"
                    ),
                "PS":
                    st.column_config.NumberColumn(
                        format="%d"
                    )
            }
        )


with tab_statistik:
    statistik_marke = st.selectbox(
        "Marke auswählen",
        lade_textwerte("brand"),
        format_func=formatiere_marke
    )

    pipeline = [
        {
            "$match": {
                "brand": statistik_marke,
                "price_in_euro": {
                    "$type": "number"
                },
                "mileage_in_km": {
                    "$type": "number"
                },
                "power_ps": {
                    "$type": "number"
                },
                "year": {
                    "$type": "number"
                }
            }
        },
        {
            "$group": {
                "_id": "$brand",
                "anzahl": {
                    "$sum": 1
                },
                "durchschnittspreis": {
                    "$avg": "$price_in_euro"
                },
                "durchschnitt_km": {
                    "$avg": "$mileage_in_km"
                },
                "durchschnitt_ps": {
                    "$avg": "$power_ps"
                }
            }
        }
    ]

    print()
    print("=" * 70)
    print("MONGODB AGGREGATION")
    print("=" * 70)
    pprint(pipeline)
    print("=" * 70)

    ergebnis = list(
        autos.aggregate(pipeline)
    )

    if ergebnis:
        s = ergebnis[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            with st.container(border=True):
                st.metric(
                    "Fahrzeuge",
                    f"{s['anzahl']:,}"
                )

        with col2:
            with st.container(border=True):
                st.metric(
                    "Ø Preis",
                    f"{s['durchschnittspreis']:,.0f} €"
                )

        with col3:
            with st.container(border=True):
                st.metric(
                    "Ø Kilometer",
                    f"{s['durchschnitt_km']:,.0f} km"
                )

        with col4:
            with st.container(border=True):
                st.metric(
                    "Ø Leistung",
                    f"{s['durchschnitt_ps']:,.0f} PS"
                )

    else:
        st.info(
            "Für diese Marke liegen keine Daten vor."
        )