import streamlit as st
import pandas as pd
import os
from model import load_model
from handler import get_response, analisis_sanggahan_nlp  # << TAMBAHAN: import fungsi NLP

# ---------- SESSION ----------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="JKNKLIN", layout="wide")

# ---------- LOAD DATA (DIPERBAIKI) ----------
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
    
    # ---------- TAMBAHKAN SEMUA KOLOM WAJIB ----------
    required_columns = {
        "tindakan_dilakukan": True,
        "verifikasi_bpjs": True,
        "detail_tindakan": "Pemeriksaan dokter: Rp100.000",
        "sanggahan_pasien": "",
        "bukti_pasien": "",
        "respons_faskes": "",
        "bukti_faskes": "",
        "status_sanggahan": "",
        "kategori_sanggahan": "Lainnya",        # << BARU: hasil NLP
        "ringkasan_sanggahan": ""               # << BARU: hasil NLP
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
                        st.write("**Tindakan yang Diberikan:**")
                        st.text(row["detail_tindakan"])
                    
                    if row.get("sanggahan_pasien"):
                        st.warning(f"**Sanggahan Anda:** {row['sanggahan_pasien']}")
                        if row.get("bukti_pasien"):
                            st.write(f"**Bukti Anda:** {row['bukti_pasien']}")
                        # 🔥 HIGHLIGHT AI DI SINI 🔥
                        if row.get("kategori_sanggahan") and row["kategori_sanggahan"] != "Lainnya":
                            st.markdown(
                                f'<span style="background:#E3F2FD; padding:2px 6px; border-radius:4px; font-size:0.9em; color:#1565C0;">'
                                f'🤖 Analisis AI: <b>{row["kategori_sanggahan"]}</b> — {row["ringkasan_sanggahan"]}'
                                f'</span>',
                                unsafe_allow_html=True
                            )
                        if row.get("status_sanggahan") == "direspons":
                            st.success("✅ Faskes telah merespons sanggahan Anda.")
                            st.write(f"**Respons Faskes:** {row.get('respons_faskes', 'Tidak ada keterangan')}")
                            if row.get("bukti_faskes"):
                                st.write("**Bukti dari Faskes:**")
                                st.text(row["bukti_faskes"])
                    else:
                        st.info("Belum ada sanggahan untuk kunjungan ini.")
        st.markdown("<center><a href='#' style='color:#0A8F5B;'>Lihat Semua Riwayat</a></center>", unsafe_allow_html=True)

    # ---------- FITUR SANGGAHAN DENGAN NLP AI ----------
    elif menu == "💬 Kirim Masukan / Sanggahan":
        st.markdown("### 📝 Ajukan Sanggahan untuk Kunjungan Tertentu")
        if user_riwayat.empty:
            st.info("Tidak ada riwayat kunjungan.")
        else:
            with st.form("form_sanggahan"):
                kunjungan_options = {}
                for idx, row in user_riwayat.iterrows():
                    label = f"{row['Tanggal'].strftime('%d %b %Y')} - {row['Layanan']} ({row['Diagnosis']})"
                    kunjungan_options[idx] = label
                selected_kunjungan = st.selectbox("Pilih Kunjungan", list(kunjungan_options.keys()), format_func=lambda x: kunjungan_options[x])
                
                sanggahan_text = st.text_area("Jelaskan sanggahan Anda secara detail", height=150, 
                                            placeholder="Contoh: Tindakan 'Suntik Omeprazole' tidak dilakukan, hanya diberi obat oral.")
                bukti_file = st.file_uploader("Upload Dokumen Pendukung (opsional)", type=["pdf", "jpg", "png"])
                submit = st.form_submit_button("Kirim Sanggahan")
            
            if submit:
                if not sanggahan_text.strip():
                    st.error("Silakan isi sanggahan terlebih dahulu.")
                else:
                    # 🔥 ANALISIS NLP OTOMATIS DENGAN AI 🔥
                    try:
                        model = load_model()
                        hasil_nlp = analisis_sanggahan_nlp(sanggahan_text, model)
                    except:
                        hasil_nlp = {"kategori": "Lainnya", "ringkasan": "Analisis AI gagal"}
                    
                    actual_idx = user_riwayat.loc[selected_kunjungan].name
                    riwayat_df.at[actual_idx, "sanggahan_pasien"] = sanggahan_text
                    riwayat_df.at[actual_idx, "kategori_sanggahan"] = hasil_nlp["kategori"]
                    riwayat_df.at[actual_idx, "ringkasan_sanggahan"] = hasil_nlp["ringkasan"]
                    riwayat_df.at[actual_idx, "status_sanggahan"] = "menunggu"
                    if bukti_file:
                        riwayat_df.at[actual_idx, "bukti_pasien"] = f"{bukti_file.name} ({pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')})"
                    
                    st.session_state.riwayat_df = riwayat_df
                    st.success(f"✅ Sanggahan dikirim! **AI Terdeteksi**: {hasil_nlp['kategori']}")
                    st.rerun()

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
    
    faskes_menu = st.sidebar.selectbox("Menu Faskes", [
        "📥 Input Tindakan",
        "📬 Tanggapi Sanggahan"
    ])
    
    if faskes_menu == "📥 Input Tindakan":
        st.info("📝 Input Detail Tindakan ke Pasien")
        if "Fasilitas" in riwayat_df.columns and not riwayat_df.empty:
            daftar_rs = sorted(riwayat_df["Fasilitas"].dropna().unique())
        else:
            daftar_rs = ["RS Mitra Sehat", "Klinik Sejahtera", "RS Harapan Bunda", "Puskesmas Kota Baru", "RS Cinta Kasih"]
        selected_rs = st.selectbox("Pilih Rumah Sakit / Faskes", daftar_rs)
        pasien_di_rs = riwayat_df[riwayat_df["Fasilitas"] == selected_rs]["user_id"].unique()
        if len(pasien_di_rs) > 0:
            pasien_rs_df = pasien_df[pasien_df["user_id"].isin(pasien_di_rs)]
            pasien_options = {row["user_id"]: row["nama"] for _, row in pasien_rs_df.iterrows()}
        else:
            st.warning(f"Belum ada pasien terdaftar di {selected_rs}. Menampilkan semua pasien.")
            pasien_options = {row["user_id"]: row["nama"] for _, row in pasien_df.iterrows()}
        selected_pasien_id = st.selectbox("Pilih Pasien", list(pasien_options.keys()), format_func=lambda x: pasien_options[x])
        
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
                "user_id": selected_pasien_id,
                "Fasilitas": selected_rs,
                "Tanggal": pd.Timestamp.now().date(),
                "Layanan": layanan_utama,
                "Status": "Dalam Review",
                "Diagnosis": diagnosis,
                "Klaim": klaim_total,
                "tindakan_dilakukan": tindakan_dilakukan,
                "verifikasi_bpjs": False,
                "detail_tindakan": detail_str,
                "sanggahan_pasien": "",
                "bukti_pasien": "",
                "respons_faskes": "",
                "bukti_faskes": "",
                "status_sanggahan": "",
                "kategori_sanggahan": "Lainnya",
                "ringkasan_sanggahan": ""
            }
            st.session_state.riwayat_df = pd.concat([riwayat_df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"✅ Tindakan berhasil disimpan untuk pasien di {selected_rs}!")

    # ---------- FITUR TANGGAPI SANGGAHAN DENGAN HIGHLIGHT AI ----------
    elif faskes_menu == "📬 Tanggapi Sanggahan":
        st.markdown("### 📬 Tanggapi Sanggahan dari Pasien")
        sanggahan_menunggu = riwayat_df[riwayat_df["status_sanggahan"] == "menunggu"]
        if sanggahan_menunggu.empty:
            st.info("✅ Saat ini tidak ada sanggahan yang perlu ditanggapi.")
        else:
            for idx, row in sanggahan_menunggu.iterrows():
                pasien_nama = pasien_df[pasien_df["user_id"] == row["user_id"]]["nama"].iloc[0]
                with st.expander(f"📝 {pasien_nama} - {row['Layanan']} ({row['Tanggal'].strftime('%d %b %Y')})"):
                    st.write(f"**Diagnosis**: {row['Diagnosis']}")
                    st.write(f"**Sanggahan Pasien**: {row['sanggahan_pasien']}")
                    # 🔥 HIGHLIGHT AI UNTUK FASKES 🔥
                    if row.get("kategori_sanggahan") and row["kategori_sanggahan"] != "Lainnya":
                        st.markdown(
                            f'<span style="background:#E8F5E9; padding:2px 6px; border-radius:4px; font-size:0.9em; color:#2E7D32;">'
                            f'🧠 Kategori AI: <b>{row["kategori_sanggahan"]}</b>'
                            f'</span>',
                            unsafe_allow_html=True
                        )
                    if row.get("bukti_pasien"):
                        st.write(f"**Bukti dari Pasien**: {row['bukti_pasien']}")
                    
                    with st.form(f"respons_form_{idx}"):
                        respons_text = st.text_area("Tanggapan Anda*", height=100)
                        bukti_foto = st.file_uploader("Upload Bukti Foto* (wajib)", type=["jpg", "png"], key=f"bukti_{idx}")
                        submit_respons = st.form_submit_button("Kirim Respons")
                    
                    if submit_respons:
                        if not respons_text.strip():
                            st.error("Tanggapan tidak boleh kosong.")
                        elif not bukti_foto:
                            st.error("Bukti foto wajib diupload.")
                        else:
                            riwayat_df.at[idx, "respons_faskes"] = respons_text
                            riwayat_df.at[idx, "bukti_faskes"] = f"{bukti_foto.name} ({pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')})"
                            riwayat_df.at[idx, "status_sanggahan"] = "direspons"
                            st.session_state.riwayat_df = riwayat_df
                            st.success("✅ Sanggahan telah dijawab!")
                            st.rerun()

# ---------- LOGIKA PERAN: BPJS ----------
elif role == "bpjs":
    st.markdown("<h2 style='text-align:center; color:#0A8F5B;'>JKNKLIN - BPJS</h2>", unsafe_allow_html=True)
    st.info("Fitur Verifikasi Klaim & Analisis Kecurangan")
    klaim_belum = riwayat_df[riwayat_df["verifikasi_bpjs"] == False]
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
                    st.write(f"**Bukti Pasien**: {row.get('bukti_pasien', 'Tidak ada')}")
                    # Tampilkan kategori AI di BPJS juga
                    if row.get("kategori_sanggahan") and row["kategori_sanggahan"] != "Lainnya":
                        st.markdown(f"**Kategori AI**: `{row['kategori_sanggahan']}`", unsafe_allow_html=False)
                    if row.get("respons_faskes"):
                        st.success(f"**Respons Faskes**: {row['respons_faskes']}")
                        if row.get("bukti_faskes"):
                            st.write("**Bukti Faskes:**")
                            st.text(row["bukti_faskes"])
                st.write(f"**Dilakukan?**: {'✅ Ya' if row.get('tindakan_dilakukan', True) else '❌ Tidak'}")
                verif = st.checkbox("Verifikasi Klaim", key=f"verif_{idx}")
                if verif:
                    riwayat_df.at[idx, "verifikasi_bpjs"] = True
                    st.session_state.riwayat_df = riwayat_df
                    st.success("Klaim diverifikasi!")
