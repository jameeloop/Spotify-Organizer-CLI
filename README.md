# Spotify Playlist Organizer CLI

A powerful command-line tool to help you organize your Spotify liked songs into playlists with automatic device playback support.

## 🎵 Features

- **Auto-play songs** on your Spotify devices while organizing
- **Create new playlists** or add to existing ones
- **Multi-playlist support** - add songs to multiple playlists at once (e.g., `1,3,5`)
- **Resume functionality** - tracks processed songs so you can continue where you left off
- **Optional 30-second previews** for songs without device playback
- **Open songs directly** in Spotify web/app
- **Comprehensive logging** - session logs and detailed application logs
- **Easy credential management** - prompts for API credentials and saves them locally

## 📋 Requirements

- Python 3.6+
- `spotipy` library (for Spotify API)
- `pygame` library (optional, for local audio previews)
- Active Spotify account with Developer App

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/jameeloop/Spotify-Organizer-CLI.git
cd Spotify-Organizer-CLI

```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up Spotify Developer App
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create an App"
3. Fill in any name and description
4. In Settings, add `http://127.0.0.1:8888` as a Redirect URI
5. Note your Client ID and Client Secret

### 4. Run the application
```bash
python main.py
```

The app will prompt you for your Spotify credentials on first run and save them to a `.config` file for future use.

## 🎯 Usage

### Interactive Mode (Default)
```bash
python main.py
```
Shows the homepage with instructions, then starts the organizing process.

### Direct Organizing Mode
```bash
python main.py --organize
```
Skips the homepage and starts organizing immediately.

### Help
```bash
python main.py --help
```

## 🎮 Controls During Organization

| Command | Action |
|---------|--------|
| `Enter` or `s` | Skip current song |
| `1`, `2`, `3`... | Add to playlist by number |
| `1,3,5` | Add to multiple playlists |
| `n` | Create new playlist and add song |
| `p` | Play/stop 30-second local preview |
| `o` | Open song in Spotify |
| `b` | Go back to previous song |
| `q` | Quit and save progress |

## 📁 File Structure

```
spotiorganize/
├── main.py                    # Main application
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── .gitignore               # Git ignore rules
├── LICENSE                  # MIT License
├── SETUP.md                 # Detailed setup guide
├── .config                  # Auto-generated credentials (not in git)
├── logs/                    # Application logs directory
│   └── spotify_organizer_*.log
├── session.log              # Simple session activity log
├── processed_tracks.log     # Tracks that have been processed
└── .cache-spotify-organizer # Spotify OAuth cache
```

## 📊 Logging

The application creates comprehensive logs:

- **Application logs**: Stored in `logs/spotify_organizer_TIMESTAMP.log` with detailed debugging information
- **Session log**: Simple activity log in `session.log` showing what you did during each session
- **Processed tracks**: `processed_tracks.log` keeps track of songs you've already organized

## 🔧 Configuration

### Credential Storage
Credentials are stored in `.config` file in JSON format:
```json
{
  "spotify_client_id": "your_client_id",
  "spotify_client_secret": "your_client_secret", 
  "spotify_redirect_uri": "http://127.0.0.1:8888",
  "created_at": "2024-01-01T12:00:00"
}
```

### Spotify API Scopes
The application requests these Spotify permissions:
- `user-library-read` - Read your liked songs
- `playlist-read-private` - Read your private playlists
- `playlist-read-collaborative` - Read collaborative playlists
- `playlist-modify-public` - Modify public playlists
- `playlist-modify-private` - Modify private playlists
- `user-read-playback-state` - See your current playback
- `user-modify-playback-state` - Control playback on your devices

## 🐛 Troubleshooting

### No Spotify devices found
- Make sure Spotify is open and active on at least one device (phone, desktop, web player)
- Try playing a song first to activate the device
- Check that your device is connected to the same network

### Authentication errors
- Verify your Client ID and Secret are correct
- Check that your redirect URI is set to `http://127.0.0.1:8888`
- Delete `.cache-spotify-organizer` and `.config` files to reset authentication

### Local preview not working
- Install pygame: `pip install pygame`
- Some songs may not have preview URLs available

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Spotipy](https://spotipy.readthedocs.io/) - Python Spotify API wrapper
- [Pygame](https://www.pygame.org/) - For local audio preview functionality
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) - For all the music data

## ⭐ Support

If you find this tool useful, please give it a star on GitHub! It helps others discover the project.

For issues, questions, or suggestions, please open an issue on GitHub.
