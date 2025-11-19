# apps.py 
import streamlit as st
import pandas as pd
import os
from model import load_model
from handler import get_response, analisis_sanggahan_nlp

# ---------- SESSION ----------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="JKNKLIN", layout="wide")

# ---------- LOAD DATA ----------
@st.cache_data
def load_all_data():
    pasien_path = os.path.join("data", "pasien.csv")
    riwayat_path = os.path.join("data", "riwayat_kunjungan.csv")
    
    pasien = pd.read_csv(pasien_path) if os.path.exists(pasien_path) else pd.DataFrame({
        "user_id": [1], "nama": ["Budi Santoso"], "no_peserta": ["000123456789"], "indeks_keandalan": [89]
    })
    
    if os.path.exists(riwayat_path):
        riwayat = pd.read_csv(riwayat_path)
    else:
        riwayat = pd.DataFrame({
            "user_id": [1],
            "Fasilitas": ["RS Mitra Sehat"],
            "Tanggal": ["2023-05-15"],
            "Layanan": ["Pemeriksaan Umum"],
            "Status": ["Terverifikasi"],
            "Diagnosis": ["ISPA"],
            "Klaim": [800000]
        })
    
    required_columns = {
        "tindakan_dilakukan": True,
        "verifikasi_bpjs": True,
        "detail_tindakan": "Pemeriksaan dokter: Rp100.000",
        "sanggahan_pasien": "",
        "bukti_pasien": "",
        "respons_faskes": "",
        "bukti_faskes": "",
        "status_sanggahan": "",
        "kategori_sanggahan": "Lainnya",
        "ringkasan_sanggahan": ""
    }
    
    for col, default_val in required_columns.items():
        if col not in riwayat.columns:
            riwayat[col] = default_val
    
    if "Tanggal" in riwayat.columns:
        riwayat["Tanggal"] = pd.to_datetime(riwayat["Tanggal"], errors="coerce")
    
    return pasien, riwayat

if "riwayat_df" not in st.session_state:
    _, riwayat = load_all_data()
    st.session_state.riwayat_df = riwayat
if "pasien_df" not in st.session_state:
    pasien, _ = load_all_data()
    st.session_state.pasien_df = pasien

pasien_df = st.session_state.pasien_df
riwayat_df = st.session_state.riwayat_df

# ---------- IMPORT UTILS ----------
from pasien_utils import tampilkan_pasien
from faskes_utils import tampilkan_faskes
from bpjs_utils import tampilkan_bpjs

# ---------- SIDEBAR: PILIH PERAN ----------
st.sidebar.title("🔐 Pilih Peran")
role = st.sidebar.selectbox("Peran", ["pasien", "faskes", "bpjs"])

# ---------- ROUTING PERAN ----------
if role == "pasien":
    tampilkan_pasien(pasien_df, riwayat_df)
elif role == "faskes":
    tampilkan_faskes(pasien_df, riwayat_df)
elif role == "bpjs":
    tampilkan_bpjs(pasien_df, riwayat_df)
