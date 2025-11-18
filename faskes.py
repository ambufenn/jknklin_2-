# faskes.py
import streamlit as st
import pandas as pd
from model import load_model
from handler import analisis_sanggahan_nlp

def tampilkan_faskes(pasien_df, riwayat_df):
    st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN - FASKES</h2>", unsafe_allow_html=True)
    
    faskes_menu = st.sidebar.selectbox("Menu Faskes", [
        "📥 Input Tindakan",
        "📬 Tanggapi Sanggahan"
    ])
    
    if faskes_menu == "📥 Input Tindakan":
        # ... (salin logika input tindakan dari apps.py asli)
        pass
    elif faskes_menu == "📬 Tanggapi Sanggahan":
        # ... (salin logika tanggapi sanggahan dari apps.py asli)
        pass
