import math
from collections import defaultdict, Counter
import re

# Soha: Ta'lim. 50 ta real axborot gaplari (IR bazasi)
documents = [
    "O'zbekiston Milliy universiteti Toshkent shahrida joylashgan bo'lib matematika va fizika fanlariga ixtisoslashgan.",
    "Alisher Navoiy nomidagi Toshkent davlat o'zbek tili va adabiyoti universiteti 2016 yilda tashkil topgan.",
    "Toshkent tibbiyot akademiyasida jarrohlik va terapiya yo'nalishlari bo'yicha tibbiy mutaxassislar tayyorlanadi.",
    "Toshkent davlat iqtisodiyot universitetida sirtqi va kechki ta'lim shakllari mavjud.",
    "Jahon iqtisodiyoti va diplomatiya universiteti xalqaro munosabatlar yo'nalishida nufuzli kadrlar tayyorlaydi.",
    "Toshkent axborot texnologiyalari universiteti dasturlash, sun'iy intellekt va kiberxavfsizlik bo'yicha yetakchi hisoblanadi.",
    "Samarqand davlat universiteti O'zbekistondagi eng qadimiy oliygohlardan biri hisoblanadi.",
    "Buxoro davlat tibbiyot instituti xorijiy talabalar uchun ham o'quv dasturlarini taklif qiladi.",
    "Farg'ona politexnika instituti muhandislik va texnologiya sohasida mutaxassislar chiqaradi.",
    "Toshkent davlat yuridik universiteti huquqshunoslik bo'yicha O'zbekistondagi yagona markazlashtirilgan oliygohdir.",
    "Andijon davlat universiteti pedagogika va gumanitar fanlarga ixtisoslashgan.",
    "Namangan muhandislik-qurilish instituti arxitektura va qurilish sohasida bilim beradi.",
    "Navoiy davlat konchilik instituti tog'-kon sanoati uchun muhandislar tayyorlaydi.",
    "Urganch davlat universiteti Xorazm viloyatining asosiy ilmiy markazi hisoblanadi.",
    "Qoraqalpoq davlat universiteti Nukus shahrida joylashgan va ko'p tarmoqli ta'lim beradi.",
    "Jizzax politexnika instituti energetika va transport sohasida faoliyat yuritadi.",
    "Qarshi davlat universiteti Qashqadaryo viloyatining eng yirik o'quv dargohidir.",
    "Termiz davlat universiteti tarix va arxeologiya sohasida kuchli maktabga ega.",
    "Guliston davlat universiteti qishloq xo'jaligi va biologiya fanlarida yetakchi o'rinlarda.",
    "Toshkent irrigatsiya va qishloq xo'jaligini mexanizatsiyalash muhandislari instituti respublikada yagona.",
    "Toshkent davlat sharqshunoslik universiteti Osiyo va Yaqin Sharq tillarini o'qitishga ixtisoslashgan.",
    "Toshkent pediatriya tibbiyot instituti bolalar kasalliklari bo'yicha mutaxassislar tayyorlaydi.",
    "Toshkent moliya instituti bank ishi va buxgalteriya hisobi bo'yicha kadrlar yetkazib beradi.",
    "Toshkent arxitektura qurilish instituti zamonaviy shaharsozlik loyihalarini o'rgatadi.",
    "Toshkent to'qimachilik va yengil sanoat instituti kiyim dizayni va texnologiyalariga yo'naltirilgan.",
    "Toshkent davlat transport universiteti temir yo'l va aviatsiya sohalari uchun muhandislar tayyorlaydi.",
    "Toshkent davlat agrar universiteti qishloq xo'jaligi mutaxassislarini tayyorlovchi markazdir.",
    "Toshkent farmatsevtika instituti dori vositalari texnologiyasi va dorishunoslikni o'qitadi.",
    "Toshkent kimyo-texnologiya instituti oziq-ovqat va neft-kimyo sanoati uchun kadrlar beradi.",
    "O'zbekiston davlat jahon tillari universiteti ingliz, fransuz, nemis va ispan tillarini o'rgatadi.",
    "O'zbekiston davlat san'at va madaniyat instituti teatr va kino aktyorlarini tayyorlaydi.",
    "Toshkent davlat texnika universiteti mashinasozlik va elektronika sohalarida eng yirik institutdir.",
    "Maktabgacha ta'lim vazirligi bog'cha tarbiyachilari uchun maxsus qayta tayyorlov kurslarini ochdi.",
    "Xalq ta'limi vazirligi 11-sinf o'quvchilari uchun yangi darsliklarni nashrdan chiqardi.",
    "Oliy ta'lim vazirligi talabalar uchun davlat stipendiyalari miqdorini oshirdi.",
    "Davlat test markazi qabul imtihonlari uchun yangi onlayn ro'yxatdan o'tish tizimini ishga tushirdi.",
    "O'zbekistonda xalqaro universitetlarning filiallari soni 30 taga yetdi.",
    "Kredit-modul tizimi barcha davlat oliy ta'lim muassasalarida joriy etildi.",
    "Magistratura bosqichiga qabul qilishda xorijiy til sertifikati majburiy qilib belgilandi.",
    "Masofaviy ta'lim shakli bo'yicha yangi kvotalar tasdiqlandi.",
    "Sirtqi ta'lim yo'nalishlarida o'qish muddati 5 yil qilib belgilangan.",
    "Iqtidorli talabalar uchun Prezident stipendiyasi tanlovi e'lon qilindi.",
    "Talabalar turar joylarida yangi kutubxonalar va kompyuter xonalari tashkil etildi.",
    "Yosh olimlar uchun ilmiy grantlar va amaliy loyihalar tanlovi boshlandi.",
    "Universitetlar o'rtasida talabalar almashinuvi dasturi xalqaro doirada kengaymoqda.",
    "Professor-o'qituvchilarning oylik maoshlari ilmiy darajasiga qarab tabaqalashtirildi.",
    "Akademik litsey bitiruvchilari o'z yo'nalishlari bo'yicha imtiyozlarga ega bo'lishdi.",
    "Texnikum bitiruvchilari oliygohning 2-kursidan suhbat asosida o'qishni davom ettirishlari mumkin.",
    "Oliygohlarga qabul test sinovlari avgust oyining birinchi haftasida bo'lib o'tadi.",
    "O'zbekiston universitetlari dunyoning top 1000 reytingiga kirish maqsadida xalqaro akkreditatsiyadan o'tmoqda."
]

# 1. Tokenlarga ajratish (Tokenization)
def tokenize(text):
    text = text.lower()
    # Punktuatsiyani tozalash va so'zlarga ajratish
    tokens = re.findall(r'\b[a-z0-9\']+\b', text)
    return tokens

# 2. Teskari indeksatsiya (Inverted Index)
def build_inverted_index(docs):
    index = defaultdict(list)
    for doc_id, text in enumerate(docs):
        tokens = set(tokenize(text))
        for token in tokens:
            index[token].append(doc_id)
    return index

inverted_index = build_inverted_index(documents)

# 3. TF-IDF Qidiruv modeli
def search_tfidf(query, docs=documents, index=inverted_index):
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    
    N = len(docs)
    scores = defaultdict(float)
    df = {token: len(index[token]) for token in query_tokens if token in index}
    
    for doc_id, text in enumerate(docs):
        doc_tokens = tokenize(text)
        doc_len = len(doc_tokens)
        token_counts = Counter(doc_tokens)
        
        for token in query_tokens:
            if token in index and doc_id in index[token]:
                tf = token_counts[token] / doc_len
                idf = math.log(N / (df[token] + 1))
                scores[doc_id] += tf * idf
                
    results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(docs[doc_id], score) for doc_id, score in results if score > 0.0]

# 4. BM25 Qidiruv modeli
def search_bm25(query, docs=documents, index=inverted_index, k1=1.5, b=0.75):
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
        
    N = len(docs)
    avgdl = sum(len(tokenize(doc)) for doc in docs) / N
    scores = defaultdict(float)
    
    df = {token: len(index[token]) for token in query_tokens if token in index}
    
    for doc_id, text in enumerate(docs):
        doc_tokens = tokenize(text)
        doc_len = len(doc_tokens)
        token_counts = Counter(doc_tokens)
        
        for token in query_tokens:
            if token in index and doc_id in index[token]:
                f = token_counts[token]
                idf = math.log((N - df[token] + 0.5) / (df[token] + 0.5) + 1)
                term = (f * (k1 + 1)) / (f + k1 * (1 - b + b * doc_len / avgdl))
                scores[doc_id] += idf * term
                
    results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(docs[doc_id], score) for doc_id, score in results if score > 0.0]

# 5. Soha bo'yicha 50ta gapni slotlarga ajratish
def extract_slots(text):
    slots = {"Tashkilot": "-", "Soha": "-", "Sana": "-"}
    
    universities = ["universiteti", "universitet", "akademiyasi", "instituti", "tatu", "vazirligi", "markazi"]
    subjects = ["matematika", "fizika", "tibbiyot", "iqtisodiyot", "dasturlash", "huquqshunoslik", "pedagogika", "arxitektura", "qishloq", "tillari", "kino", "kiberxavfsizlik"]
    locations_dates = ["toshkent", "samarqand", "buxoro", "farg'ona", "andijon", "namangan", "navoiy", "urganch", "nukus", "jizzax", "qarshi", "termiz", "guliston", "2016", "2020", "2023", "avgust"]
    
    tokens = tokenize(text)
    
    # Slotlarni to'ldirish
    for word in tokens:
        for u in universities:
            if u in word: slots["Tashkilot"] = "Topildi"
        for s in subjects:
            if s in word: slots["Soha"] = s.capitalize()
        for l in locations_dates:
            if l in word: slots["Sana"] = l.capitalize()
            
    return slots

def get_slotted_sentences():
    results = []
    for doc in documents:
        results.append({
            "text": doc,
            "slots": extract_slots(doc)
        })
    return results
