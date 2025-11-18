import pandas as pd
import os

def load_tarif_data():
    path = os.path.join("data", "tarif_ina_cbgs.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    df = pd.read_csv(path)
    INA_CBGs = dict(zip(df["Diagnosis"], df["Tarif_BPJS"]))
    REGIONAL_AVG = dict(zip(df["Diagnosis"], df["Regional_Avg"]))
    return INA_CBGs, REGIONAL_AVG

INA_CBGs, REGIONAL_AVG = load_tarif_data()

def analyze_claim(diagnosis, claimed_amount, facility_type="Rumah Sakit", days=1):
    diagnosis_key = diagnosis if diagnosis in INA_CBGs else "Rawat Jalan Umum"
    tarif_bpjs = INA_CBGs.get(diagnosis_key, 0)
    avg_claim = REGIONAL_AVG.get(diagnosis_key, tarif_bpjs)
    warning = []
    is_suspicious = False

    if tarif_bpjs > 0:
        over_bpjs_pct = (claimed_amount - tarif_bpjs) / tarif_bpjs * 100
        if over_bpjs_pct > 20:
            warning.append(f"Klaim {over_bpjs_pct:.1f}% di atas tarif INA-CBGs BPJS.")
            is_suspicious = True
        elif over_bpjs_pct > 10:
            warning.append(f"Klaim sedikit di atas tarif BPJS (+{over_bpjs_pct:.1f}%).")
    else:
        warning.append("Diagnosis tidak ditemukan dalam daftar tarif — perlu verifikasi manual.")

    if avg_claim > 0 and claimed_amount > avg_claim * 1.25:
        over_avg_pct = (claimed_amount - avg_claim) / avg_claim * 100
        warning.append(f"Klaim {over_avg_pct:.1f}% di atas rata-rata regional.")
        is_suspicious = True

    if days > 3 and diagnosis in ["ISPA", "Diare"]:
        warning.append("Rawat inap >3 hari tidak lazim untuk diagnosis ringan ini.")
        is_suspicious = True

    return {
        "diagnosis": diagnosis,
        "claimed_amount": claimed_amount,
        "tarif_bpjs": tarif_bpjs,
        "regional_avg": avg_claim,
        "warning": warning,
        "is_suspicious": is_suspicious,
        "facility_type": facility_type,
        "days": days
    }

def generate_appeal_suggestion(analysis_result):
    if analysis_result["is_suspicious"]:
        return (
            "Berdasarkan analisis FairCare, klaim ini memiliki indikasi ketidaksesuaian. "
            "Anda dapat mengajukan sanggahan dengan menyertakan:\n"
            "- Salinan rincian klaim dari rumah sakit\n"
            "- Bukti diagnosis (hasil lab/resep)\n"
            "- Pertanyaan: mengapa biaya melebihi tarif BPJS?"
        )
    else:
        return (
            "Klaim ini sesuai dengan standar tarif dan pola pelayanan. "
            "Jika Anda tetap ingin mengajukan sanggahan, silakan jelaskan alasan spesifik Anda."
        )
