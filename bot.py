import discord
from discord.ext import tasks
import psutil
import os
from dotenv import load_dotenv

load_dotenv()

# --- KONFIGURASI ---
TOKEN = os.getenv('TOKEN_BOT')
# Interval pembaruan status dalam detik
UPDATE_INTERVAL_SECONDS = 2

# --- LOGIKA BOT ---
intents = discord.Intents.default()
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Bot telah login sebagai {bot.user}')

# Pastikan Anda menjalankan bot dengan variabel TOKEN
if TOKEN is None:
    print("Error: DISCORD_TOKEN tidak ditemukan di file .env")
else:
    bot.run(TOKEN)

# Variabel untuk melacak status mana yang akan ditampilkan
show_cpu_status = True

@tasks.loop(seconds=UPDATE_INTERVAL_SECONDS)
async def update_presence():
    """Tugas berulang untuk memperbarui status aktivitas bot."""
    global show_cpu_status
    await bot.wait_until_ready()

    activity_text = ""
    if show_cpu_status:
        # Ambil dan format data CPU
        cpu_percent = psutil.cpu_percent()
        activity_text = f"CPU {cpu_percent}%"
    else:
        # Ambil dan format data RAM
        ram_percent = psutil.virtual_memory().percent
        activity_text = f"RAM {ram_percent}%"

    # Buat objek aktivitas baru
    activity = discord.Game(name=activity_text)
    
    # Ubah status bot
    await bot.change_presence(activity=activity)

    # Ganti toggle untuk tampilan berikutnya
    show_cpu_status = not show_cpu_status

@bot.event
async def on_ready():
    """Fungsi yang berjalan saat bot berhasil online."""
    print(f'Bot telah login sebagai {bot.user}')
    print('Memulai pembaruan status otomatis...')
    # Memulai loop jika belum berjalan
    if not update_presence.is_running():
        update_presence.start()

# Menjalankan bot dengan token Anda
bot.run(TOKEN)