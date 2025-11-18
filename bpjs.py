# bpjs.py
import streamlit as st
import pandas as pd
from fairness_engine import INA_CBGs

def tampilkan_bpjs(pasien_df, riwayat_df):
    st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN - BPJS</h2>", unsafe_allow_html=True)
    st.info("Fitur Verifikasi Klaim & Analisis Kecurangan")
    
    klaim_belum = riwayat_df[riwayat_df["verifikasi_bpjs"] == False]
    if klaim_belum.empty:
        st.success("✅ Semua klaim sudah diverifikasi.")
    else:
        for idx, row in klaim_belum.iterrows():
            with st.expander(f"Klaim ID {idx} - {row['Diagnosis']}"):
                # ... (salin logika BPJS lengkap dari apps.py asli)
                # termasuk deteksi fraud, highlight AI, dll
                pass
