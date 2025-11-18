# pasien_utils.py
import streamlit as st
import pandas as pd
from model import load_model
from handler import get_response, analisis_sanggahan_nlp

def tampilkan_pasien(pasien_df, riwayat_df):
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
