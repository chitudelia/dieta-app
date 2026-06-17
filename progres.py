import json
import os
import requests
from datetime import datetime
from openai import OpenAI
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from database import get_toti_utilizatorii, analizeaza_progres, actualizeaza_dieta

# Configurare — citește din variabile de mediu
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
GMAIL_USER = os.environ.get("GMAIL_USER", "")

def trimite_telegram(chat_id, mesaj):
    if not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": mesaj, "parse_mode": "HTML"})

def trimite_email(email_destinatar, subiect, continut_html):
    try:
        message = Mail(
            from_email=GMAIL_USER,
            to_emails=email_destinatar,
            subject=subiect,
            html_content=continut_html
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"Eroare email: {e}")
        return False

def analizeaza_trend(inregistrari, obiectiv):
    if len(inregistrari) < 2:
        return 'date_insuficiente'

    greutate_veche = inregistrari[-1][1]
    greutate_noua = inregistrari[0][1]
    diferenta = greutate_noua - greutate_veche

    if obiectiv == "Slăbire":
        if diferenta < -0.3:
            return 'progres_bun'
        elif diferenta > 0.3:
            return 'regres'
        else:
            return 'stagnare'
    elif obiectiv == "Creștere în masă musculară":
        if diferenta > 0.3:
            return 'progres_bun'
        elif diferenta < -0.3:
            return 'regres'
        else:
            return 'stagnare'
    else:
        if abs(diferenta) < 0.5:
            return 'progres_bun'
        else:
            return 'stagnare'

def reconfigureaza_dieta(utilizator, trend, inregistrari):
    email, telegram_id, greutate_initiala, obiectiv, kg_target, luni, alimente, alergii, varsta, inaltime, sex = utilizator

    greutate_curenta = inregistrari[0][1] if inregistrari else greutate_initiala
    diferenta = greutate_curenta - greutate_initiala

    if trend == 'regres':
        motiv = f"utilizatorul s-a îngrășat cu {abs(diferenta):.1f} kg în ultimele 7 zile"
        actiune = "mai restrictivă, cu mai puține calorii și mai multe proteine"
    else:
        motiv = f"utilizatorul a stagnat (diferență de doar {diferenta:.1f} kg) în ultimele 7 zile"
        actiune = "ajustată pentru a accelera metabolismul"

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""Reconfigurează dieta pentru un utilizator care nu face progres.

Situație: {motiv}
Profil: {sex}, {varsta} ani, {inaltime} cm, greutate curentă {greutate_curenta} kg
Obiectiv: {obiectiv} {kg_target} kg în {luni} luni
Alimente preferate: {alimente}
Alergii: {alergii if alergii else 'Nimic'}

Creează o dietă nouă {actiune}.

Răspunde EXACT în acest format JSON:
{{
    "calorii_zilnice": 1600,
    "timp_estimat_saptamani": 6,
    "motiv_schimbare": "Explicație scurtă de ce s-a schimbat dieta",
    "modificari_principale": "Ce s-a schimbat față de dieta anterioară",
    "meniu": {{
        "Luni": {{"mic_dejun": "...", "pranz": "...", "cina": "...", "gustare": "..."}},
        "Marti": {{"mic_dejun": "...", "pranz": "...", "cina": "...", "gustare": "..."}},
        "Miercuri": {{"mic_dejun": "...", "pranz": "...", "cina": "...", "gustare": "..."}},
        "Joi": {{"mic_dejun": "...", "pranz": "...", "cina": "...", "gustare": "..."}},
        "Vineri": {{"mic_dejun": "...", "pranz": "...", "cina": "...", "gustare": "..."}},
        "Sambata": {{"mic_dejun": "...", "pranz": "...", "cina": "...", "gustare": "..."}},
        "Duminica": {{"mic_dejun": "...", "pranz": "...", "cina": "...", "gustare": "..."}}
    }},
    "sfaturi": "..."
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )

        raw = response.choices[0].message.content
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        dieta_noua = json.loads(raw)

        actualizeaza_dieta(email, raw)

        email_html = f"""
        <html>
        <body style="font-family: Arial; max-width: 600px; margin: auto; padding: 20px;">
            <h1 style="color: #FF6B35;"> Dieta ta a fost reconfigurată!</h1>
            <p>Bună ziua,</p>
            <p>Am analizat progresul tău din ultimele 7 zile și am observat că <b>{motiv}</b>.</p>
            <p>De aceea, am reconfigurat dieta ta pentru a se adapta mai bine metabolismului tău.</p>
            <h2 style="color: #FF6B35;">📊 Ce s-a schimbat:</h2>
            <p>{dieta_noua['modificari_principale']}</p>
            <h2 style="color: #FF6B35;">🔥 Noile calorii zilnice: {dieta_noua['calorii_zilnice']} kcal</h2>
            <h2 style="color: #FF6B35;">⏱️ Timp estimat nou: {dieta_noua['timp_estimat_saptamani']} săptămâni</h2>
            <h2 style="color: #FF6B35;">🥗 Noul tău plan săptămânal:</h2>
            {"".join([f"<h3>📅 {zi}</h3><p>🍳 <b>Mic dejun:</b> {meniu['mic_dejun']}<br>🥗 <b>Prânz:</b> {meniu['pranz']}<br>🍽️ <b>Cină:</b> {meniu['cina']}<br>🍎 <b>Gustare:</b> {meniu['gustare']}</p>" for zi, meniu in dieta_noua['meniu'].items()])}
            <h2 style="color: #FF6B35;">💡 Sfaturi:</h2>
            <p>{dieta_noua['sfaturi']}</p>
            <p style="color: #888; font-size: 12px;">Trimis automat de Dieta Personalizată 💪</p>
        </body>
        </html>
        """

        trimite_email(email, "🔄 Dieta ta a fost reconfigurată automat!", email_html)

        telegram_msg = f"""🔄 <b>Dieta ta a fost reconfigurată!</b>

Am observat că {motiv}.

✅ <b>Ce s-a schimbat:</b> {dieta_noua['modificari_principale']}
🔥 <b>Calorii noi:</b> {dieta_noua['calorii_zilnice']} kcal/zi
⏱️ <b>Timp estimat:</b> {dieta_noua['timp_estimat_saptamani']} săptămâni

Verifică emailul pentru planul complet! 📧"""

        trimite_telegram(telegram_id, telegram_msg)

        print(f" Dietă reconfigurată pentru {email}")
        return True

    except Exception as e:
        print(f"❌ Eroare la reconfigurare pentru {email}: {e}")
        return False

def verifica_toti_utilizatorii():
    print(f"🔍 Verificare progres utilizatori - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    utilizatori = get_toti_utilizatorii()

    if not utilizatori:
        print("Nu există utilizatori cu profil complet.")
        return

    for utilizator in utilizatori:
        email = utilizator[0]
        obiectiv = utilizator[3]

        inregistrari = analizeaza_progres(email)

        if len(inregistrari) < 7:
            print(f"⏳ {email} — date insuficiente ({len(inregistrari)}/7 zile)")
            continue

        trend = analizeaza_trend(inregistrari, obiectiv)
        print(f" {email} — trend: {trend}")

        if trend in ['regres', 'stagnare']:
            print(f"🔄 Reconfigurare dietă pentru {email}...")
            reconfigureaza_dieta(utilizator, trend, inregistrari)
        else:
            print(f" {email} — progres bun, nicio schimbare necesară")

if __name__ == "__main__":
    verifica_toti_utilizatorii()