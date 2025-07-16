import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# Ambil credentials dari ENV dan ubah jadi dictionary
keyfile_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Catatan Keuangan").sheet1

def tambah_transaksi(jenis, jumlah, deskripsi):
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet.append_row([tanggal, jenis, jumlah, deskripsi])

def hitung_total():
    data = sheet.get_all_records()
    pemasukan = sum(row["Jumlah"] for row in data if row["Jenis"] == "pemasukan")
    pengeluaran = sum(row["Jumlah"] for row in data if row["Jenis"] == "pengeluaran")
    saldo = pemasukan - pengeluaran
    return pemasukan, pengeluaran, saldo

@app.route("/bot", methods=["POST"])
def bot():
    pesan = request.form.get("Body").lower()
    resp = MessagingResponse()

    if "pengeluaran" in pesan:
        try:
            parts = pesan.split(" ")
            jumlah = int(parts[1])
            deskripsi = " ".join(parts[2:])
            tambah_transaksi("pengeluaran", jumlah, deskripsi)
            resp.message(f"✅ Tercatat pengeluaran Rp{jumlah:,} untuk {deskripsi}")
        except:
            resp.message("❌ Format salah. Contoh: pengeluaran 50000 makan")

    elif "pemasukan" in pesan:
        try:
            parts = pesan.split(" ")
            jumlah = int(parts[1])
            deskripsi = " ".join(parts[2:])
            tambah_transaksi("pemasukan", jumlah, deskripsi)
            resp.message(f"✅ Tercatat pemasukan Rp{jumlah:,} dari {deskripsi}")
        except:
            resp.message("❌ Format salah. Contoh: pemasukan 100000 gaji")

    elif "total" in pesan:
        pemasukan, pengeluaran, saldo = hitung_total()
        resp.message(f"""📊 Rekap:
📥 Pemasukan: Rp{pemasukan:,}
📤 Pengeluaran: Rp{pengeluaran:,}
💰 Saldo: Rp{saldo:,}
""")
    else:
        resp.message("Halo! Kirim:\n- pengeluaran 50000 makan\n- pemasukan 200000 gaji\n- total")

    return str(resp)

if __name__ == "__main__":
    app.run()
