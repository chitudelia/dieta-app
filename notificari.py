import requests
import schedule
import time
import json
from datetime import datetime

# Credențiale Telegram
TOKEN = "8708526353:AAEPk3S_YbLQEPinTQcguqR_dTVokNm-cfA"
CHAT_ID = "8766569482"

# Ziua din săptămână în română
ZILE = {
    "Monday": "Luni",
    "Tuesday": "Marti",
    "Wednesday": "Miercuri",
    "Thursday": "Joi",
    "Friday": "Vineri",
    "Saturday": "Sambata",
    "Sunday": "Duminica"
}

def trimite_mesaj(mesaj):
    # Trimite un mesaj pe Telegram
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"})

def get_meniu_azi():
    # Citește dieta salvată și returnează meniul pentru ziua de azi
    try:
        with open("dieta_salvata.json", "r", encoding="utf-8") as f:
            dieta = json.load(f)

        zi_engleza = datetime.now().strftime("%A")
        zi_romana = ZILE[zi_engleza]
        meniu = dieta["meniu"][zi_romana]

        mesaj = f"""🌅 <b>Bună ziua!</b>

📅 <b>Meniul pentru ziua de {zi_romana}:</b>

🍳 <b>Mic dejun:</b> {meniu['mic_dejun']}

🥗 <b>Prânz:</b> {meniu['pranz']}

🍽️ <b>Cină:</b> {meniu['cina']}

🍎 <b>Gustare:</b> {meniu['gustare']}

💧 Nu uita să bei cel puțin 8 pahare de apă!
💪 O zi productivă îți doresc!"""

        return mesaj
    except Exception as e:
        return f"Eroare la citirea meniului: {e}"

def notificare_meniu_dimineata():
    # Trimite meniul zilei în fiecare dimineață
    trimite_mesaj(get_meniu_azi())

def notificare_pranz():
    trimite_mesaj("☀️ E ora prânzului! Ai mâncat? 🥗\nNu sări peste mese!")

def notificare_apa():
    trimite_mesaj("💧 Reminder: Ai băut apă azi?\nÎncearcă să bei un pahar acum!")

def notificare_cina():
    trimite_mesaj("🌆 E timpul pentru cină! 🍽️\nAmintește-ți: cina cu 2 ore înainte de culcare!")

def raport_zilnic():
    # Trimite un raport scurt la finalul zilei
    trimite_mesaj(f"""🌙 <b>Raport zilnic - {datetime.now().strftime('%d/%m/%Y')}</b>

✅ Ai urmat dieta azi?
💧 Ai băut suficientă apă?
🏃 Ai făcut mișcare?

Continuă tot așa! Mâine e o nouă zi! 💪""")

def verificare_progres_saptamanal():
    # Rulează analiza de progres în fiecare duminică
    print(f"🔍 Rulare verificare progres săptămânală...")
    try:
        from progres import verifica_toti_utilizatorii
        verifica_toti_utilizatorii()
    except Exception as e:
        print(f"Eroare la verificare progres: {e}")

# Programare notificări zilnice
schedule.every().day.at("05:00").do(notificare_meniu_dimineata)
schedule.every().day.at("09:30").do(notificare_pranz)
schedule.every().day.at("12:00").do(notificare_apa)
schedule.every().day.at("16:00").do(notificare_cina)
schedule.every().day.at("18:00").do(raport_zilnic)

# Verificare progres în fiecare duminică la 20:00
schedule.every().sunday.at("20:00").do(verificare_progres_saptamanal)

print("✅ Notificările sunt active! Nu închide acest terminal.")

while True:
    schedule.run_pending()
    time.sleep(60)
    