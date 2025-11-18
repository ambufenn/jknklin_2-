import os
import pandas as pd

# ---------- LOAD KNOWLEDGE BASE ----------
def load_knowledge_base():
    tarif_path = os.path.join("data", "tarif_ina_cbgs.csv")
    if os.path.exists(tarif_path):
        df = pd.read_csv(tarif_path)
        info = "DATA TARIF INA-CBGs BPJS KESEHATAN TERKINI:\n"
        for _, row in df.iterrows():
            info += f"- {row['Diagnosis']}: tarif BPJS Rp{row['Tarif_BPJS']:,}, rata-rata klaim regional Rp{row['Regional_Avg']:,}\n"
        return info
    return "DATA TARIF TIDAK TERSEDIA.\n"

def load_faq():
    path = os.path.join("data", "jkn_faq.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

# Gabungkan semua pengetahuan
KNOWLEDGE_SNIPPET = load_knowledge_base() + "\n" + load_faq()

# ---------- GENERATE RESPONSE ----------
def get_response(user_input, model, user_context=""):
    """
    user_context (opsional): riwayat pengguna, misal: "Riwayat terbaru: ISPA, klaim Rp800.000"
    """
    if len(user_input) > 500:
        user_input = user_input[:500] + "..."

    full_prompt = f"""Kamu adalah FairCare Assistant, chatbot resmi sistem JKNKLIN yang membantu peserta JKN memahami transparansi layanan kesehatan, klaim BPJS, dan hak mereka.

{KNOWLEDGE_SNIPPET}

{user_context}

Aturan respons:
1. Jawab hanya dalam konteks JKN/BPJS Kesehatan Indonesia.
2. Gunakan bahasa Indonesia yang jelas, sopan, dan empatik.
3. Jangan mengarang data, kebijakan, atau angka di luar pengetahuan yang diberikan.
4. Jika pertanyaan di luar topik, arahkan ke topik JKN atau sarankan hubungi BPJS langsung.
5. Jika pengguna tanya tentang klaim atau tarif, tawarkan bantuan lewat fitur "Bandingkan Tarif & Tindakan".
6. Jawaban maksimal 3 kalimat kecuali penjelasan teknis diperlukan.

Pertanyaan pengguna: {user_input}
"""

    try:
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 350,
                "top_p": 0.9
            },
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )
        output = response.text.strip()
        if not output:
            raise ValueError("Respons kosong")
        return output
    except Exception:
        return "Maaf, saya sedang tidak dapat menjawab. Silakan coba tanya hal lain seputar JKN atau gunakan fitur 'Bandingkan Tarif' untuk analisis klaim."
