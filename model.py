import os
import google.generativeai as genai

def load_model():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    return genai.GenerativeModel("gemini-1.5-flash")
