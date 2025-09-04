# Setup Guide

## Step-by-Step Setup Instructions

### 1. Create a Spotify Developer App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create an App"**
4. Fill in the form:
   - **App Name**: `My Playlist Organizer` (or any name you prefer)
   - **App Description**: `CLI tool to organize my Spotify playlists`
   - **Website**: Leave blank or put your GitHub repo URL
   - Check the boxes to agree to terms
5. Click **"Create"**

### 2. Configure Your App

1. Click on your newly created app
2. Click **"Settings"** in the top right
3. In the **"Redirect URIs"** section:
   - Click **"Add Redirect URI"**
   - Enter: `http://127.0.0.1:8888`
   - Click **"Add"**
   - Click **"Save"** at the bottom
4. Note down your **Client ID** (visible on the main app page)
5. Click **"View client secret"** and note down your **Client Secret**

### 3. Install and Run

1. Clone/download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```
4. When prompted, enter your Client ID and Client Secret from step 2
5. Your credentials will be saved automatically for future use

### 4. First-Time Authentication

1. The app will open a browser window asking you to log into Spotify
2. Click **"Agree"** to grant the requested permissions
3. You'll be redirected to a page that might show an error - this is normal!
4. Copy the entire URL from your browser's address bar
5. Paste it into the terminal when prompted
6. Authentication is now complete!

## Troubleshooting

### "No module named 'spotipy'" Error
```bash
pip install spotipy requests pygame
```

### "Invalid redirect URI" Error
- Double-check that you added `http://127.0.0.1:8888` as a redirect URI in your Spotify app settings
- Make sure there are no extra spaces or characters

### "Invalid client" Error
- Verify your Client ID and Client Secret are correct
- Try deleting the `.config` file and re-entering your credentials

### No Spotify Devices Found
- Open Spotify on your phone, computer, or web browser
- Start playing any song to activate the device
- Make sure your device is connected to the internet

## What the App Does

1. **Fetches your liked songs** - All songs you've hearted/liked on Spotify
2. **Shows each song** - Displays artist, title, album, year, etc.
3. **Auto-plays songs** - Starts playing each song on your selected Spotify device
4. **Lets you organize** - Add songs to existing playlists or create new ones
5. **Remembers progress** - Won't show you the same songs again in future runs
6. **Creates playlists** - Actually creates new playlists on your Spotify account

## Privacy & Security

- Your credentials are stored locally in a `.config` file
- No data is sent to any external servers (except Spotify's official API)
- All playlist modifications happen on your own Spotify account
- You can revoke app access anytime in your [Spotify Account Settings](https://www.spotify.com/account/apps/)

## Need Help?

If you run into issues, check the logs in the `logs/` directory for detailed error information, or open an issue on the GitHub repository.