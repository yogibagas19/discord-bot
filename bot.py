import discord
from discord.ext import tasks, commands
import psutil
import os
from dotenv import load_dotenv
import platform
import qbittorrentapi
import aiohttp

# Memuat variabel dari file .env
load_dotenv()
TOKEN = os.getenv('TOKEN_BOT')

# Interval pembaruan status dalam detik
UPDATE_INTERVAL_SECONDS = 2

QBIT_HOST = os.getenv("QBIT_HOST")
QBIT_PORT = os.getenv("QBIT_PORT")
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
QBIT_USERNAME = os.getenv('QBIT_USERNAME')
QBIT_PASSWORD = os.getenv('QBIT_PASSWORD')

# Mengatur intents yang diperlukan
intents = discord.Intents.default()
intents.message_content = True
# Anda mungkin perlu mengaktifkan Presence Intent di Discord Developer Portal
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents)

bot = discord.Client(intents=intents)

@tasks.loop(seconds=UPDATE_INTERVAL_SECONDS)
async def update_presence():
    """Tugas berulang untuk memperbarui status aktivitas bot."""
    await bot.wait_until_ready()
    
    try:
        # Ambil data CPU dan RAM
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        
        # Format teks status sesuai keinginan Anda
        activity_text = f"{cpu_percent}% • {ram_percent}%"
        
        # Buat objek aktivitas baru
        activity = discord.Game(name=activity_text)
        
        # Ubah status bot
        await bot.change_presence(activity=activity)
        
    except Exception as e:
        print(f"ERROR di dalam loop: {e}")

@bot.event
async def on_ready():
    """Fungsi yang berjalan saat bot berhasil online."""
    print(f'Bot telah login sebagai {bot.user}')
    
    # Memulai loop jika belum berjalan
    if not update_presence.is_running():
        update_presence.start()

# --- Perintah !add untuk Torrent ---
@bot.commands(name='add', help='Menambahkan torrent baru via magnet link atau file .torrent.')
async def add_torrent(ctx, *, magnet_link: str = None):
    """
    Menambahkan unduhan baru ke qBittorrent.
    Bisa dari magnet link atau file .torrent yang diunggah.
    """
    # Inisialisasi koneksi ke qBittorrent
    qbt_client = qbittorrentapi.Client(
        host=QBIT_HOST,
        port=QBIT_PORT,
        username=QBIT_USERNAME,
        password=QBIT_PASSWORD
    )

    try:
        # Coba login untuk memverifikasi koneksi
        await ctx.send("⏳ Menghubungi qBittorrent...", delete_after=5)
        qbt_client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        await ctx.send("❌ **Login Gagal!** Periksa kembali host, port, username, dan password qBittorrent Anda.")
        return
    except Exception as e:
        await ctx.send(f"❌ **Tidak bisa terhubung ke qBittorrent!** Pastikan qbittorrent-nox berjalan dan Web UI aktif. Error: {e}")
        return

    # Kasus 1: Pengguna mengunggah file .torrent
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith('.torrent'):
            try:
                # Mengunduh konten file torrent dari Discord
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            torrent_file_content = await resp.read()
                            # Menambahkan torrent dari file
                            result = qbt_client.torrents_add(torrent_files=torrent_file_content)
                            if result == "Ok.":
                                await ctx.send(f"✅ **Berhasil!** File `{attachment.filename}` telah ditambahkan ke antrean unduhan.")
                            else:
                                await ctx.send(f"⚠️ Gagal menambahkan torrent. qBittorrent merespons: `{result}`")
                        else:
                            await ctx.send("❌ Gagal mengunduh file `.torrent` dari Discord.")
                return
            except Exception as e:
                await ctx.send(f"❌ Terjadi kesalahan saat memproses file: {e}")
                return

    # Kasus 2: Pengguna memberikan magnet link
    if magnet_link and magnet_link.startswith('magnet:'):
        try:
            result = qbt_client.torrents_add(urls=magnet_link)
            if result == "Ok.":
                await ctx.send("✅ **Berhasil!** Magnet link telah ditambahkan ke antrean unduhan.")
            else:
                await ctx.send(f"⚠️ Gagal menambahkan torrent. qBittorrent merespons: `{result}`")
        except Exception as e:
            await ctx.send(f"❌ Terjadi kesalahan saat menambahkan magnet link: {e}")
        return

    # Jika tidak ada input yang valid
    await ctx.send("⚠️ **Perintah tidak valid.**\nGunakan `!add [magnet link]` atau unggah file `.torrent` bersamaan dengan perintah `!add`.")

# Menjalankan bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERROR: Token tidak ditemukan. Pastikan file .env sudah benar.")
