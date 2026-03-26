import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Uitslagen Den Haag 2026", layout="wide")

# Check of bestanden bestaan om errors te voorkomen
if not os.path.exists('cleaned_election_data.csv') or not os.path.exists('station_info.csv'):
    st.error("⚠️ Fout: Data bestanden niet gevonden op GitHub! Zorg dat 'cleaned_election_data.csv' en 'station_info.csv' in dezelfde map staan.")
    st.stop()

@st.cache_data
def load_and_clean_final():
    df = pd.read_csv('cleaned_election_data.csv')
    stations = pd.read_csv('station_info.csv')
    df = df.merge(stations[['Polling Station', 'Postcode']], on='Polling Station', how='left')
    
    def postcode_naar_wijk(pc_str):
        try:
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

# --- SIDEBAR ---
st.sidebar.title("🔍 Selectie")
partijen = sorted(df['Party'].unique())
selected_party = st.sidebar.selectbox("1. Kies een Partij", ["Alle"] + partijen)

# Dynamische kandidatenlijst
if selected_party != "Alle":
    kandidaat_opties = sorted(df[df['Party'] == selected_party]['Candidate'].unique())
else:
    kandidaat_opties = sorted(df['Candidate'].unique())

selected_candidate = st.sidebar.selectbox("2. Kies een Kandidaat", kandidaat_opties)

wijken = sorted(df['Wijk'].unique())
selected_wijken = st.sidebar.multiselect("3. Filter op Wijk(en)", wijken, default=wijken)

filtered_df = df[df['Wijk'].isin(selected_wijken)]
if selected_party != "Alle":
    filtered_df = filtered_df[filtered_df['Party'] == selected_party]

# --- DASHBOARD ---
st.title(f"🗳️ Analyse: {selected_party}")

tab1, tab2 = st.tabs(["📊 Wijkoverzicht", "👤 Kandidaat Detail"])

with tab1:
    wijk_data = filtered_df.groupby(['Wijk', 'Party'])['Votes'].sum().reset_index()
    fig = px.bar(wijk_data, x='Wijk', y='Votes', color='Party', barmode='stack')
    st.plotly_chart(fig, use_container_width=True)
    
    pivot = wijk_data.pivot(index='Party', columns='Wijk', values='Votes').fillna(0).astype(int)
    st.write("### Cijfers per wijk", pivot)

with tab2:
    cand_detail = df[df['Candidate'] == selected_candidate]
    st.header(f"Rapport: {selected_candidate}")
    col1, col2 = st.columns(2)
    col1.metric("Totaal stemmen", f"{cand_detail['Votes'].sum():,}")
    col2.metric("Partij", cand_detail['Party'].iloc[0])
    
    fig_cand = px.bar(cand_detail.groupby('Wijk')['Votes'].sum().reset_index(), x='Wijk', y='Votes')
    st.plotly_chart(fig_cand, use_container_width=True)
