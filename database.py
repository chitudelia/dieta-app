import sqlite3
import hashlib
from datetime import datetime

def conectare():
    conn = sqlite3.connect("dieta.db")
    return conn

def creare_tabele():
    conn = conectare()
    c = conn.cursor()

    # Tabel utilizatori
    c.execute("""
        CREATE TABLE IF NOT EXISTS utilizatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nume TEXT,
            email TEXT UNIQUE,
            parola TEXT,
            telegram_chat_id TEXT
        )
    """)

    # Tabel profiluri — salvează profilul și targetul fiecărui user
    c.execute("""
        CREATE TABLE IF NOT EXISTS profiluri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            varsta INTEGER,
            inaltime REAL,
            greutate REAL,
            sex TEXT,
            obiectiv TEXT,
            kg_target REAL,
            luni INTEGER,
            alimente TEXT,
            alergii TEXT,
            dieta TEXT
        )
    """)

    # Tabel greutăți
    c.execute("""
        CREATE TABLE IF NOT EXISTS greutati (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            data TEXT,
            greutate REAL
        )
    """)

    # Tabel jurnal alimentar
    c.execute("""
        CREATE TABLE IF NOT EXISTS jurnal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            data TEXT,
            mic_dejun INTEGER,
            pranz INTEGER,
            cina INTEGER,
            apa INTEGER
        )
    """)

    conn.commit()
    conn.close()

def inregistrare(nume, email, parola, telegram_chat_id):
    conn = conectare()
    c = conn.cursor()
    parola_criptata = hashlib.sha256(parola.encode()).hexdigest()
    try:
        c.execute("INSERT INTO utilizatori (nume, email, parola, telegram_chat_id) VALUES (?, ?, ?, ?)",
                  (nume, email, parola_criptata, telegram_chat_id))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def login(email, parola):
    conn = conectare()
    c = conn.cursor()
    parola_criptata = hashlib.sha256(parola.encode()).hexdigest()
    c.execute("SELECT nume, email, telegram_chat_id FROM utilizatori WHERE email=? AND parola=?",
              (email, parola_criptata))
    utilizator = c.fetchone()
    conn.close()
    return utilizator

# Salvează sau actualizează profilul unui utilizator
def salveaza_profil(email, varsta, inaltime, greutate, sex, obiectiv, kg_target, luni, alimente, alergii, dieta):
    conn = conectare()
    c = conn.cursor()
    c.execute("SELECT id FROM profiluri WHERE email=?", (email,))
    exista = c.fetchone()
    if exista:
        c.execute("""UPDATE profiluri SET varsta=?, inaltime=?, greutate=?, sex=?,
                     obiectiv=?, kg_target=?, luni=?, alimente=?, alergii=?, dieta=?
                     WHERE email=?""",
                  (varsta, inaltime, greutate, sex, obiectiv, kg_target, luni, alimente, alergii, dieta, email))
    else:
        c.execute("""INSERT INTO profiluri (email, varsta, inaltime, greutate, sex,
                     obiectiv, kg_target, luni, alimente, alergii, dieta)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (email, varsta, inaltime, greutate, sex, obiectiv, kg_target, luni, alimente, alergii, dieta))
    conn.commit()
    conn.close()

# Returnează profilul salvat al unui utilizator
def get_profil(email):
    conn = conectare()
    c = conn.cursor()
    c.execute("SELECT * FROM profiluri WHERE email=?", (email,))
    rezultat = c.fetchone()
    conn.close()
    return rezultat

def salveaza_greutate(email, greutate):
    conn = conectare()
    c = conn.cursor()
    c.execute("INSERT INTO greutati (email, data, greutate) VALUES (?, ?, ?)",
              (email, datetime.now().strftime("%d/%m/%Y"), greutate))
    conn.commit()
    conn.close()

def get_greutati(email):
    conn = conectare()
    c = conn.cursor()
    c.execute("SELECT data, greutate FROM greutati WHERE email=? ORDER BY id", (email,))
    rezultat = c.fetchall()
    conn.close()
    return rezultat

def salveaza_jurnal(email, mic_dejun, pranz, cina, apa):
    conn = conectare()
    c = conn.cursor()
    azi = datetime.now().strftime("%d/%m/%Y")
    c.execute("SELECT id FROM jurnal WHERE email=? AND data=?", (email, azi))
    exista = c.fetchone()
    if exista:
        c.execute("""UPDATE jurnal SET mic_dejun=?, pranz=?, cina=?, apa=?
                     WHERE email=? AND data=?""", (mic_dejun, pranz, cina, apa, email, azi))
    else:
        c.execute("""INSERT INTO jurnal (email, data, mic_dejun, pranz, cina, apa)
                     VALUES (?, ?, ?, ?, ?, ?)""", (email, azi, mic_dejun, pranz, cina, apa))
    conn.commit()
    conn.close()

def get_jurnal_azi(email):
    conn = conectare()
    c = conn.cursor()
    azi = datetime.now().strftime("%d/%m/%Y")
    c.execute("SELECT mic_dejun, pranz, cina, apa FROM jurnal WHERE email=? AND data=?", (email, azi))
    rezultat = c.fetchone()
    conn.close()
    return rezultat

creare_tabele()

# Verifică progresul din ultimele 7 zile
def analizeaza_progres(email):
    conn = conectare()
    c = conn.cursor()
    c.execute("""SELECT data, greutate FROM greutati 
                 WHERE email=? ORDER BY id DESC LIMIT 7""", (email,))
    rezultat = c.fetchall()
    conn.close()
    return rezultat

# Salvează dieta reconfigurată
def actualizeaza_dieta(email, dieta_noua):
    conn = conectare()
    c = conn.cursor()
    c.execute("UPDATE profiluri SET dieta=? WHERE email=?", (dieta_noua, email))
    conn.commit()
    conn.close()

# Returnează toți utilizatorii cu profil complet
def get_toti_utilizatorii():
    conn = conectare()
    c = conn.cursor()
    c.execute("""SELECT u.email, u.telegram_chat_id, p.greutate, p.obiectiv, 
                 p.kg_target, p.luni, p.alimente, p.alergii, p.varsta, 
                 p.inaltime, p.sex
                 FROM utilizatori u
                 JOIN profiluri p ON u.email = p.email""")
    rezultat = c.fetchall()
    conn.close()
    return rezultat