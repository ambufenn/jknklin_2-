import streamlit as st
import pandas as pd
import os
from model import load_model
from handler import get_response

# ---------- SESSION ----------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "current_role" not in st.session_state:
    st.session_state.current_role = "pasien"

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="JKNKLIN", layout="wide")

# ---------- LOAD DATA ----------
@st.cache_data(ttl=300)  # refresh tiap 5 menit
def load_data():
    pengguna = pd.read_csv("data/pengguna.csv") if os.path.exists("data/pengguna.csv") else pd.DataFrame({
        "user_id": [1, 2, 3],
        "nama": ["Budi Santoso", "RS Mitra Sehat", "Admin BPJS"],
        "peran": ["pasien", "faskes", "bpjs"],
        "no_identitas": ["000123456789", "RS001", "BPJS2025"]
    })
    
    riwayat = pd.read_csv("data/riwayat_klaim.csv") if os.path.exists("data/riwayat_klaim.csv") else pd.DataFrame({
        "klaim_id": [1],
        "user_id_pasien": [1],
        "user_id_faskes": [2],
        "tanggal": ["2023-05-15"],
        "diagnosis": ["ISPA"],
        "tindakan": ["Pemeriksaan Umum"],
        "klaim": [800000],
        "tarif_bpjs": [850000],
        "tindakan_dilakukan": [True],
        "verifikasi_bpjs": [True],
        "catatan_pasien": [""]
    })
    riwayat["tanggal"] = pd.to_datetime(riwayat["tanggal"], errors="coerce")
    return pengguna, riwayat

# Simpan data ke session untuk bisa diubah
if "pengguna_df" not in st.session_state or "riwayat_df" not in st.session_state:
    pengguna, riwayat = load_data()
    st.session_state.pengguna_df = pengguna
    st.session_state.riwayat_df = riwayat

# ---------- SIDEBAR: PILIH PERAN ----------
st.sidebar.title("🔐 Pilih Peran")
role = st.sidebar.selectbox("Peran", ["pasien", "faskes", "bpjs"], key="role_selector")
st.session_state.current_role = role

# ---------- SIDEBAR: PILIH PENGGUNA SESUAI PERAN ----------
pengguna = st.session_state.pengguna_df
riwayat = st.session_state.riwayat_df

pengguna_peran = pengguna[pengguna["peran"] == role]
if pengguna_peran.empty:
    st.sidebar.error("Tidak ada pengguna untuk peran ini.")
    st.stop()

user_options = {row["user_id"]: f"{row['nama']} ({row['no_identitas']})" for _, row in pengguna_peran.iterrows()}
selected_user_id = st.sidebar.selectbox("Pengguna", list(user_options.keys()), format_func=lambda x: user_options[x])

# Dapatkan data pengguna aktif
user_data = pengguna[pengguna["user_id"] == selected_user_id].iloc[0]

# ---------- HEADER ----------
st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN</h2>", unsafe_allow_html=True)
st.markdown(f"### Peran: **{role.upper()}** | Pengguna: **{user_data['nama']}**")

# ---------- MENU SESUAI PERAN ----------
if role == "pasien":
    menu = st.sidebar.selectbox("Menu", ["🗂️ Riwayat Klaim", "💬 Sanggah Klaim", "🤖 Chatbot Bantuan"])
elif role == "faskes":
    menu = st.sidebar.selectbox("Menu", ["📥 Input Tindakan", "📋 Daftar Klaim", "📊 Analisis Klaim"])
else:  # bpjs
    menu = st.sidebar.selectbox("Menu", ["🔍 Verifikasi Klaim", "📈 Dashboard Kecurangan", "⚙️ Kelola Tarif"])

# ---------- FITUR: PASIEN ----------
if role == "pasien":
    if menu == "🗂️ Riwayat Klaim":
        klaim_pasien = riwayat[riwayat["user_id_pasien"] == selected_user_id]
        if klaim_pasien.empty:
            st.info("Belum ada riwayat klaim.")
        else:
            df_show = klaim_pasien[["tanggal", "diagnosis", "tindakan", "klaim", "tindakan_dilakukan", "verifikasi_bpjs"]].copy()
            df_show["status_tindakan"] = df_show["tindakan_dilakukan"].map({True: "✅ Dilakukan", False: "❌ Tidak Dilakukan"})
            df_show["status_verif"] = df_show["verifikasi_bpjs"].map({True: "🟢 Terverifikasi", False: "🟡 Menunggu"})
            st.dataframe(df_show[["tanggal", "diagnosis", "tindakan", "status_tindakan", "status_verif", "klaim"]])
    
    elif menu == "💬 Sanggah Klaim":
        st.markdown("### Sanggah Klaim yang Tidak Sesuai")
        klaim_belum_verif = riwayat[(riwayat["user_id_pasien"] == selected_user_id) & (~riwayat["verifikasi_bpjs"])]
        if klaim_belum_verif.empty:
            st.success("✅ Semua klaim Anda sudah diverifikasi.")
        else:
            for _, row in klaim_belum_verif.iterrows():
                with st.expander(f"Klaim ID {row['klaim_id']}: {row['diagnosis']} - Rp{row['klaim']:,}".replace(",", ".")):
                    st.write(f"**Tindakan**: {row['tindakan']}")
                    st.write(f"**Dilakukan?**: {'✅ Ya' if row['tindakan_dilakukan'] else '❌ Tidak'}")
                    if not row["tindakan_dilakukan"]:
                        st.warning("Anda sudah menyatakan tindakan tidak dilakukan.")
                    else:
                        alasan = st.text_area("Jelaskan sanggahan", key=f"sanggah_{row['klaim_id']}")
                        if st.button("Kirim Sanggahan", key=f"btn_{row['klaim_id']}"):
                            # Simpan ke data (untuk demo, hanya update session)
                            riwayat.loc[riwayat["klaim_id"] == row["klaim_id"], "tindakan_dilakukan"] = False
                            riwayat.loc[riwayat["klaim_id"] == row["klaim_id"], "catatan_pasien"] = alasan
                            st.session_state.riwayat_df = riwayat
                            st.success("Sanggahan dikirim! Menunggu verifikasi BPJS.")
    
    elif menu == "🤖 Chatbot Bantuan":
        st.markdown("### FairCare Assistant")
        model = load_model()
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        if prompt := st.chat_input("Tanya tentang JKN..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            try:
                response = get_response(prompt, model)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
            except Exception:
                st.error("Gangguan teknis.")

# ---------- FITUR: FASKES ----------
elif role == "faskes":
    if menu == "📥 Input Tindakan":
        st.markdown("### Input Klaim Baru")
        pasien_list = pengguna[pengguna["peran"] == "pasien"]
        pasien_id = st.selectbox("Pasien", pasien_list["user_id"], format_func=lambda x: pasien_list[pasien_list["user_id"]==x]["nama"].iloc[0])
        diagnosis = st.selectbox("Diagnosis", ["ISPA", "Diare", "Hipertensi", "Diabetes", "Fraktur Tulang"])
        tindakan = st.text_input("Tindakan yang Dilakukan")
        klaim = st.number_input("Nilai Klaim (Rp)", min_value=0, value=1000000)
        if st.button("Simpan Klaim"):
            new_id = riwayat["klaim_id"].max() + 1 if not riwayat.empty else 1
            new_row = {
                "klaim_id": new_id,
                "user_id_pasien": pasien_id,
                "user_id_faskes": selected_user_id,
                "tanggal": pd.Timestamp.now().date(),
                "diagnosis": diagnosis,
                "tindakan": tindakan,
                "klaim": klaim,
                "tarif_bpjs": 850000,  # bisa diambil dari tarif_ina_cbgs.csv
                "tindakan_dilakukan": True,
                "verifikasi_bpjs": False,
                "catatan_pasien": ""
            }
            st.session_state.riwayat_df = pd.concat([riwayat, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Klaim ID {new_id} berhasil disimpan!")
    
    elif menu == "📋 Daftar Klaim":
        klaim_faskes = riwayat[riwayat["user_id_faskes"] == selected_user_id]
        if klaim_faskes.empty:
            st.info("Belum ada klaim.")
        else:
            df_show = klaim_faskes.copy()
            df_show["status"] = df_show["verifikasi_bpjs"].map({True: "✅ Terverifikasi", False: "⏳ Menunggu"})
            st.dataframe(df_show[["klaim_id", "tanggal", "diagnosis", "tindakan", "klaim", "status"]])

# ---------- FITUR: BPJS ----------
else:  # role == "bpjs"
    if menu == "🔍 Verifikasi Klaim":
        klaim_belum_verif = riwayat[~riwayat["verifikasi_bpjs"]]
        if klaim_belum_verif.empty:
            st.success("✅ Semua klaim sudah diverifikasi.")
        else:
            for _, row in klaim_belum_verif.iterrows():
                pasien_nama = pengguna[pengguna["user_id"] == row["user_id_pasien"]]["nama"].iloc[0]
                faskes_nama = pengguna[pengguna["user_id"] == row["user_id_faskes"]]["nama"].iloc[0]
                with st.expander(f"Klaim ID {row['klaim_id']} - {pasien_nama}"):
                    st.write(f"**Faskes**: {faskes_nama}")
                    st.write(f"**Diagnosis**: {row['diagnosis']}")
                    st.write(f"**Tindakan**: {row['tindakan']}")
                    st.write(f"**Klaim**: Rp{row['klaim']:,}".replace(",", "."))
                    st.write(f"**Dilakukan menurut pasien**: {'✅ Ya' if row['tindakan_dilakukan'] else '❌ Tidak'}")
                    if not row["tindakan_dilakukan"]:
                        st.warning(f"Catatan pasien: {row['catatan_pasien']}")
                    status = st.radio("Verifikasi", ["Terverifikasi", "Tolak"], key=f"verif_{row['klaim_id']}")
                    if st.button("Simpan Verifikasi", key=f"save_{row['klaim_id']}"):
                        riwayat.loc[riwayat["klaim_id"] == row["klaim_id"], "verifikasi_bpjs"] = (status == "Terverifikasi")
                        st.session_state.riwayat_df = riwayat
                        st.success("Verifikasi disimpan!")
    
    elif menu == "📈 Dashboard Kecurangan":
        st.markdown("### Indeks Kecurangan Faskes")
        # Hitung klaim ditolak per faskes
        tolak_per_faskes = riwayat[riwayat["verifikasi_bpjs"] == False].groupby("user_id_faskes").size()
        faskes_list = pengguna[pengguna["peran"] == "faskes"]
        result = []
        for _, faskes in faskes_list.iterrows():
            tolak = tolak_per_faskes.get(faskes["user_id"], 0)
            total = len(riwayat[riwayat["user_id_faskes"] == faskes["user_id"]])
            persen = (tolak / total * 100) if total > 0 else 0
            result.append({
                "Faskes": faskes["nama"],
                "Klaim Ditahan": tolak,
                "Total Klaim": total,
                "Indeks Kecurangan": f"{persen:.1f}%"
            })
        st.dataframe(pd.DataFrame(result))

# ---------- SIMPAN PERUBAHAN (untuk demo, tidak persist ke file) ----------
# Di lingkungan nyata, simpan ke database/file setelah setiap perubahan
