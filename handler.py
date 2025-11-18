# handler.py
import pandas as pd
import os

# Load knowledge base
def load_knowledge_base():
    tarif_path = os.path.join("data", "tarif_ina_cbgs.csv")
    if os.path.exists(tarif_path):
        df = pd.read_csv(tarif_path)
        info = ""
        for _, row in df.iterrows():
            info += f"- {row['Diagnosis']}: tarif BPJS Rp{row['Tarif_BPJS']:,}, rata-rata klaim Rp{row['Regional_Avg']:,}\n"
        return info
    return ""

KNOWLEDGE_SNIPPET = load_knowledge_base()

def get_response(user_input, model):
    if len(user_input) > 500:
        user_input = user_input[:500] + "..."

    system_prompt = f"""
Kamu adalah FairCare Assistant, chatbot resmi dari sistem JKNKLIN yang membantu peserta JKN memahami:
- Tarif INA-CBGs BPJS Kesehatan
- Analisis klaim rumah sakit
- Proses sanggahan klaim
- Indikasi overclaim atau ketidakwajaran layanan

Berikut data tarif terkini:
{KNOWLEDGE_SNIPPET}

Aturan:
1. Jawab hanya dalam konteks JKN & BPJS Kesehatan Indonesia.
2. Jika tidak tahu, katakan: "Saya tidak memiliki informasi tersebut, silakan hubungi BPJS Kesehatan langsung."
3. Gunakan bahasa Indonesia yang jelas, empatik, dan informatif.
4. Jangan mengarang angka atau kebijakan.
5. Jika pengguna tanya tentang klaim, tawarkan bantuan analisis via fitur 'Bandingkan Tarif'.

Pertanyaan pengguna: {user_input}
"""

    response = model.generate_content(
        system_prompt,
        generation_config={
            "temperature": 0.3,  # lebih konsisten
            "max_output_tokens": 300,
            "top_p": 0.9
        },
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
        }
    )
    return response.text.strip()
