import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta


def calculate_working_days(start_date, end_date):
    """Calculate the number of working days (excluding weekends) between two dates."""
    current_date = start_date
    working_days = 0

    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday to Friday (0=Monday, 4=Friday)
            working_days += 1
        current_date += timedelta(days=1)

    return working_days

def analyze_publication_delays(df):

    # Remove invalid rows
    df = df.dropna(subset=["data_registro_generale", "data_inizio_pubblicazione"])
    
    """Compute the delay in publication in terms of working days."""
    df["ritardo_pubblicazione"] = df.apply(lambda row: 
        calculate_working_days(row["data_registro_generale"], row["data_inizio_pubblicazione"]) - 1, axis=1)
    
    # Handle cases where the start and end dates are the same
    df["ritardo_pubblicazione"] = df["ritardo_pubblicazione"].apply(lambda x: max(x, 0))

    return df

def analyze_mittenti_performance(df):
    """Analyze the average delay per sender (mittente)."""
    mittente_performance = df.groupby("mittente")["ritardo_pubblicazione"].mean().reset_index()
    mittente_performance.columns = ["Mittente", "Ritardo Medio (giorni lavorativi)"]
    mittente_performance = mittente_performance.sort_values(by="Ritardo Medio (giorni lavorativi)", ascending=False)
    return mittente_performance

def main():
    st.title("📊 Combined Analysis of Publications")

    # Load data
    df = load_data(DB_NAME)
    if df.empty:
        st.warning("No publication data available.")
        return

    # Analyze publication delays
    df = analyze_publication_delays(df)

    # Display data preview
    st.subheader("Dataset Overview")
    st.write("This table shows the first few records from the database:")
    st.dataframe(df.head())

    # Histogram of publication delays
    st.subheader("📅 Publication Delays (Working Days)")
    fig1 = px.histogram(df, x="ritardo_pubblicazione", nbins=15,
                        title="Distribution of Publication Delays (Working Days)",
                        labels={"ritardo_pubblicazione": "Delay (Working Days)", "count": "Number of Publications"})
    st.plotly_chart(fig1)

    # Performance of different senders (mittenti)
    mittente_performance = analyze_mittenti_performance(df)
    
    st.subheader("⏳ Sender Performance (Average Delay)")
    st.write("The following table shows the average publication delay per sender (mittente):")
    st.dataframe(mittente_performance)

    # Bar chart of sender performance
    fig2 = px.bar(mittente_performance, x="Ritardo Medio (giorni lavorativi)", y="Mittente", 
                  orientation="h", title="Average Publication Delay per Sender",
                  labels={"Ritardo Medio (giorni lavorativi)": "Average Delay (Working Days)", "Mittente": "Sender"})
    st.plotly_chart(fig2)

if __name__ == "__main__":
    main()
