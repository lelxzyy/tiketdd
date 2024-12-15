from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import qrcode
from io import BytesIO
import base64
from flask_mail import Mail, Message
import pandas as pd

app = Flask(__name__)

# Konfigurasi Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'youremail@gmail.com'
app.config['MAIL_PASSWORD'] = 'yourpassword'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Database Setup
def init_db():
    conn = sqlite3.connect('participants.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        email TEXT NOT NULL,
                        category TEXT NOT NULL,
                        ticket_code TEXT NOT NULL UNIQUE,
                        attended INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# Halaman Utama
@app.route('/')
def home():
    return render_template('home.html')

# Submit Tiket
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    category = request.form['category']

    # Generate kode tiket unik
    ticket_code = f"TIKET-{name[:3].upper()}-{email[:3].upper()}"

    # Simpan ke database
    conn = sqlite3.connect('participants.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO participants (name, phone, email, category, ticket_code) VALUES (?, ?, ?, ?, ?)', (name, phone, email, category, ticket_code))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Email sudah digunakan untuk pemesanan tiket!"
    conn.close()

    # Generate QR Code
    qr = qrcode.QRCode()
    qr.add_data(ticket_code)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Kirim Email
    msg = Message('Tiket Anda', sender='youremail@gmail.com', recipients=[email])
    msg.body = f"Terima kasih {name}, berikut adalah tiket Anda.\nKode Tiket: {ticket_code}"
    msg.html = f"<h1>Terima kasih {name}</h1><p>Berikut adalah tiket Anda:</p><img src='data:image/png;base64,{qr_code_base64}'><p>Kode Tiket: {ticket_code}</p>"
    mail.send(msg)

    return render_template('ticket.html', name=name, ticket_code=ticket_code, qr_code=qr_code_base64)

# Export ke Excel
@app.route('/export')
def export():
    conn = sqlite3.connect('participants.db')
    df = pd.read_sql_query('SELECT * FROM participants', conn)
    conn.close()

    file_path = 'participants_list.xlsx'
    df.to_excel(file_path, index=False)
    return f"Data berhasil diexport ke {file_path}"

# Scan Tiket
@app.route('/scan', methods=['POST'])
def scan():
    ticket_code = request.form['ticket_code']

    conn = sqlite3.connect('participants.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE participants SET attended = 1 WHERE ticket_code = ?', (ticket_code,))
    conn.commit()
    conn.close()

    return f"Tiket {ticket_code} berhasil diverifikasi dan ditandai sebagai hadir."

if __name__ == '__main__':
    init_db()
    app.run(debug=True)