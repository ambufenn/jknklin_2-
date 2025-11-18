import streamlit as st
import pandas as pd
import os
from model import load_model
from handler import get_response

# ---------- SESSION ----------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="JKNKLIN", layout="centered")

# ---------- HEADER ----------
st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN</h2>", unsafe_allow_html=True)
st.markdown("### Selamat Datang, **Budi Santoso**")
st.caption("No. Peserta: 000123456789")

# ---------- INDEKS KEANDALAN ----------
st.markdown("""
<div style="background:#F2FBF7; border:1px solid #D9F0E4; padding:10px; border-radius:8px; margin:1rem 0;">
<b>Indeks Keandalan:</b> <span style="color:#007F3D;">89/100</span><br>
<i>Akses Anda: Sehat & Transparan</i>
</div>
""", unsafe_allow_html=True)

# ---------- MENU DROPDOWN ----------
menu = st.selectbox("Pilih Fitur", [
    "🗂️ Lihat Riwayat Layanan",
    "📊 Bandingkan Tarif & Tindakan",
    "💬 Kirim Masukan / Sanggahan",
    "🤖 Chatbot Bantuan"
])

# ---------- FITUR: RIWAYAT ----------
if menu == "🗂️ Lihat Riwayat Layanan":
    path = os.path.join("data", "riwayat_budi.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if "Status" in df.columns:
                def color_status(val):
                    colors = {"Terverifikasi": "#D4EDDA", "Dalam Review": "#D1ECF1", "Catatan Ditambahkan": "#FFF3CD"}
                    return f"background-color: {colors.get(val, 'white')}"
                st.dataframe(df.style.applymap(color_status, subset=["Status"]))
            else:
                st.dataframe(df)
        except Exception as e:
            st.error("Gagal membaca file riwayat.")
    else:
        st.warning("File `data/riwayat_budi.csv` tidak ditemukan.")

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
        col3.warning("⚠️ Perlu Tinjauan") if result["is_suspicious"] else col3.success("✅ Wajar")
        
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
        st.success("✅ Sanggahan Anda telah dikirim! Nomor tiket: FC-2025-11451")

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
        except Exception as e:
            st.error("Maaf, sedang ada gangguan teknis.")
