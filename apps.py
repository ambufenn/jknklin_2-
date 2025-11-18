import streamlit as st
import pandas as pd
import os
from model import load_model
from handler import get_response

# ---------- SESSION STATE ----------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="JKNKLIN", layout="wide")

# ---------- LOAD RIWAYAT (AMAN) ----------
@st.cache_data
def load_visit_history():
    path = os.path.join("data", "riwayat_budi.csv")
    if not os.path.exists(path):
        return pd.DataFrame({
            "Fasilitas": ["RS Mitra Sehat"],
            "Tanggal": ["2023-05-15"],
            "Layanan": ["Pemeriksaan Umum"],
            "Status": ["Terverifikasi"]
        })
    df = pd.read_csv(path)
    if "Tanggal" in df.columns:
        df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    else:
        df["Tanggal"] = pd.to_datetime("2023-01-01")
    return df

# ---------- HEADER (1 PASIEN: BUDI) ----------
st.markdown("""
    <h2 style='color:#0A8F5B; text-align:center;'>JKNKLIN</h2>
""", unsafe_allow_html=True)

st.markdown("""
    <h3 style='color:#007F3D;'>Selamat Datang, <b>Budi Santoso</b></h3>
    <p>No. Peserta: <b>000123456789</b></p>
""", unsafe_allow_html=True)

# ---------- INFO PANEL ----------
st.markdown("""
<div style="border:1px solid #D9F0E4; background-color:#F2FBF7; padding:10px; border-radius:8px; margin-bottom:1rem;">
<b>Indeks Keandalan:</b> <span style="color:#007F3D;">89/100</span><br>
<i>Akses Anda: Sehat & Transparan</i>
</div>
""", unsafe_allow_html=True)

st.success("✅ **Transparansi AI** — Sistem tidak menemukan kejanggalan dalam layanan terakhir Anda.")
st.markdown("[Pelajari lebih lanjut ›](#)")

# ---------- DROPDOWN FITUR ----------
menu = st.selectbox(
    "Pilih Fitur",
    ["🗂️ Lihat Riwayat Layanan", "📊 Bandingkan Tarif & Tindakan", "💬 Kirim Masukan / Sanggahan", "🤖 Chatbot Bantuan"]
)

# ---------- LOAD DATA RIWAYAT (untuk semua fitur) ----------
riwayat_df = load_visit_history()

# ---------- FITUR: RIWAYAT ----------
if menu == "🗂️ Lihat Riwayat Layanan":
    st.markdown("### 🏥 Riwayat Kunjungan Terakhir")
    df_show = riwayat_df[["Fasilitas", "Tanggal", "Layanan", "Status"]].copy()
    
    def status_color(status):
        color_map = {
            "Terverifikasi": "#D4EDDA",
            "Dalam Review": "#D1ECF1",
            "Catatan Ditambahkan": "#FFF3CD"
        }
        return f"background-color: {color_map.get(status, 'white')}"
    
    st.dataframe(df_show.style.apply(lambda s: [status_color(v) for v in s], subset=["Status"]))
    st.markdown("<center><a href='#' style='color:#0A8F5B;'>Lihat Semua Riwayat</a></center>", unsafe_allow_html=True)

# ---------- FITUR: BANDINGKAN TARIF ----------
elif menu == "📊 Bandingkan Tarif & Tindakan":
    st.markdown("### 📊 Bandingkan Tarif & Tindakan")
    with st.form("claim_form"):
        diagnosis = st.selectbox("Diagnosis", ["ISPA", "Diare", "Hipertensi", "Diabetes", "Fraktur Tulang", "Lainnya"])
        if diagnosis == "Lainnya":
            diagnosis = st.text_input("Diagnosis Lain")
        klaim = st.number_input("Nilai Klaim (Rp)", min_value=0, value=1000000, step=100000)
        hari = st.number_input("Lama Rawat Inap (hari)", min_value=0, max_value=30, value=1)
        rs = st.text_input("Nama Fasilitas", value="RS Umum Daerah")
        submit = st.form_submit_button("Analisis")
    
    if submit and diagnosis:
        from fairness_engine import analyze_claim, generate_appeal_suggestion
        hasil = analyze_claim(diagnosis, klaim, rs, hari)
        
        st.markdown("#### 📌 Hasil Analisis")
        c1, c2, c3 = st.columns(3)
        c1.metric("Klaim RS", f"Rp{hasil['claimed_amount']:,}".replace(",", "."))
        c2.metric("Tarif BPJS", f"Rp{hasil['tarif_bpjs']:,}".replace(",", "."))
        c3.warning("⚠️ Perlu Tinjauan") if hasil["is_suspicious"] else c3.success("✅ Wajar")
        
        if hasil["warning"]:
            st.markdown("#### ⚠️ Peringatan")
            for w in hasil["warning"]:
                st.warning(w)
        
        st.markdown("#### 💬 Saran Sanggahan")
        st.info(generate_appeal_suggestion(hasil))

# ---------- FITUR: SANGGAHAN ----------
elif menu == "💬 Kirim Masukan / Sanggahan":
    st.markdown("### 💬 Kirim Sanggahan atau Masukan")
    with st.form("sanggah_form"):
        st.text_area("Jelaskan sanggahan Anda", height=150)
        st.file_uploader("Dokumen Pendukung (opsional)", type=["pdf", "jpg", "png"])
        kirim = st.form_submit_button("Kirim Sanggahan")
    if kirim:
        st.success("✅ Sanggahan Anda telah dikirim! Nomor tiket: FC-2025-11451")

# ---------- FITUR: CHATBOT ----------
elif menu == "🤖 Chatbot Bantuan":
    st.markdown("### 🤖 FairCare Assistant")
    
    @st.cache_resource
    def init_model():
        return load_model()
    
    model = init_model()
    
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Tanyakan sesuatu tentang layanan JKN..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        try:
            response = get_response(prompt, model)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
        except Exception:
            err = "Maaf, sedang ada gangguan teknis. Coba lagi nanti."
            st.session_state.chat_messages.append({"role": "assistant", "content": err})
            with st.chat_message("assistant"):
                st.error(err)
