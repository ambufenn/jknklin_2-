# bpjs_utils.py
import streamlit as st
import pandas as pd
from fairness_engine import INA_CBGs

def tampilkan_bpjs(pasien_df, riwayat_df):
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
                
                warning_list = []
                tarif_bpjs = INA_CBGs.get(row["Diagnosis"], 0)
                klaim = row.get("Klaim", 0)
                if tarif_bpjs > 0 and klaim > tarif_bpjs * 1.2:
                    warning_list.append("⚠️ **Overklaim**: Klaim >20% di atas tarif BPJS")
                if row["Diagnosis"] in ["ISPA", "Diare"] and "Rawat Inap" in str(row["Layanan"]):
                    warning_list.append("⚠️ **Pola Tidak Lazim**: Rawat inap untuk diagnosis ringan")
                if row.get("sanggahan_pasien"):
                    warning_list.append("⚠️ **Ada Sanggahan Pasien**: Perlu klarifikasi")
                
                if warning_list:
                    st.warning("🚨 **Deteksi Potensi Masalah:**")
                    for w in warning_list:
                        st.write(w)
                    faskes = row["Fasilitas"]
                    if "RS" in faskes or "Rumah Sakit" in faskes:
                        area_rekom = "unit rawat inap & farmasi"
                    elif "Klinik" in faskes:
                        area_rekom = "rekam medis & tindakan"
                    else:
                        area_rekom = "dokumentasi klaim"
                    st.markdown(
                        f'<div style="background:#E3F2FD; padding:10px; border-radius:6px; margin-top:10px;">'
                        f'<b>🤖 Rekomendasi AI:</b> Prioritaskan verifikasi manual dan '
                        f'periksa <b>{area_rekom}</b> di {faskes}.'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.success("✅ Tidak ditemukan indikasi kejanggalan.")
                    st.markdown(
                        '<div style="background:#F1F8E9; padding:10px; border-radius:6px; margin-top:10px;">'
                        '<b>🤖 Rekomendasi AI:</b> Klaim ini berisiko rendah. Verifikasi standar cukup.'
                        '</div>',
                        unsafe_allow_html=True
                    )
                
                if row.get("sanggahan_pasien"):
                    st.warning(f"**Sanggahan Pasien**: {row['sanggahan_pasien']}")
                    st.write(f"**Bukti Pasien**: {row.get('bukti_pasien', 'Tidak ada')}")
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
                    st.success("✅ Klaim diverifikasi!")
