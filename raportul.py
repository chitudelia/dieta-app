import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def trimite_raport(gmail_user, gmail_password, email_destinatar, profil, target, dieta, greutati, jurnal_azi):
    # Calculează progresul greutății
    if len(greutati) > 1:
        greutate_initiala = greutati[0][1]
        greutate_curenta = greutati[-1][1]
        diferenta = greutate_curenta - greutate_initiala
        if diferenta < 0:
            progres_text = f"Ai slăbit {abs(diferenta):.1f} kg față de start! 🎉"
        elif diferenta > 0:
            progres_text = f"Ai luat {diferenta:.1f} kg față de start."
        else:
            progres_text = "Greutatea ta e stabilă! ⚖️"
    else:
        progres_text = "Continuă să îți înregistrezi greutatea zilnic!"

    # Jurnalul de azi
    if jurnal_azi:
        mic_dejun, pranz, cina, apa = jurnal_azi
        jurnal_text = f"""
        🍳 Mic dejun: {"✅" if mic_dejun else "❌"}
        🥗 Prânz: {"✅" if pranz else "❌"}
        🍽️ Cină: {"✅" if cina else "❌"}
        💧 Pahare de apă: {apa}/8
        """
    else:
        jurnal_text = "Nu ai completat jurnalul de azi."

    # Construiește emailul
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Raportul tău zilnic de dietă - {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = gmail_user
    msg["To"] = email_destinatar

    # Conținutul emailului în HTML
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
        <h1 style="color: #FF6B35;">🥗 Raport zilnic - {profil['nume']}</h1>
        <p style="color: #888;">{datetime.now().strftime('%d/%m/%Y')}</p>
        <hr>
        <h2>👤 Profilul tău</h2>
        <ul>
            <li>Vârstă: {profil['varsta']} ani</li>
            <li>Înălțime: {profil['inaltime']} cm</li>
            <li>Greutate curentă: {profil['greutate']} kg</li>
        </ul>
        <h2>🎯 Obiectivul tău</h2>
        <p>{target['obiectiv']} — {target['kg_target']} kg în {target['luni']} luni</p>
        <h2>📊 Progres</h2>
        <p>{progres_text}</p>
        <h2>🗓️ Jurnal de azi</h2>
        <pre>{jurnal_text}</pre>
        <h2>🥗 Dieta ta</h2>
        <p>{dieta[:500]}..