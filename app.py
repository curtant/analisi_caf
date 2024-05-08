import streamlit as st
import pandas as pd
import altair as alt
# Funzione per caricare i dati, utilizzando la cache per migliorare le prestazioni
@st.cache_data
def load_data():
    path = "data/fatturato.csv"
    data = pd.read_csv(path)
    return data


def plot_fatturato_totale(df):
    # DataFrame separato per le somme
    total_df = pd.DataFrame({
        'Tipo': ['Fatturato IRPEF', 'Fatturato Custom'],
        'Totale': [df['Fatturato_IRPEF_Dopo_Sconti'].sum(), df['Fatturato_Custom_Dopo_Sconti'].sum()]
    })

    # Grafico Fatturato Totale
    chart = alt.Chart(total_df).mark_bar().encode(
        x='Tipo',
        y='Totale',
        color='Tipo',
        tooltip=['Totale']
    ).properties(
        title='Fatturato Totale IRPEF vs Custom',
        height=400,
        width=600
    )
    return chart


def plot_fatturato_per_classe(df):
    # Grafico del fatturato per classe di reddito
    base = alt.Chart(df).encode(
        x=alt.X('Classe:N', sort=None), 
        tooltip=['Classe', 'Fatturato_IRPEF', 'Fatturato_Custom_Dopo_Sconti']
    )
    bar1 = base.mark_bar(color='blue').encode(
        y='Fatturato_IRPEF_Dopo_Sconti:Q',
        tooltip=['Fatturato_IRPEF_Dopo_Sconti']
    )
    bar2 = base.mark_bar(color='green').encode(
        y='Fatturato_Custom_Dopo_Sconti:Q',
        tooltip=['Fatturato_Custom_Dopo_Sconti']
    )

    chart = alt.layer(bar1, bar2).resolve_scale(y='independent').properties(
        title='Confronto Fatturato per Classe di Reddito',
        width=600,
        height=400
    )
    return chart


def prepare_pie_data(df):
    #  Grafico a torta prime 10 classi di reddito
    df_sorted = df.sort_values(by='Numero_Clienti', ascending=False).head(10)
    total_clients = df_sorted['Numero_Clienti'].sum()
    df_sorted['Percentuale_Clienti'] = (df_sorted['Numero_Clienti'] / total_clients) * 100
    return df_sorted

def plot_pie_chart(df):
    pie_chart = alt.Chart(df).mark_arc().encode(
        theta=alt.Theta(field="Percentuale_Clienti", type="quantitative"),
        color=alt.Color(field="Classe", type="nominal", legend=alt.Legend(title="Classi di Reddito")),
        tooltip=[alt.Tooltip('Classe', title='Classe di Reddito'), alt.Tooltip('Percentuale_Clienti', title='Percentuale', format='.2f')]
    ).properties(
        title='Top 10 Distribuzione Percentuale dei Clienti per Classe di Reddito',
        width=400,
        height=400
    )
    return pie_chart


def main():
    st.title('Dashboard Analisi Tariffario CAF')

    # Sidebar per i controlli
    st.sidebar.title("Impostazioni")

    # Caricamento dei dati
    df = load_data()

    # Sezione per gestire il Fatturato Custom
    st.sidebar.header("Fatturato Custom")
    df = load_data()

    # Campo di input per modificare la tariffa custom
    custom_rate = st.sidebar.number_input('Seleziona il nuovo obiettivo di tariffa media:', min_value=0, max_value=100, value=35, step=1)
    df['Tariffa_Custom'] = custom_rate
    df['Fatturato_Custom'] = df['Numero_Clienti'] * df['Tariffa_Custom']

    # Slider per gestire la percentuale di rinuncia
    rinuncia_rate = st.sidebar.slider('Percentuale di rinuncia:', min_value=0, max_value=50, value=0, step=1)
    df['Percentuale_Rinuncia'] = rinuncia_rate
    df['Fatturato_Custom_Adjusted'] = df['Fatturato_Custom'] * (1 - df['Percentuale_Rinuncia'] / 100)

    # Sezione per gestire gli Sconti
    st.sidebar.header("Sconti")
    sconto_tesserati = st.sidebar.number_input('Sconto per tesserati (€):', min_value=0, value=5)
    sconto_congiunti = st.sidebar.number_input('Sconto per congiunti (€):', min_value=0, value=3)

    # Slider per modificare la percentuale di tesserati e congiunti
    pct_tesserati = st.sidebar.slider('Percentuale di tesserati:', min_value=0, max_value=50, value=15)
    pct_congiunti = st.sidebar.slider('Percentuale di congiunti:', min_value=0, max_value=50, value=10)
    df['Percentuale_Tesserati'] = pct_tesserati
    df['Percentuale_Congiunti'] = pct_congiunti
    df['Clienti_Tesserati'] = (df['Numero_Clienti'] * df['Percentuale_Tesserati'] / 100).astype(int)
    df['Clienti_Congiunti'] = (df['Numero_Clienti'] * df['Percentuale_Congiunti'] / 100).astype(int)

    df['Sconto_Totale_Tesserati'] = df['Clienti_Tesserati'] * sconto_tesserati
    df['Sconto_Totale_Congiunti'] = df['Clienti_Congiunti'] * sconto_congiunti
    df['Fatturato_IRPEF_Dopo_Sconti'] = df['Fatturato_IRPEF'] - (df['Sconto_Totale_Tesserati'] + df['Sconto_Totale_Congiunti'])
    df['Fatturato_Custom_Dopo_Sconti'] = df['Fatturato_Custom_Adjusted'] - (df['Sconto_Totale_Tesserati'] + df['Sconto_Totale_Congiunti'])

    # Visualizzazione dei grafici
    st.altair_chart(plot_fatturato_totale(df), use_container_width=True)
    st.altair_chart(plot_fatturato_per_classe(df), use_container_width=True)
    
    df_prepared = prepare_pie_data(df)
    pie_chart = plot_pie_chart(df_prepared)
    st.altair_chart(pie_chart, use_container_width=True)
    
    # Visualizzazione dei dati aggiornati nella pagina principale
    st.write("Dati aggiornati:", df)

if __name__ == "__main__":
    main()
