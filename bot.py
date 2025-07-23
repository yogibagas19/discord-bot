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
BASE_DOWNLOAD_PATH = '/mnt/volume_sgp1_01/media'

# Mengatur intents yang diperlukan
intents = discord.Intents.default()
intents.message_content = True
# Anda mungkin perlu mengaktifkan Presence Intent di Discord Developer Portal
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents)

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
@bot.command(name='add', help='Menambahkan torrent ke path tertentu. Cth: !add movies [link]')
async def add_torrent(ctx, save_category: str = None, *, magnet_link: str = None):
    """
    Menambahkan unduhan baru ke qBittorrent dengan path dinamis (misal: /mnt/movies).
    """
    if not save_category:
        await ctx.send("⚠️ **Path dibutuhkan!**\nGunakan format: `!add [kategori] [magnet_link]`\nContoh: `!add movies <link>` atau `!add shows` sambil unggah file.")
        return

    # --- Validasi Path untuk Keamanan ---
    # Menggabungkan path dasar dengan kategori yang diberikan
    full_save_path = os.path.join(BASE_DOWNLOAD_PATH, save_category)
    
    # Mencegah serangan Directory Traversal (e.g., !add ../../etc)
    # Memastikan path absolut yang dituju benar-benar berada di dalam BASE_DOWNLOAD_PATH
    if not os.path.realpath(full_save_path).startswith(os.path.realpath(BASE_DOWNLOAD_PATH)):
        await ctx.send("❌ **Error Keamanan!** Kategori path tidak valid.")
        return

    # Inisialisasi koneksi ke qBittorrent
    qbt_client = qbittorrentapi.Client(
        host=QBIT_HOST, port=QBIT_PORT, username=QBIT_USERNAME, password=QBIT_PASSWORD
    )
    try:
        await ctx.send(f"⏳ Menghubungi qBittorrent untuk menyimpan di `{full_save_path}`...", delete_after=10)
        qbt_client.auth_log_in()
    except qbittorrentapi.LoginFailed:
        await ctx.send("❌ **Login Gagal!** Periksa kembali kredensial qBittorrent Anda.")
        return
    except Exception as e:
        await ctx.send(f"❌ **Tidak bisa terhubung ke qBittorrent!** Pastikan layanan berjalan. Error: {e}")
        return

    # Opsi unduhan, termasuk path dan aturan seeding
    download_options = {
        'save_path': full_save_path,
        'ratio_limit': 0,
        'seeding_time_limit': 0
    }

    # Kasus 1: Pengguna mengunggah file .torrent
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith('.torrent'):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            torrent_file_content = await resp.read()
                            result = qbt_client.torrents_add(torrent_files=torrent_file_content, **download_options)
                            if result == "Ok.":
                                await ctx.send(f"✅ **Berhasil!** File `{attachment.filename}` ditambahkan ke `{full_save_path}`.")
                            else:
                                await ctx.send(f"⚠️ Gagal menambahkan. Respons: `{result}`")
                        else:
                            await ctx.send("❌ Gagal mengunduh file `.torrent` dari Discord.")
                return
            except Exception as e:
                await ctx.send(f"❌ Terjadi kesalahan saat memproses file: {e}")
                return

    # Kasus 2: Pengguna memberikan magnet link
    if magnet_link and magnet_link.startswith('magnet:'):
        try:
            result = qbt_client.torrents_add(urls=magnet_link, **download_options)
            if result == "Ok.":
                await ctx.send(f"✅ **Berhasil!** Magnet link ditambahkan ke `{full_save_path}`.")
            else:
                await ctx.send(f"⚠️ Gagal menambahkan. Respons: `{result}`")
        except Exception as e:
            await ctx.send(f"❌ Terjadi kesalahan saat menambahkan magnet link: {e}")
        return

    await ctx.send(f"⚠️ **Link atau file tidak ditemukan.**\nPastikan Anda menyertakan magnet link setelah kategori, atau unggah file `.torrent` bersamaan dengan perintah `!add {save_category}`.")

# Menjalankan bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERROR: Token tidak ditemukan. Pastikan file .env sudah benar.")
