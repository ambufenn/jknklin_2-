# faskes_utils.py
import streamlit as st
import pandas as pd

def tampilkan_input_tindakan(pasien_df, riwayat_df):
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

def tampilkan_tanggapi_sanggahan(riwayat_df, pasien_df):
    st.markdown("### 📬 Tanggapi Sanggahan dari Pasien")
    sanggahan_menunggu = riwayat_df[riwayat_df["status_sanggahan"] == "menunggu"]
    with st.form("form_respons_faskes"):
        if sanggahan_menunggu.empty:
            st.info("ℹ️ Tidak ada sanggahan yang perlu ditanggapi saat ini.")
            st.selectbox("Pilih Sanggahan", ["Tidak ada sanggahan"], disabled=True)
            respons_text = st.text_area("Tanggapan Anda*", disabled=True, placeholder="Tidak ada sanggahan untuk direspons.")
            bukti_foto = st.file_uploader("Upload Bukti Foto*", type=["jpg", "png"], disabled=True)
        else:
            sanggahan_options = {}
            for idx, row in sanggahan_menunggu.iterrows():
                pasien_nama = pasien_df[pasien_df["user_id"] == row["user_id"]]["nama"].iloc[0]
                label = f"{pasien_nama} - {row['Layanan']} ({row['Tanggal'].strftime('%d %b %Y')})"
                sanggahan_options[idx] = label
            selected_sanggahan = st.selectbox("Pilih Sanggahan untuk Direspons", list(sanggahan_options.keys()), format_func=lambda x: sanggahan_options[x])
            row = sanggahan_menunggu.loc[selected_sanggahan]
            st.write(f"**Diagnosis**: {row['Diagnosis']}")
            st.write(f"**Sanggahan Pasien**: {row['sanggahan_pasien']}")
            if row.get("bukti_pasien"):
                st.write(f"**Bukti dari Pasien**: {row['bukti_pasien']}")
            if row.get("kategori_sanggahan") and row["kategori_sanggahan"] != "Lainnya":
                st.markdown(
                    f'<span style="background:#E8F5E9; padding:2px 6px; border-radius:4px; font-size:0.9em; color:#2E7D32;">'
                    f'🧠 Kategori AI: <b>{row["kategori_sanggahan"]}</b>'
                    f'</span>',
                    unsafe_allow_html=True
                )
            respons_text = st.text_area("Tanggapan Anda*", height=100)
            bukti_foto = st.file_uploader("Upload Bukti Foto* (wajib)", type=["jpg", "png"])
        submit = st.form_submit_button("Kirim Respons")
    
    if 'form_respons_faskes' in st.session_state or submit:
        if sanggahan_menunggu.empty:
            st.warning("Tidak ada sanggahan untuk direspons.")
        else:
            if not respons_text.strip():
                st.error("❌ Tanggapan tidak boleh kosong.")
            elif not bukti_foto:
                st.error("❌ Bukti foto wajib diupload.")
            else:
                riwayat_df.at[selected_sanggahan, "respons_faskes"] = respons_text
                riwayat_df.at[selected_sanggahan, "bukti_faskes"] = f"{bukti_foto.name} ({pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')})"
                riwayat_df.at[selected_sanggahan, "status_sanggahan"] = "direspons"
                st.session_state.riwayat_df = riwayat_df
                st.success("✅ Sanggahan telah dijawab!")
                st.rerun()
