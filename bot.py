import discord
from discord.ext import tasks
import psutil
import os
from dotenv import load_dotenv

# Memuat variabel dari file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Interval pembaruan status dalam detik
UPDATE_INTERVAL_SECONDS = 5

# --- PENGATURAN INTENTS ---
# Ini sangat penting. Tanpa ini, banyak hal tidak akan berfungsi dengan benar.
intents = discord.Intents.default()
# Jika Anda berencana menambahkan fitur lain di masa depan, Anda mungkin perlu menambahkan intents lain,
# intents.messages = True

bot = discord.Client(intents=intents)

# Variabel untuk melacak status mana yang akan ditampilkan
show_cpu_status = True

@tasks.loop(seconds=UPDATE_INTERVAL_SECONDS)
async def update_presence():
    """Tugas berulang untuk memperbarui status aktivitas bot."""
    global show_cpu_status
    
    # Tambahkan print untuk memastikan loop ini berjalan
    print("DEBUG: Loop 'update_presence' sedang berjalan...")
    
    try:
        activity_text = ""
        if show_cpu_status:
            cpu_percent = psutil.cpu_percent()
            activity_text = f"CPU {cpu_percent}%"
        else:
            ram_percent = psutil.virtual_memory().percent
            activity_text = f"RAM {ram_percent}%"

        # Buat objek aktivitas baru
        activity = discord.Game(name=activity_text)
        
        # Ubah status bot
        await bot.change_presence(activity=activity)
        print(f"DEBUG: Status berhasil diubah menjadi -> {activity_text}")

        # Ganti toggle untuk tampilan berikutnya
        show_cpu_status = not show_cpu_status
    except Exception as e:
        print(f"ERROR di dalam loop: {e}")


@bot.event
async def on_ready():
    """Fungsi yang berjalan saat bot berhasil online."""
    print(f'Bot telah login sebagai {bot.user}')
    print("-" * 20)
    
    # Memulai loop jika belum berjalan
    if not update_presence.is_running():
        print("DEBUG: Memulai loop 'update_presence'...")
        update_presence.start()
    else:
        print("DEBUG: Loop 'update_presence' sudah berjalan.")

# Menjalankan bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERROR: Token tidak ditemukan. Pastikan file .env sudah benar.")