# 🎵 Spotify Playlist Organizer CLI

A powerful yet lightweight **command‑line tool** to organize your Spotify **Liked Songs** into playlists — with optional **automatic playback** on your devices, local **30‑second previews**, smart **resume**, and comprehensive **logging**.

Built with Python, [Spotipy](https://spotipy.readthedocs.io/), and `pygame` for a fun terminal experience.

---

## ✨ Features

- **Auto‑play songs** on your Spotify devices while organizing
- **Create new playlists** or add to existing ones
- **Multi‑playlist selection** (e.g., `1,3,5` to add to several at once)
- **Resume where you left off** (processed tracks are tracked on disk)
- **Optional 30‑second previews** via `pygame` when device playback isn’t available
- **Open current track** directly in the Spotify app or web
- **Comprehensive logging** (session log + detailed rotating logs)
- **Easy credential setup** (prompts once, stores locally in `.config`)
- **Clean CLI homepage** with an ASCII banner

---

## 🖥️ Requirements

- Python **3.8+**
- A Spotify account + **Developer App** credentials
- Python packages (installed via `requirements.txt`):
  - `spotipy`
  - `requests`
  - `pygame` (optional but recommended for previews)

> macOS users: if you see the pygame support message and want it hidden, set `PYGAME_HIDE_SUPPORT_PROMPT=1` before importing pygame (already handled in the app).

---

## 🚀 Quick Start

### 1) Clone the repository
```bash
git clone https://github.com/jameeloop/Spotify-Organizer-CLI.git
cd Spotify-Organizer-CLI
```

### 2) Create a virtual environment (recommended)

**macOS / Linux (bash/zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scriptsctivate
```

### 3) Install dependencies (cross‑platform, safe form)
```bash
python -m pip install -r requirements.txt
```
> On macOS/Linux, if `python` points to Python 2, use `python3 -m pip install -r requirements.txt`.

### 4) Set up your Spotify Developer App

1. Go to the **[Spotify Developer Dashboard](https://developer.spotify.com/dashboard)** and create an app.
2. Open **Settings** → **Redirect URIs** → add:
   ```text
   http://127.0.0.1:8888
   ```
3. Note your **Client ID** and **Client Secret**.
4. On first run, the app will prompt for these and store them locally in `.config`.

### 5) Run the application

**Cross‑platform:**
```bash
python main.py
```
> On macOS/Linux, if needed: `python3 main.py`.

---

## 🎯 Usage

### Interactive Mode (default)
```bash
python main.py
```
Shows the homepage and walks you through organizing.

### Direct Organizing Mode
```bash
python main.py --organize
```
Skips the homepage and starts organizing immediately.

### Help
```bash
python main.py --help
```

---

## 🎮 Controls During Organization

| Command      | Action                                   |
|--------------|-------------------------------------------|
| `Enter` / `s`| Skip current song                         |
| `1`, `2`, …  | Add to playlist by number                 |
| `1,3,5`      | Add to multiple playlists                 |
| `n`          | Create a new playlist + add song          |
| `p`          | Play/stop 30‑sec local preview            |
| `o`          | Open song in Spotify                      |
| `b`          | Go back to previous song                  |
| `q`          | Quit and save progress                    |

---

## 📁 File Structure

```
Spotify-Organizer-CLI/
├─ main.py                     # Entry point
├─ requirements.txt            # Dependencies
├─ setup_guide.md              # Spotify API setup guide
├─ README.md                   # This file
├─ LICENSE                     # MIT License
├─ logs/                       # Application logs (created at runtime)
│  └─ spotify_organizer_*.log
├─ session.log                 # Session activity log
├─ processed_tracks.log        # Tracks you've already handled
├─ .cache-spotify-organizer    # Spotify OAuth cache (created at runtime)
└─ .config                     # Stored credentials (created at runtime)
```

> **Important:** `.config`, `.cache-spotify-organizer`, `logs/`, and IDE folders should be ignored by Git. See **Git Ignore** below.

---

## 📊 Logging

- **Application logs**: detailed rotating logs in `logs/spotify_organizer_*.log`
- **Session log**: human‑readable summary in `session.log`
- **Processed tracks**: stored in `processed_tracks.log` so you can safely resume

---

## 🔧 Configuration

### Credentials (`.config`)
Saved as JSON on first run:
```json
{
  "spotify_client_id": "your_client_id",
  "spotify_client_secret": "your_client_secret",
  "spotify_redirect_uri": "http://127.0.0.1:8888",
  "created_at": "2024-01-01T12:00:00"
}
```

### Spotify API Scopes
The application requests these scopes:
- `user-library-read`
- `playlist-read-private`
- `playlist-read-collaborative`
- `playlist-modify-public`
- `playlist-modify-private`
- `user-read-playback-state`
- `user-modify-playback-state`

---

## 🧹 Git Ignore (recommended)

Ensure these entries (you may already have them):
```gitignore
# IDE / caches
.idea/
.cache-spotify-organizer
logs/
session.log
processed_tracks.log

# Python
__pycache__/
*.py[cod]
*.egg*
*.log

# Envs
.venv/
venv/
env/
*.env

# OS
.DS_Store
Thumbs.db
```

To remove already‑tracked IDE/cache files:
```bash
git rm -r --cached .idea logs .cache-spotify-organizer 2>/dev/null || true
git rm --cached session.log processed_tracks.log 2>/dev/null || true
git add .gitignore
git commit -m "chore: ignore IDE/cache/log files"
git push
```

---

## 🐛 Troubleshooting

**No Spotify devices found**
- Ensure Spotify is open on a device (desktop, mobile, or web player)
- Start playback once to “wake” the device
- Confirm the device is reachable on your network

**Authentication errors**
- Double‑check Client ID/Secret and redirect URI (`http://127.0.0.1:8888`)
- Delete `.cache-spotify-organizer` and `.config` to re‑authenticate

**Local preview not working**
- Install `pygame` (`python -m pip install pygame`)
- Some tracks simply don’t have preview URLs

**pip vs python mismatch**
- Always install with the same interpreter you run:
  ```bash
  python -m pip install -r requirements.txt
  python main.py
  ```
  On macOS/Linux, replace `python` with `python3` if needed.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/awesome-thing`
3. Make changes + tests
4. Submit a Pull Request

---

## 📜 License

Licensed under the **MIT License** — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgments

- [Spotipy](https://spotipy.readthedocs.io/) — Python Spotify API wrapper
- [Pygame](https://www.pygame.org/) — Local audio preview & CLI flair
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) — Data + playback control

---

## ⭐ Support

If you find this useful, please **star the repo** — it helps others discover it.
For issues or ideas, open a **GitHub Issue**.
