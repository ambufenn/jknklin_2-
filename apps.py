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
        "Layanan": ["Pemeriksaan Umum"], "Status": ["Terverifikasi"], "Diagnosis": ["ISPA"], "Klaim": [800000],
        "tindakan_dilakukan": [True],
        "verifikasi_bpjs": [True],
        "detail_tindakan": ["Pemeriksaan dokter: Rp100.000"],
        "sanggahan_pasien": [""],
        "bukti_faskes": [""],
        "status_sanggahan": [""]
    })
    
    if "Tanggal" in riwayat.columns:
        riwayat["Tanggal"] = pd.to_datetime(riwayat["Tanggal"], errors="coerce")
    
    return pasien, riwayat

# Muat data
if "riwayat_df" not in st.session_state:
    _, riwayat = load_all_data()
    st.session_state.riwayat_df = riwayat
if "pasien_df" not in st.session_state:
    pasien, _ = load_all_data()
    st.session_state.pasien_df = pasien

pasien_df = st.session_state.pasien_df
riwayat_df = st.session_state.riwayat_df

# ---------- SIDEBAR: PILIH PERAN ----------
st.sidebar.title("🔐 Pilih Peran")
role = st.sidebar.selectbox("Peran", ["pasien", "faskes", "bpjs"])

# ---------- LOGIKA PERAN: PASIEN ----------
if role == "pasien":
    st.sidebar.title("👤 Pilih Peserta")
    user_options = {row["user_id"]: f"{row['nama']} (ID: {row['user_id']})" for _, row in pasien_df.iterrows()}
    selected_user_id = st.sidebar.selectbox("Peserta JKN", list(user_options.keys()), format_func=lambda x: user_options[x])
    user_data = pasien_df[pasien_df["user_id"] == selected_user_id].iloc[0]
    user_riwayat = riwayat_df[riwayat_df["user_id"] == selected_user_id]

    st.sidebar.title("🧭 Navigasi")
    menu = st.sidebar.selectbox("Pilih Fitur", [
        "🗂️ Lihat Riwayat Layanan",
        "📊 Bandingkan Tarif & Tindakan",
        "💬 Kirim Masukan / Sanggahan",
        "🤖 Chatbot Bantuan"
    ])

    st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN</h2>", unsafe_allow_html=True)
    st.markdown(f"### Selamat Datang, **{user_data['nama']}**")
    st.caption(f"No. Peserta: **{user_data['no_peserta']}**")

    indeks = int(user_data["indeks_keandalan"])
    warna = "#007F3D" if indeks >= 85 else "#FFA500" if indeks >= 70 else "#D32F2F"
    status = "Sehat & Transparan" if indeks >= 85 else "Perlu Pemantauan" if indeks >= 70 else "Berisiko"
    st.markdown(f"""
    <div style="background:#F2FBF7; border:1px solid #D9F0E4; padding:10px; border-radius:8px; margin:1rem 0;">
    <b>Indeks Keandalan:</b> <span style="color:{warna};">{indeks}/100</span><br>
    <i>Akses Anda: {status}</i>
    </div>
    """, unsafe_allow_html=True)

    if menu == "🗂️ Lihat Riwayat Layanan":
        if user_riwayat.empty:
            st.info("Belum ada riwayat kunjungan.")
        else:
            cols_to_show = ["Fasilitas", "Tanggal", "Layanan", "Status"]
            if "tindakan_dilakukan" in user_riwayat.columns:
                cols_to_show.append("tindakan_dilakukan")
                user_riwayat["tindakan_dilakukan"] = user_riwayat["tindakan_dilakukan"].map({True: "✅ Dilakukan", False: "❌ Tidak"})
            df_show = user_riwayat[cols_to_show].copy()
            
            def color_status(val):
                if val in ["✅ Dilakukan", "❌ Tidak"]:
                    return ""
                colors = {"Terverifikasi": "#D4EDDA", "Dalam Review": "#D1ECF1", "Catatan Ditambahkan": "#FFF3CD"}
                return f"background-color: {colors.get(val, 'white')}"
            
            st.dataframe(df_show.style.applymap(color_status, subset=["Status"]))
            
            st.markdown("### 📋 Detail Tindakan & Sanggahan")
            for idx, row in user_riwayat.iterrows():
                with st.expander(f"{row['Tanggal'].strftime('%d %b %Y')} - {row['Layanan']}"):
                    if "detail_tindakan" in row and pd.notna(row["detail_tindakan"]):
                        st.write("**Tindakan:**")
                        st.text(row["detail_tindakan"])
                    # Tampilkan status sanggahan
                    if row.get("status_sanggahan") == "direspons":
                        st.success("✅ Sanggahan telah direspons oleh faskes.")
                        if row.get("bukti_faskes"):
                            st.write("**Bukti dari Faskes:**")
                            st.text(row["bukti_faskes"])
                    elif row.get("sanggahan_pasien"):
                        st.warning("⚠️ Sanggahan Anda sedang diproses.")
                    else:
                        st.info("Tidak ada sanggahan.")
        st.markdown("<center><a href='#' style='color:#0A8F5B;'>Lihat Semua Riwayat</a></center>", unsafe_allow_html=True)

    elif menu == "💬 Kirim Masukan / Sanggahan":
        st.markdown("### 📝 Sanggah Tindakan yang Tidak Dilakukan")
        # Hanya tampilkan klaim yang tindakan_dilakukan=False atau belum diverifikasi
        klaim_sanggah = user_riwayat[
            (user_riwayat.get("tindakan_dilakukan", True) == False) | 
            (user_riwayat.get("verifikasi_bpjs", True) == False)
        ]
        if klaim_sanggah.empty:
            st.info("Tidak ada tindakan yang bisa disanggah.")
        else:
            for idx, row in klaim_sanggah.iterrows():
                with st.expander(f"{row['Layanan']} - {row['Diagnosis']}"):
                    if not row.get("sanggahan_pasien"):
                        sanggahan = st.text_area("Jelaskan tindakan yang tidak dilakukan", key=f"sanggah_{idx}")
                        if st.button("Kirim Sanggahan", key=f"btn_sanggah_{idx}"):
                            riwayat_df.at[riwayat_df.index[riwayat_df['user_id'] == selected_user_id].tolist()[0] + idx, "sanggahan_pasien"] = sanggahan
                            riwayat_df.at[riwayat_df.index[riwayat_df['user_id'] == selected_user_id].tolist()[0] + idx, "status_sanggahan"] = "menunggu"
                            st.session_state.riwayat_df = riwayat_df
                            st.success("Sanggahan dikirim!")
                    else:
                        st.warning(f"Sanggahan sudah dikirim: {row['sanggahan_pasien']}")

    # Fitur lainnya tetap sama (Bandingkan Tarif, Chatbot)
    elif menu == "📊 Bandingkan Tarif & Tindakan":
        # ... (kode Anda tetap sama)
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

    elif menu == "🤖 Chatbot Bantuan":
        st.markdown("### FairCare Assistant")
        model = load_model()
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

# ---------- LOGIKA PERAN: FASKES ----------
elif role == "faskes":
    st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN - FASKES</h2>", unsafe_allow_html=True)
    
    # Menu Faskes
    faskes_menu = st.sidebar.selectbox("Menu Faskes", [
        "📥 Input Tindakan",
        "📬 Tanggapi Sanggahan"
    ])
    
    if faskes_menu == "📥 Input Tindakan":
        st.info("📝 Input Detail Tindakan ke Pasien")
        pasien_list = pasien_df
        selected_pasien = st.selectbox("Pilih Pasien", pasien_list["user_id"], format_func=lambda x: pasien_list[pasien_list["user_id"]==x]["nama"].iloc[0])
        
        with st.form("input_tindakan_detail"):
            diagnosis = st.selectbox("Diagnosis", ["ISPA", "Diare", "Hipertensi", "Diabetes", "Fraktur Tulang"])
            layanan_utama = st.text_input("Layanan Utama", value="Pemeriksaan Umum")
            num_items = st.number_input("Jumlah Item Tindakan", min_value=1, max_value=10, value=3)
            tindakan_list = []
            for i in range(int(num_items)):
                col1, col2 = st.columns(2)
                with col1:
                    tindakan = st.text_input(f"Tindakan {i+1}", key=f"tindakan_{i}")
                with col2:
                    biaya = st.number_input(f"Biaya (Rp)", min_value=0, key=f"biaya_{i}")
                if tindakan and biaya > 0:
                    tindakan_list.append(f"{tindakan}: Rp{biaya:,}".replace(",", "."))
            
            klaim_total = sum(int(b.split("Rp")[-1].replace(".", "")) for b in tindakan_list) if tindakan_list else 0
            st.success(f"**Total Klaim: Rp{klaim_total:,}".replace(",", ".") + "**")
            tindakan_dilakukan = st.checkbox("Tindakan benar-benar dilakukan", value=True)
            submit = st.form_submit_button("Simpan Tindakan")
        
        if submit:
            detail_str = "\n".join(tindakan_list) if tindakan_list else "Tidak ada detail"
            new_row = {
                "user_id": selected_pasien,
                "Fasilitas": "RS Anda",
                "Tanggal": pd.Timestamp.now().date(),
                "Layanan": layanan_utama,
                "Status": "Dalam Review",
                "Diagnosis": diagnosis,
                "Klaim": klaim_total,
                "tindakan_dilakukan": tindakan_dilakukan,
                "verifikasi_bpjs": False,
                "detail_tindakan": detail_str,
                "sanggahan_pasien": "",
                "bukti_faskes": "",
                "status_sanggahan": ""
            }
            st.session_state.riwayat_df = pd.concat([riwayat_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success("✅ Detail tindakan berhasil disimpan!")

    elif faskes_menu == "📬 Tanggapi Sanggahan":
        st.markdown("### 📬 Sanggahan dari Pasien")
        # Filter hanya riwayat dengan sanggahan menunggu
        sanggahan_menunggu = riwayat_df[riwayat_df["status_sanggahan"] == "menunggu"]
        if sanggahan_menunggu.empty:
            st.success("Tidak ada sanggahan yang perlu ditanggapi.")
        else:
            for idx, row in sanggahan_menunggu.iterrows():
                pasien_nama = pasien_df[pasien_df["user_id"] == row["user_id"]]["nama"].iloc[0]
                with st.expander(f"Sanggahan oleh {pasien_nama} - {row['Layanan']}"):
                    st.write(f"**Diagnosis**: {row['Diagnosis']}")
                    st.write(f"**Sanggahan**: {row['sanggahan_pasien']}")
                    st.write("**Upload Bukti Respons**")
                    st.caption("📸 Foto harus menunjukkan jam & tanggal (misal: hasil TTV di layar monitor)")
                    bukti_file = st.file_uploader("Upload Bukti (Foto)", type=["jpg", "png"], key=f"bukti_{idx}")
                    keterangan = st.text_area("Keterangan Tambahan", key=f"ket_{idx}")
                    if st.button("Kirim Respons", key=f"res_{idx}"):
                        if bukti_file:
                            # Simulasi: simpan nama file
                            bukti_nama = f"{bukti_file.name} ({pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')})"
                            riwayat_df.at[idx, "bukti_faskes"] = bukti_nama
                        riwayat_df.at[idx, "status_sanggahan"] = "direspons"
                        st.session_state.riwayat_df = riwayat_df
                        st.success("Respons sanggahan dikirim!")

# ---------- LOGIKA PERAN: BPJS ----------
elif role == "bpjs":
    st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN - BPJS</h2>", unsafe_allow_html=True)
    st.info("Fitur Verifikasi Klaim & Analisis Kecurangan")
    
    if "verifikasi_bpjs" in riwayat_df.columns:
        klaim_belum = riwayat_df[riwayat_df["verifikasi_bpjs"] == False]
    else:
        klaim_belum = riwayat_df
    
    if klaim_belum.empty:
        st.success("✅ Semua klaim sudah diverifikasi.")
    else:
        for idx, row in klaim_belum.iterrows():
            with st.expander(f"Klaim ID {idx} - {row['Diagnosis']}"):
                st.write(f"**Pasien**: {pasien_df[pasien_df['user_id'] == row['user_id']]['nama'].iloc[0]}")
                st.write(f"**Fasilitas**: {row['Fasilitas']}")
                st.write(f"**Layanan**: {row['Layanan']}")
                if "detail_tindakan" in row and pd.notna(row["detail_tindakan"]):
                    st.write("**Detail Tindakan:**")
                    st.text(row["detail_tindakan"])
                if row.get("sanggahan_pasien"):
                    st.warning(f"**Sanggahan Pasien**: {row['sanggahan_pasien']}")
                    if row.get("bukti_faskes"):
                        st.success(f"**Bukti Faskes**: {row['bukti_faskes']}")
                st.write(f"**Dilakukan?**: {'✅ Ya' if row.get('tindakan_dilakukan', True) else '❌ Tidak'}")
                verif = st.checkbox("Verifikasi Klaim", key=f"verif_{idx}")
                if verif:
                    riwayat_df.at[idx, "verifikasi_bpjs"] = True
                    st.session_state.riwayat_df = riwayat_df
                    st.success("Klaim diverifikasi!")
