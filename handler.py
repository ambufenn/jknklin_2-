#handler.py
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

# ---------- FUNGSI BARU: ANALISIS NLP UNTUK SANGGAHAN ----------
def analisis_sanggahan_nlp(sanggahan_text, model):
    """
    Analisis maksud sanggahan menggunakan Gemini (NLP).
    Returns: {"kategori": str, "ringkasan": str}
    """
    prompt = f"""
    Anda adalah analis klaim BPJS. Klasifikasikan sanggahan berikut ke dalam SATU kategori:
    - Tindakan Tidak Dilakukan
    - Biaya Tidak Wajar
    - Diagnosis Salah
    - Dokumen Tidak Sesuai
    - Lainnya

    Berikan juga ringkasan maksimal 8 kata.

    Format respons: KATEGORI: [kategori] | RINGKASAN: [ringkasan]

    Sanggahan: "{sanggahan_text}"
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 64, "top_p": 0.9},
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )
        output = response.text.strip()
        
        # Parse output
        if "KATEGORI:" in output and "RINGKASAN:" in output:
            kategori = output.split("KATEGORI:")[1].split("|")[0].strip()
            ringkasan = output.split("RINGKASAN:")[1].strip()
            return {"kategori": kategori, "ringkasan": ringkasan}
        else:
            return {"kategori": "Lainnya", "ringkasan": sanggahan_text[:30] + ("..." if len(sanggahan_text) > 30 else "")}
    except Exception:
        return {"kategori": "Lainnya", "ringkasan": "Analisis AI gagal"}

# ---------- FUNGSI CHATBOT (TIDAK DIUBAH) ----------
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
