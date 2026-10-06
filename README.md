# BNB/USDT Telegram Signal Bot (Binance)

Bot Python otomatis untuk mendeteksi sinyal pergerakan harga **BNB/USDT** di Binance pada timeframe **15m** dan mengirimkan notifikasi ke Telegram berbasis transisi status (crossover & cancellation).

---

## 📈 Logika & Ketentuan Sinyal

Bot mengevaluasi setiap **candle yang sudah close** (`is_closed = True`):

| Indikator | Kondisi Bullish | Keterangan |
| :--- | :--- | :--- |
| **EMA 20** | `Close > EMA 20` | Harga berada di atas Exponential Moving Average 20 |
| **EMA 50** | `Close > EMA 50` | Harga berada di atas Exponential Moving Average 50 |
| **AVL (Avg Vol)** | `Volume > SMA 20 Volume` | Volume berada di atas rata-rata 20 periode |

### Kebijakan Notifikasi
- 🟢 **Sinyal AKTIF**: Dikirim saat kondisi berubah dari `False` ➔ `True` (crossover).
- 🔴 **Sinyal BATAL**: Dikirim saat kondisi berubah dari `True` ➔ `False` (detail penyebab pembatalan disertakan).
- Tidak ada spam notifikasi jika kondisi tetap sama pada candle berikutnya.

---

## 🚀 Panduan Instalasi & Menjalankan

### 1. Persiapan Environment

Salin file `.env.example` ke `.env`:
```bash
cp .env.example .env
```

Buka `.env` dan masukkan kredensial Telegram:
```env
TELEGRAM_BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
```

> **Cara mendapatkan token & chat ID Telegram:**
> 1. Buat bot via [@BotFather](https://t.me/BotFather) dan salin HTTP API Token.
> 2. Dapatkan Chat ID Anda via [@userinfobot](https://t.me/userinfobot) atau tambahkan bot ke group/channel lalu gunakan ID group/channel tersebut.

---

### 2. Menjalankan secara Lokal

1. Buat virtual environment (opsional tapi disarankan):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Pasang dependensi:
   ```bash
   pip install -r requirements.txt
   ```

3. Uji coba pengiriman pesan ke Telegram:
   ```bash
   python -m src.notifier
   ```

4. Jalankan bot:
   ```bash
   python -m src.main
   ```

---

### 3. Menjalankan Unit Tests

```bash
pytest -v
```

---

### 4. Menjalankan dengan Docker

```bash
docker compose up -d --build
```

Melihat log:
```bash
docker compose logs -f
```

Menghentikan:
```bash
docker compose down
```

---

## ⚙️ Konfigurasi Tambahan (`.env`)

| Variabel | Default | Penjelasan |
| :--- | :--- | :--- |
| `SYMBOL` | `BNBUSDT` | Simbol trading Binance |
| `INTERVAL` | `15m` | Timeframe candle (mis. 15m, 1h, 4h) |
| `EMA_FAST` | `20` | Periode EMA cepat |
| `EMA_SLOW` | `50` | Periode EMA lambat |
| `VOLUME_MA_PERIOD`| `20` | Periode rata-rata volume (AVL) |
| `HISTORY_LIMIT` | `200` | Jumlah candle warm-up awal |
| `DRY_RUN` | `false` | Jika `true`, bot hanya mencetak notifikasi ke log tanpa Telegram |
| `STATE_FILE` | `state.json` | Lokasi file penyimpanan status terakhir |
