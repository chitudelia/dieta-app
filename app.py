import streamlit as st
from openai import OpenAI
from datetime import datetime
import pandas as pd
import json
import os
from database import inregistrare, login, salveaza_greutate, get_greutati, salveaza_jurnal, get_jurnal_azi, salveaza_profil, get_profil

# Configurare pagina
st.set_page_config(page_title="Dieta Personalizată", page_icon="🥗", layout="centered")

# Citește cheile din environment variables sau secrets
def get_secret(key):
    val = os.environ.get(key)
    if val:
        return val
    try:
        return st.secrets[key]
    except:
        return ""

# CSS custom tema portocalie
st.markdown("""
<style>
    .stApp { background-color: #fff8f5; }
    .stButton > button {
        background-color: #FF6B35;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: bold;
        font-size: 15px;
        transition: 0.3s;
        width: 100%;
    }
    .stButton > button:hover { background-color: #e55a25; color: white; }
    h1 { color: #FF6B35 !important; }
    h2, h3 { color: #cc4a1a !important; }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffe8de;
        border-radius: 10px;
        padding: 5px;
        gap: 5px;
    }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #FF6B35; font-weight: bold; }
    .stTabs [aria-selected="true"] { background-color: #FF6B35 !important; color: white !important; }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input { border: 2px solid #FFB899; border-radius: 8px; }
    .stExpander { border: 1px solid #FFB899 !important; border-radius: 10px !important; background-color: white; }
    hr { border-color: #FFB899; }
    .stAlert { border-radius: 10px; }
    .block-container { padding-top: 2rem; max-width: 750px; }
</style>
""", unsafe_allow_html=True)

# Initializare sesiune
if "utilizator" not in st.session_state:
    st.session_state.utilizator = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "auth"
if "profil" not in st.session_state:
    st.session_state.profil = None
if "target" not in st.session_state:
    st.session_state.target = None
if "dieta" not in st.session_state:
    st.session_state.dieta = None
if "dieta_json" not in st.session_state:
    st.session_state.dieta_json = None

# ---- PAGINA AUTH ----
if st.session_state.pagina == "auth":
    st.markdown("<h1 style='text-align:center'>🥗 Dieta Personalizată</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>Aplicația ta de nutriție personalizată cu AI</p>", unsafe_allow_html=True)
    st.markdown("---")

    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Înregistrare"])

    with tab_login:
        st.subheader("Bun venit înapoi! 👋")
        email_login = st.text_input("Email", key="email_login")
        parola_login = st.text_input("Parolă", type="password", key="parola_login")

        if st.button("Intră în cont 🔑"):
            if email_login and parola_login:
                utilizator = login(email_login, parola_login)
                if utilizator:
                    st.session_state.utilizator = {
                        "nume": utilizator[0],
                        "email": utilizator[1],
                        "telegram_chat_id": utilizator[2]
                    }
                    profil_salvat = get_profil(email_login)
                    if profil_salvat:
                        st.session_state.profil = {
                            "nume": utilizator[0],
                            "email": utilizator[1],
                            "telegram_chat_id": utilizator[2],
                            "varsta": profil_salvat[2],
                            "inaltime": profil_salvat[3],
                            "greutate": profil_salvat[4],
                            "sex": profil_salvat[5]
                        }
                        st.session_state.target = {
                            "obiectiv": profil_salvat[6],
                            "kg_target": profil_salvat[7],
                            "luni": profil_salvat[8],
                            "alimente": profil_salvat[9],
                            "alergii": profil_salvat[10]
                        }
                        st.session_state.dieta = profil_salvat[11]
                        if profil_salvat[11]:
                            st.session_state.dieta_json = json.loads(profil_salvat[11])
                        st.session_state.pagina = "dieta"
                    else:
                        st.session_state.pagina = "profil"
                    st.rerun()
                else:
                    st.error("❌ Email sau parolă greșită!")
            else:
                st.error("Te rog completați toate câmpurile!")

    with tab_register:
        st.subheader("Creează un cont nou ✨")
        nume_reg = st.text_input("Nume", key="nume_reg")
        email_reg = st.text_input("Email", key="email_reg")
        parola_reg = st.text_input("Parolă", type="password", key="parola_reg")
        parola_reg2 = st.text_input("Confirmă parola", type="password", key="parola_reg2")
        st.info("📱 Pentru notificări Telegram: caută **@userinfobot** pe Telegram și trimite /start — îți dă Chat ID-ul tău.")
        telegram_id = st.text_input("Chat ID Telegram (opțional)", placeholder="Ex: 123456789", key="telegram_id")

        if st.button("Creează cont 📝"):
            if nume_reg and email_reg and parola_reg and parola_reg2:
                if parola_reg != parola_reg2:
                    st.error("❌ Parolele nu coincid!")
                elif len(parola_reg) < 6:
                    st.error("❌ Parola trebuie să aibă cel puțin 6 caractere!")
                else:
                    succes = inregistrare(nume_reg, email_reg, parola_reg, telegram_id)
                    if succes:
                        st.success("✅ Cont creat cu succes! Acum te poți loga.")
                    else:
                        st.error("❌ Emailul este deja folosit!")
            else:
                st.error("Te rog completați toate câmpurile!")

# ---- PAGINA 1: PROFIL ----
elif st.session_state.pagina == "profil":
    u = st.session_state.utilizator
    st.markdown("<h1>👤 Profilul tău</h1>", unsafe_allow_html=True)
    st.subheader(f"Bună, {u['nume']}! Hai să te cunoaștem mai bine 😊")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        varsta = st.number_input("🎂 Vârstă", min_value=10, max_value=100, value=25)
        inaltime = st.number_input("📏 Înălțime (cm)", min_value=100, max_value=250, value=165)
    with col2:
        greutate = st.number_input("⚖️ Greutate (kg)", min_value=30, max_value=300, value=65)
        sex = st.selectbox("👤 Sex", ["Femeie", "Bărbat"])

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Deconectare 🚪"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col2:
        if st.button("Continuă →"):
            inaltime_m = inaltime / 100
            imc = greutate / (inaltime_m ** 2)

            if imc < 18.5:
                imc_categorie = "Subponderal ⚠️"
                imc_color = "warning"
            elif imc < 25:
                imc_categorie = "Normal ✅"
                imc_color = "success"
            elif imc < 30:
                imc_categorie = "Supraponderal ⚠️"
                imc_color = "warning"
            else:
                imc_categorie = "Obezitate ❌"
                imc_color = "error"

            st.session_state.profil = {
                "nume": u['nume'],
                "email": u['email'],
                "telegram_chat_id": u['telegram_chat_id'],
                "varsta": varsta,
                "inaltime": inaltime,
                "greutate": greutate,
                "sex": sex,
                "imc": round(imc, 1),
                "imc_categorie": imc_categorie
            }
            salveaza_greutate(u['email'], greutate)

            if imc_color == "success":
                st.success(f"📊 IMC-ul tău: **{round(imc, 1)}** — {imc_categorie}")
            elif imc_color == "warning":
                st.warning(f"📊 IMC-ul tău: **{round(imc, 1)}** — {imc_categorie}")
            else:
                st.error(f"📊 IMC-ul tău: **{round(imc, 1)}** — {imc_categorie}")

            st.session_state.pagina = "target"
            st.rerun()

# ---- PAGINA 2: TARGET ----
elif st.session_state.pagina == "target":
    p = st.session_state.profil
    st.markdown("<h1>🎯 Obiectivul tău</h1>", unsafe_allow_html=True)
    st.subheader(f"Ce vrei să obții, {p['nume']}?")

    if "imc" in p:
        st.info(f"📊 IMC-ul tău: **{p['imc']}** — {p['imc_categorie']}")

    st.markdown("---")

    obiectiv = st.selectbox("🏆 Obiectiv principal", [
        "Slăbire",
        "Menținere greutate",
        "Creștere în masă musculară"
    ])

    col1, col2 = st.columns(2)
    with col1:
        kg_target = st.number_input("⚖️ Câte kg?", min_value=0.5, max_value=50.0, value=5.0)
    with col2:
        luni = st.number_input("📅 În câte luni?", min_value=1, max_value=24, value=2)

    alimente = st.text_area("🍎 Ce alimente preferi?", placeholder="Ex: pui, orez, broccoli, ouă, iaurt, mere...")
    alergii = st.text_input("⚠️ Alergii sau alimente de evitat?", placeholder="Ex: lactate, gluten... (lasă gol dacă nu ai)")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Înapoi"):
            st.session_state.pagina = "profil"
            st.rerun()
    with col2:
        if st.button("Generează Dieta 🚀"):
            if alimente:
                st.session_state.target = {
                    "obiectiv": obiectiv,
                    "kg_target": kg_target,
                    "luni": luni,
                    "alimente": alimente,
                    "alergii": alergii
                }
                st.session_state.pagina = "dieta"
                st.rerun()
            else:
                st.error("Te rog introduceți alimentele preferate!")

# ---- PAGINA 3: DIETA ----
elif st.session_state.pagina == "dieta":
    p = st.session_state.profil
    t = st.session_state.target

    tab1, tab2, tab3, tab4 = st.tabs(["🥗 Dieta mea", "📊 Progres", "🗓️ Jurnal", "📧 Raport"])

    with tab1:
        st.markdown(f"<h1>🥗 Dieta ta, {p['nume']}!</h1>", unsafe_allow_html=True)

        if "imc" in p:
            if p['imc'] < 25:
                st.success(f"📊 IMC: **{p['imc']}** — {p['imc_categorie']}")
            else:
                st.warning(f"📊 IMC: **{p['imc']}** — {p['imc_categorie']}")

        if st.session_state.dieta is None:
            with st.spinner("Se generează dieta ta personalizată... ⏳"):
                try:
                    # Citește cheia din Railway Variables sau secrets.toml
                    cheie_debug = get_secret("OPENAI_API_KEY")
                    st.info(f"🔍 DEBUG: cheia folosită se termină în ...{cheie_debug[-6:]} (lungime: {len(cheie_debug)})")
                    client = OpenAI(api_key=cheie_debug)

                    prompt = f"""Creează un plan de dietă săptămânal personalizat pentru:
- Nume: {p['nume']}, {p['sex']}, {p['varsta']} ani
- Înălțime: {p['inaltime']} cm, Greutate: {p['greutate']} kg
- IMC: {p.get('imc', 'necunoscut')} ({p.get('imc_categorie', '')})
- Obiectiv: {t['obiectiv']} {t['kg_target']} kg în {t['luni']} luni
- Alimente preferate: {t['alimente']}
- Alergii/evitat: {t['alergii'] if t['alergii'] else 'Nimic'}

Răspunde EXACT în acest format JSON, nimic altceva în afară de JSON:
{{
    "calorii_zilnice": 1800,
    "timp_estimat_saptamani": 8,
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
                    st.session_state.dieta_json = json.loads(raw)
                    st.session_state.dieta = raw

                    salveaza_profil(
                        p['email'], p['varsta'], p['inaltime'], p['greutate'], p['sex'],
                        t['obiectiv'], t['kg_target'], t['luni'], t['alimente'], t['alergii'],
                        raw
                    )

                    with open("dieta_salvata.json", "w", encoding="utf-8") as f:
                        json.dump(st.session_state.dieta_json, f, ensure_ascii=False)

                except Exception as e:
                    st.error(f"Eroare: {e}")
                    st.stop()

        if st.session_state.dieta_json:
            d = st.session_state.dieta_json

            col1, col2 = st.columns(2)
            with col1:
                st.metric("🔥 Calorii zilnice", f"{d['calorii_zilnice']} kcal")
            with col2:
                st.metric("⏱️ Timp estimat", f"{d['timp_estimat_saptamani']} săptămâni")

            st.markdown("---")
            for zi, meniu in d['meniu'].items():
                with st.expander(f"📅 {zi}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"🍳 **Mic dejun:** {meniu['mic_dejun']}")
                        st.write(f"🥗 **Prânz:** {meniu['pranz']}")
                    with col2:
                        st.write(f"🍽️ **Cină:** {meniu['cina']}")
                        st.write(f"🍎 **Gustare:** {meniu['gustare']}")

            st.markdown("---")
            st.info(f"💡 **Sfaturi:** {d['sfaturi']}")

        st.markdown("---")
        ora = datetime.now().hour
        if 6 <= ora < 10:
            st.success("🌅 Bună dimineața! E timpul pentru micul dejun!")
        elif 12 <= ora < 14:
            st.success("☀️ E ora prânzului! Nu uita să mănânci!")
        elif 18 <= ora < 20:
            st.success("🌆 E timpul pentru cină!")
        else:
            st.info("💧 Nu uita să bei apă!")

    with tab2:
        st.markdown("<h1>📊 Grafic de progres</h1>", unsafe_allow_html=True)

        if "imc" in p:
            st.info(f"📊 IMC curent: **{p['imc']}** — {p['imc_categorie']}")

        greutate_azi = st.number_input(
            "Greutatea de azi (kg):",
            min_value=30.0, max_value=300.0,
            value=float(p['greutate'])
        )

        if st.button("Salvează greutatea ✅"):
            salveaza_greutate(p['email'], greutate_azi)
            inaltime_m = p['inaltime'] / 100
            imc_nou = round(greutate_azi / (inaltime_m ** 2), 1)
            st.success(f"✅ Greutatea salvată! IMC nou: **{imc_nou}**")
            st.rerun()

        date_greutati = get_greutati(p['email'])
        if date_greutati:
            df = pd.DataFrame(date_greutati, columns=["Data", "Greutate"])
            st.line_chart(df.set_index("Data")["Greutate"])
            diferenta = date_greutati[-1][1] - date_greutati[0][1]
            if diferenta < 0:
                st.success(f"🎉 Ai slăbit {abs(diferenta):.1f} kg față de start!")
            elif diferenta > 0:
                st.info(f"📈 Ai luat {diferenta:.1f} kg față de start!")
            else:
                st.info("⚖️ Greutatea ta e stabilă!")

    with tab3:
        st.markdown("<h1>🗓️ Jurnal alimentar</h1>", unsafe_allow_html=True)
        st.subheader(f"Azi — {datetime.now().strftime('%d/%m/%Y')}")

        jurnal_azi = get_jurnal_azi(p['email'])
        if jurnal_azi:
            mic_dejun_val, pranz_val, cina_val, apa_val = jurnal_azi
        else:
            mic_dejun_val, pranz_val, cina_val, apa_val = 0, 0, 0, 0

        col1, col2 = st.columns(2)
        with col1:
            mic_dejun = st.checkbox("🍳 Am mâncat micul dejun", value=bool(mic_dejun_val))
            pranz = st.checkbox("🥗 Am mâncat prânzul", value=bool(pranz_val))
        with col2:
            cina = st.checkbox("🍽️ Am mâncat cina", value=bool(cina_val))

        apa = st.slider("💧 Pahare de apă băute azi:", min_value=0, max_value=12, value=int(apa_val))

        if st.button("Salvează jurnalul 💾"):
            salveaza_jurnal(p['email'], mic_dejun, pranz, cina, apa)
            st.success("✅ Jurnal salvat!")

        mese_bifate = sum([mic_dejun, pranz, cina])
        st.markdown("---")
        if mese_bifate == 3 and apa >= 8:
            st.success("🎉 Ziua perfectă! Ai mâncat toate mesele și ai băut suficientă apă!")
        elif mese_bifate == 3:
            st.warning("✅ Ai mâncat toate mesele! Mai bea puțină apă!")
        elif apa >= 8:
            st.warning(f"💧 Hidratare perfectă! Ai mâncat {mese_bifate}/3 mese.")
        else:
            st.info(f"📊 Progres: {mese_bifate}/3 mese, {apa}/8 pahare apă")

    with tab4:
        st.markdown("<h1>📧 Raport pe email</h1>", unsafe_allow_html=True)
        st.write("Primești un raport complet cu dieta și progresul tău!")

        email = st.text_input("Adresa ta de email:", value=p['email'])

        if st.button("Trimite raport 📧"):
            if email:
                with st.spinner("Se trimite emailul... ⏳"):
                    from raportul import trimite_raport
                    rezultat = trimite_raport(
                        gmail_user=get_secret("GMAIL_USER"),
                        gmail_password=get_secret("GMAIL_PASSWORD"),
                        email_destinatar=email,
                        profil=p,
                        target=t,
                        dieta=st.session_state.dieta,
                        greutati=get_greutati(p['email']),
                        jurnal_azi=get_jurnal_azi(p['email'])
                    )
                    if rezultat == True:
                        st.success(f"✅ Raportul a fost trimis la {email}!")
                    else:
                        st.error(f"Eroare: {rezultat}")
            else:
                st.error("Te rog introduceți adresa de email!")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Schimbă obiectivul"):
            st.session_state.pagina = "target"
            st.session_state.dieta = None
            st.session_state.dieta_json = None
            st.rerun()
    with col2:
        if st.button("Deconectare 🚪"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()