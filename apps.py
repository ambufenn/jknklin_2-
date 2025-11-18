import streamlit as st
import pandas as pd
from model import load_model
from handler import get_response
import os

# ---------- SESSION STATE ----------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="JKNKLIN", layout="wide")

# ---------- LOAD DATA ----------
@st.cache_data
def load_visit_history():
    path = os.path.join("data", "riwayat_budi.csv")
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["Tanggal"])
    else:
        # fallback dummy
        return pd.DataFrame({
            "Fasilitas": ["RS Mitra Sehat", "Klinik Sejahtera", "RS Cinta Kasih"],
            "Tanggal": ["2023-05-15", "2023-04-02", "2023-03-10"],
            "Layanan": ["Pemeriksaan Umum", "Konsultasi Spesialis", "Rawat Inap"],
            "Status": ["Terverifikasi", "Dalam Review", "Catatan Ditambahkan"],
            "Diagnosis": ["ISPA", "Hipertensi", "Fraktur Tulang"],
            "Klaim": [800000, 1100000, 3400000]
        })

# ---------- HEADER (HARDCODED UNTUK 1 PASIEN DEMO) ----------
st.markdown("""
    <h2 style='color:#0A8F5B; text-align:center;'>JKNKLIN</h2>
""", unsafe_allow_html=True)

st.markdown("""
    <h3 style='color:#007F3D;'>Selamat Datang, <b>Budi Santoso</b></h3>
    <p>No. Peserta: <b>000123456789</b></p>
""", unsafe_allow_html=True)

# ---------- STATIC INFO PANEL ----------
st.markdown("""
<div style="border:1px solid #D9F0E4; background-color:#F2FBF7; padding:10px; border-radius:8px; margin-bottom:1rem;">
<b>Indeks Keandalan:</b> <span style="color:#007F3D;">89/100</span><br>
<i>Akses Anda: Sehat & Transparan</i>
</div>
""", unsafe_allow_html=True)

st.success("✅ **Transparansi AI** — Sistem tidak menemukan kejanggalan dalam layanan terakhir Anda.")
st.markdown("[Pelajari lebih lanjut ›](#)")

# ---------- MAIN DROPDOWN MENU (FITUR, BUKAN PASIEN) ----------
menu_options = {
    "🗂️ Lihat Riwayat Layanan": "riwayat",
    "📊 Bandingkan Tarif & Tindakan": "compare",
    "💬 Kirim Masukan / Sanggahan": "appeal",
    "🤖 Chatbot Bantuan": "chat"
}

selected = st.selectbox("Pilih Fitur", list(menu_options.keys()), key="main_menu")
action = menu_options[selected]

# ---------- FUNGSI HALAMAN ----------
def show_riwayat():
    st.markdown("### 🏥 Riwayat Kunjungan Terakhir")
    df = load_visit_history()
    df_display = df[["Fasilitas", "Tanggal", "Layanan", "Status"]].copy()

    def status_color(status):
        color_map = {
            "Terverifikasi": "#D4EDDA",
            "Dalam Review": "#D1ECF1",
            "Catatan Ditambahkan": "#FFF3CD"
        }
        return f"background-color: {color_map.get(status, 'white')}"

    st.dataframe(df_display.style.apply(lambda s: [status_color(v) for v in s], subset=["Status"]))
    st.markdown("<center><a href='#' style='color:#0A8F5B;'>Lihat Semua Riwayat</a></center>", unsafe_allow_html=True)

def show_compare():
    st.markdown("### 📊 Bandingkan Tarif & Tindakan")
    with st.form("claim_analysis_form"):
        diagnosis = st.selectbox("Diagnosis Utama", [
            "ISPA", "Diare", "Hipertensi", "Diabetes", "Fraktur Tulang", "Lainnya"
        ])
        if diagnosis == "Lainnya":
            diagnosis = st.text_input("Diagnosis Lain")
        claimed_amount = st.number_input("Nilai Klaim (Rp)", min_value=0, value=1000000, step=100000)
        days = st.number_input("Lama Rawat Inap (hari)", min_value=0, max_value=30, value=1)
        facility = st.text_input("Nama Fasilitas", value="RS Umum Daerah")
        submitted = st.form_submit_button("Analisis Klaim")

    if submitted and diagnosis:
        from fairness_engine import analyze_claim, generate_appeal_suggestion
        result = analyze_claim(diagnosis, claimed_amount, facility, days)

        st.markdown("#### 📌 Hasil Analisis")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Klaim RS", f"Rp{result['claimed_amount']:,}".replace(",", "."))
        with col_b:
            st.metric("Tarif BPJS", f"Rp{result['tarif_bpjs']:,}".replace(",", "."))
        with col_c:
            st.warning("⚠️ Perlu Tinjauan") if result["is_suspicious"] else st.success("✅ Wajar")

        if result["warning"]:
            st.markdown("#### ⚠️ Peringatan")
            for w in result["warning"]:
                st.warning(w)

        st.markdown("#### 💬 Saran Sanggahan")
        st.info(generate_appeal_suggestion(result))

def show_appeal():
    st.markdown("### 💬 Kirim Sanggahan atau Masukan")
    with st.form("appeal_form"):
        st.text_area("Jelaskan sanggahan Anda", height=150,
                     placeholder="Contoh: Klaim rawat inap ISPA selama 5 hari terlalu mahal...")
        st.file_uploader("Dokumen Pendukung (opsional)", type=["pdf", "jpg", "png"])
        submitted = st.form_submit_button("Kirim Sanggahan")
    if submitted:
        st.success("✅ Sanggahan Anda telah dikirim! Nomor tiket: FC-2025-11451")

def show_chat():
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
        except Exception as e:
            msg = "Maaf, sedang ada gangguan teknis. Coba lagi nanti."
            st.session_state.chat_messages.append({"role": "assistant", "content": msg})
            with st.chat_message("assistant"):
                st.error(msg)

# ---------- RENDER SESUAI PILIHAN MENU ----------
if action == "riwayat":
    show_riwayat()
elif action == "compare":
    show_compare()
elif action == "appeal":
    show_appeal()
elif action == "chat":
    show_chat()
