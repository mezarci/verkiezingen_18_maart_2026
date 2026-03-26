import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Uitslagen Den Haag 2026", layout="wide")

@st.cache_data
def load_and_clean_final():
    df = pd.read_csv('cleaned_election_data.csv')
    stations = pd.read_csv('station_info.csv')
    
    # Voeg postcode informatie toe aan de hoofd-dataset
    df = df.merge(stations[['Polling Station', 'Postcode']], on='Polling Station', how='left')
    
    def postcode_naar_wijk(pc_str):
        try:
            # Pak de eerste 4 cijfers van de postcode (bijv. 2511)
            pc = int(str(pc_str)[:4])
            if 2511 <= pc <= 2518: return 'Centrum'
            if 2519 <= pc <= 2525: return 'Schilderswijk / Centrum'
            if 2526 <= pc <= 2533: return 'Laak / Spoorwijk'
            if 2541 <= pc <= 2548: return 'Escamp (Bouwlust/Morgenstond)'
            if 2551 <= pc <= 2555: return 'Loosduinen'
            if 2561 <= pc <= 2566: return 'Segbroek'
            if 2571 <= pc <= 2574: return 'Transvaal / Rustenburg'
            if 2581 <= pc <= 2587: return 'Scheveningen'
            if 2591 <= pc <= 2597: return 'Haagse Hout / Bezuidenhout'
            if 2491 <= pc <= 2498: return 'Leidschenveen / Ypenburg'
            return 'Overig Den Haag'
        except:
            return 'Onbekend'

    df['Wijk'] = df['Postcode'].apply(postcode_naar_wijk)
    return df

df = load_and_clean_final()

# --- SIDEBAR MET DYNAMISCHE FILTERS ---
st.sidebar.title("🔍 Selectie")

# 1. Partij filter
partijen = sorted(df['Party'].unique())
selected_party = st.sidebar.selectbox("Stap 1: Kies een Partij", ["Alle"] + partijen)

# 2. Dynamische Kandidaat filter (afhankelijk van partij)
if selected_party != "Alle":
    kandidaat_opties = sorted(df[df['Party'] == selected_party]['Candidate'].unique())
else:
    kandidaat_opties = sorted(df['Candidate'].unique())

selected_candidate = st.sidebar.selectbox("Stap 2: Kies een Kandidaat", kandidaat_opties)

# 3. Wijk filter
wijken = sorted(df['Wijk'].unique())
selected_wijken = st.sidebar.multiselect("Stap 3: Filter op Wijk(en)", wijken, default=wijken)

# Toepassen van filters op de dataset
filtered_df = df[df['Wijk'].isin(selected_wijken)]
if selected_party != "Alle":
    filtered_df = filtered_df[filtered_df['Party'] == selected_party]

# --- DASHBOARD LAYOUT ---
st.title(f"🗳️ Analyse: {selected_party if selected_party != 'Alle' else 'Alle Partijen'}")

tab_overzicht, tab_kandidaat = st.tabs(["📊 Wijkoverzicht", "👤 Kandidaat Detail"])

with tab_overzicht:
    st.subheader("Stemmenverdeling per Wijk")
    
    # Aggregeren voor grafiek
    wijk_data = filtered_df.groupby(['Wijk', 'Party'])['Votes'].sum().reset_index()
    
    fig = px.bar(wijk_data, x='Wijk', y='Votes', color='Party', 
                 title="Totaal aantal stemmen per wijk (gefilterd)",
                 barmode='stack', height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabel met exacte cijfers
    pivot_table = wijk_data.pivot(index='Party', columns='Wijk', values='Votes').fillna(0).astype(int)
    st.write("### Exacte aantallen per wijk", pivot_table)

with tab_kandidaat:
    # Hier focussen we op de geselecteerde kandidaat uit de sidebar
    cand_detail = df[df['Candidate'] == selected_candidate]
    
    st.header(f"Rapportage: {selected_candidate}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Totaal stemmen", f"{cand_detail['Votes'].sum():,}")
    c2.metric("Partij", cand_detail['Party'].iloc[0])
    c3.metric("Hoofdkwartier (Beste Wijk)", cand_detail.groupby('Wijk')['Votes'].sum().idxmax())
    
    # Grafiek voor kandidaat
    st.subheader("Waar kwamen de stemmen vandaan?")
    fig_cand = px.bar(cand_detail.groupby('Wijk')['Votes'].sum().reset_index(), 
                       x='Wijk', y='Votes', color='Wijk', title=f"Spreiding {selected_candidate}")
    st.plotly_chart(fig_cand, use_container_width=True)
    
    st.subheader("Top stembureaus voor deze kandidaat")
    st.dataframe(cand_detail.sort_values('Votes', ascending=False)[['Polling Station', 'Wijk', 'Votes']].head(15))