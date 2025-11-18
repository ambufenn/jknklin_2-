import streamlit as st
import pandas as pd
import os
from model import load_model
from handler import get_response

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
    
    riwayat = pd.read_csv(riwayat_path) if os.path.exists(riwayat_path) else pd.DataFrame({
        "user_id": [1], "Fasilitas": ["RS Mitra Sehat"], "Tanggal": ["2023-05-15"],
        "Layanan": ["Pemeriksaan Umum"], "Status": ["Terverifikasi"], "Diagnosis": ["ISPA"], "Klaim": [800000]
    })
    
    if "Tanggal" in riwayat.columns:
        riwayat["Tanggal"] = pd.to_datetime(riwayat["Tanggal"], errors="coerce")
    
    return pasien, riwayat

pasien_df, riwayat_df = load_all_data()

# ---------- SIDEBAR: PILIH PASIEN ----------
st.sidebar.title("👤 Pilih Peserta")
user_options = {row["user_id"]: f"{row['nama']} (ID: {row['user_id']})" for _, row in pasien_df.iterrows()}
selected_user_id = st.sidebar.selectbox(
    "Peserta JKN",
    options=list(user_options.keys()),
    format_func=lambda x: user_options[x]
)

# Dapatkan data pasien aktif
user_data = pasien_df[pasien_df["user_id"] == selected_user_id].iloc[0]
user_riwayat = riwayat_df[riwayat_df["user_id"] == selected_user_id]

# ---------- SIDEBAR: MENU FITUR ----------
st.sidebar.title("🧭 Navigasi")
menu = st.sidebar.selectbox("Pilih Fitur", [
    "🗂️ Lihat Riwayat Layanan",
    "📊 Bandingkan Tarif & Tindakan",
    "💬 Kirim Masukan / Sanggahan",
    "🤖 Chatbot Bantuan"
])

# ---------- HEADER (DINAMIS PER PASIEN) ----------
st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN</h2>", unsafe_allow_html=True)
st.markdown(f"### Selamat Datang, **{user_data['nama']}**")
st.caption(f"No. Peserta: **{user_data['no_peserta']}**")

# ---------- INDEKS KEANDALAN DINAMIS ----------
indeks = int(user_data["indeks_keandalan"])
warna = "#007F3D" if indeks >= 85 else "#FFA500" if indeks >= 70 else "#D32F2F"
status = "Sehat & Transparan" if indeks >= 85 else "Perlu Pemantauan" if indeks >= 70 else "Berisiko"

st.markdown(f"""
<div style="background:#F2FBF7; border:1px solid #D9F0E4; padding:10px; border-radius:8px; margin:1rem 0;">
<b>Indeks Keandalan:</b> <span style="color:{warna};">{indeks}/100</span><br>
<i>Akses Anda: {status}</i>
</div>
""", unsafe_allow_html=True)

# ---------- FITUR: RIWAYAT ----------
if menu == "🗂️ Lihat Riwayat Layanan":
    if user_riwayat.empty:
        st.info("Belum ada riwayat kunjungan.")
    else:
        df_show = user_riwayat[["Fasilitas", "Tanggal", "Layanan", "Status"]].copy()
        def color_status(val):
            colors = {"Terverifikasi": "#D4EDDA", "Dalam Review": "#D1ECF1", "Catatan Ditambahkan": "#FFF3CD"}
            return f"background-color: {colors.get(val, 'white')}"
        st.dataframe(df_show.style.applymap(color_status, subset=["Status"]))
    st.markdown("<center><a href='#' style='color:#0A8F5B;'>Lihat Semua Riwayat</a></center>", unsafe_allow_html=True)

# ---------- FITUR: BANDINGKAN TARIF ----------
elif menu == "📊 Bandingkan Tarif & Tindakan":
    with st.form("claim_form"):
        diagnosis = st.selectbox("Diagnosis Utama", ["ISPA", "Diare", "Hipertensi", "Diabetes", "Fraktur Tulang", "Lainnya"])
        if diagnosis == "Lainnya":
            diagnosis = st.text_input("Diagnosis Lain")
        klaim = st.number_input("Nilai Klaim (Rp)", min_value=0, value=1000000, step=100000)
        hari = st.number_input("Lama Rawat Inap (hari)", min_value=0, max_value=30, value=1)
        rs = st.text_input("Nama Fasilitas", value="RS Umum Daerah")
        submit = st.form_submit_button("Analisis Klaim")
    
    if submit and diagnosis:
        from fairness_engine import analyze_claim, generate_appeal_suggestion
        result = analyze_claim(diagnosis, klaim, rs, hari)
        
        st.markdown("#### 📌 Hasil Analisis")
        col1, col2, col3 = st.columns(3)
        col1.metric("Klaim RS", f"Rp{result['claimed_amount']:,}".replace(",", "."))
        col2.metric("Tarif BPJS", f"Rp{result['tarif_bpjs']:,}".replace(",", "."))
        if result["is_suspicious"]:
            col3.warning("⚠️ Perlu Tinjauan")
        else:
            col3.success("✅ Wajar")
        
        if result["warning"]:
            st.markdown("#### ⚠️ Peringatan")
            for w in result["warning"]:
                st.warning(w)
        
        st.markdown("#### 💬 Saran Sanggahan")
        st.info(generate_appeal_suggestion(result))

# ---------- FITUR: SANGGAHAN ----------
elif menu == "💬 Kirim Masukan / Sanggahan":
    st.markdown("### Kirim Sanggahan atau Masukan")
    with st.form("appeal_form"):
        st.text_area("Jelaskan sanggahan Anda", height=150, placeholder="Contoh: Klaim rawat inap ISPA selama 5 hari terlalu mahal...")
        st.file_uploader("Dokumen Pendukung (opsional)", type=["pdf", "jpg", "png"])
        submit = st.form_submit_button("Kirim Sanggahan")
    if submit:
        st.success(f"✅ Sanggahan Anda telah dikirim! Nomor tiket: FC-2025-{selected_user_id}451")

# ---------- FITUR: CHATBOT ----------
elif menu == "🤖 Chatbot Bantuan":
    st.markdown("### FairCare Assistant")
    
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
            st.error("Maaf, sedang ada gangguan teknis.")
