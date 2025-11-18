import os
import pandas as pd

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

KNOWLEDGE_SNIPPET = load_knowledge_base() + "\n" + load_faq()

def get_response(user_input, model, user_context=""):
    if len(user_input) > 500:
        user_input = user_input[:500] + "..."
    
    full_prompt = f"""Kamu adalah FairCare Assistant, chatbot resmi sistem JKNKLIN yang membantu peserta JKN memahami transparansi layanan kesehatan, klaim BPJS, dan hak mereka.

{KNOWLEDGE_SNIPPET}

Aturan:
1. Jawab hanya seputar JKN/BPJS Kesehatan Indonesia.
2. Gunakan bahasa Indonesia yang jelas dan empatik.
3. Jangan mengarang data.
4. Jika tidak tahu, arahkan ke fitur 'Bandingkan Tarif' atau sarankan hubungi BPJS.
5. Jawaban maksimal 3 kalimat.

Pertanyaan pengguna: {user_input}
"""
    
    try:
        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.3, "max_output_tokens": 350, "top_p": 0.9},
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )
        output = response.text.strip()
        return output if output else "Maaf, saya tidak dapat menjawab saat ini."
    except Exception:
        return "Maaf, sedang ada gangguan teknis. Silakan coba fitur 'Bandingkan Tarif' untuk analisis klaim."
