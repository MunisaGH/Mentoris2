import pickle
import re
import sys

def clean_uzbek_text(text):
    text = text.lower()
    text = re.sub(r'(lik|lar|ni|ning|ga|da|dan|cha|chi|lari|mi|ngiz|miz)\b', '', text)
    return text

try:
    with open('c:/Users/MUNISA/Desktop/MENTORSUZ/NLP_Klassifikator/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    with open('c:/Users/MUNISA/Desktop/MENTORSUZ/NLP_Klassifikator/model.pkl', 'rb') as f:
        model = pickle.load(f)

    print("Model muvaffaqiyatli yuklandi.")
    
    text1 = "menga kompyuterlar va dasturlash yoqadi"
    print("T1:", model.predict(vectorizer.transform([clean_uzbek_text(text1)])))

    text2 = "menga shifokorlik yoqadi"
    print("T2:", model.predict(vectorizer.transform([clean_uzbek_text(text2)])))
except Exception as e:
    print("XATOLIK YUZ BERDI:", e)
