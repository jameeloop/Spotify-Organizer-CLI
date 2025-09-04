#!/usr/bin/env python3
"""
Spotify Playlist Organizer CLI
A tool to help organize your Spotify liked songs into playlists with device playback support.
"""
import os
import sys
import time
import webbrowser
import contextlib
import tempfile
import requests
import argparse
from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Optional local 30s previews (not needed for device playback)
try:
    with contextlib.redirect_stdout(open(os.devnull, "w")):
        import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class SpotifyOrganizerCLI:
    def __init__(self, client_id, client_secret, redirect_uri):
        """Initialize the Spotify Organizer with credentials."""
        # Scopes: read playlists & library, modify playlists, and control playback on a device
        self.scope = (
            "user-library-read "
            "playlist-read-private "
            "playlist-read-collaborative "
            "playlist-modify-public "
            "playlist-modify-private "
            "user-read-playback-state "
            "user-modify-playback-state"
        )

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=self.scope,
                cache_path=".cache-spotify-organizer",
                show_dialog=True,
                open_browser=True,
            )
        )

        me = self.sp.current_user()
        self.user_id = me["id"]

        self.user_playlists = {}
        self.custom_playlists = {}
        self.songs = []
        self.current_index = 0
        self.skipped_count = 0
        self.is_playing_preview = False
        self.temp_file = None
        self.device_id = None  # will be set once at startup

        # Persistent logging to avoid repeats
        self.processed_log_path = "processed_tracks.log"
        self.processed_ids = self.load_processed_ids()

        if AUDIO_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            except Exception:
                pass

        print(f"✅ Authenticated as: {self.user_id}")

    def load_processed_ids(self):
        """Load previously processed track IDs from log file."""
        ids = set()
        if os.path.exists(self.processed_log_path):
            try:
                with open(self.processed_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        tid = line.strip()
                        if tid:
                            ids.add(tid)
            except Exception:
                pass
        return ids

    def mark_processed(self, track_id):
        """Persist that we've handled this track so it doesn't repeat next run."""
        if not track_id or track_id in self.processed_ids:
            return
        self.processed_ids.add(track_id)
        try:
            with open(self.processed_log_path, "a", encoding="utf-8") as f:
                f.write(track_id + "\n")
        except Exception:
            pass

    def can_clear(self):
        """Check if we can clear the terminal screen."""
        # Avoid "TERM environment variable not set" in some IDEs/Windows
        return os.name == "nt" or ("TERM" in os.environ and os.environ["TERM"])

    def clear_screen(self):
        """Clear the terminal screen."""
        if self.can_clear():
            os.system("cls" if os.name == "nt" else "clear")
        else:
            print("\n" * 3)

    def print_header(self):
        """Print the application header."""
        print("🎵" + "=" * 60 + "🎵")
        print("           SPOTIFY PLAYLIST ORGANIZER CLI")
        print("🎵" + "=" * 60 + "🎵")

    def print_progress(self):
        """Print current progress information."""
        total = len(self.songs)
        current = min(self.current_index + 1, total) if total else 0
        pct = (current / total) * 100 if total > 0 else 0
        bar_len = 40
        filled = int(bar_len * current // total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\n📊 Progress: [{bar}] {current}/{total} ({pct:.1f}%)")
        print(f"⏭️  Skipped: {self.skipped_count} songs")
        if self.custom_playlists:
            total_in_custom = sum(len(s) for s in self.custom_playlists.values())
            print(f"🆕 Songs in new playlists: {total_in_custom}")

    def get_user_playlists(self):
        """Fetch all user playlists from Spotify."""
        print("🔄 Loading your existing playlists...")
        offset = 0
        total_seen = 0
        while True:
            try:
                playlists = self.sp.current_user_playlists(limit=50, offset=offset)
                items = playlists.get("items", [])
                if not items:
                    break
                total_seen += len(items)
                print(f"   Fetched {len(items)} playlists at offset {offset} (total seen: {total_seen})")
                for pl in items:
                    if pl["owner"]["id"] == self.user_id or pl.get("collaborative", False):
                        self.user_playlists[pl["name"]] = pl["id"]
                if playlists.get("next"):
                    offset += 50
                else:
                    break
            except Exception as e:
                print(f"❌ Error loading playlists: {e}")
                break
        print(f"📋 Found {len(self.user_playlists)} of your modifiable playlists")

    def get_liked_songs(self):
        """Fetch all liked songs from Spotify."""
        print("🔄 Fetching your liked songs...")
        try:
            results = self.sp.current_user_saved_tracks(limit=50)
            while results:
                items = results.get("items", [])
                for it in items:
                    if it and it.get("track"):
                        self.songs.append(it["track"])
                print(f"   Loaded {len(self.songs)} songs...")
                if results.get("next"):
                    results = self.sp.next(results)
                else:
                    break
            print(f"✅ Found {len(self.songs)} liked songs")
        except Exception as e:
            print(f"❌ Error fetching liked songs: {e}")

    def select_device_once(self):
        """Pick a device once at startup. If only one exists, use it. If none, prompt until available."""
        while True:
            try:
                devices = self.sp.devices().get("devices", [])
            except Exception as e:
                print(f"❌ Error listing devices: {e}")
                devices = []

            if not devices:
                print("📵 No active Spotify devices found.")
                input("➡️  Open Spotify on your phone/desktop, then press Enter to retry...")
                continue

            if len(devices) == 1:
                d = devices[0]
                self.device_id = d["id"]
                print(f"📱 Using device: {d['name']} ({d['type']})")
                return

            print("\n📱 Available devices:")
            for i, d in enumerate(devices, 1):
                active = " (active)" if d.get("is_active") else ""
                print(f"  {i}. {d['name']} - {d['type']}{active}")

            sel = input("Select device number to auto-use for playback: ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(devices):
                self.device_id = devices[int(sel) - 1]["id"]
                print(f"✅ Selected: {devices[int(sel) - 1]['name']}")
                return
            print("❌ Invalid selection. Try again.")

    def play_on_device(self, song):
        """Start playback of the full track on the selected device."""
        if not self.device_id:
            return False
        try:
            self.sp.start_playback(device_id=self.device_id, uris=[song["uri"]])
            return True
        except spotipy.exceptions.SpotifyException as se:
            try:
                code = getattr(se, "http_status", None)
            except Exception:
                code = None
            print(f"⚠️  Spotify playback error ({code}). Re-selecting device...")
            self.select_device_once()
            try:
                self.sp.start_playback(device_id=self.device_id, uris=[song["uri"]])
                return True
            except Exception as e2:
                print(f"❌ Could not start playback: {e2}")
                return False
        except Exception as e:
            print(f"❌ Error starting playback: {e}")
            return False

    def pause_device(self):
        """Pause playback on the selected device."""
        if not self.device_id:
            return
        try:
            self.sp.pause_playback(device_id=self.device_id)
        except Exception:
            pass

    def play_preview(self, preview_url, song=None):
        """Play a 30-second local preview of the song."""
        if not AUDIO_AVAILABLE:
            print("🔇 Local audio (pygame) not available")
            return False

        data = None
        source = None

        # Try Spotify 30s URL first
        if preview_url:
            try:
                r = requests.get(preview_url, timeout=10)
                r.raise_for_status()
                data = r.content
                source = "Spotify"
            except Exception:
                pass

        # Fallback to iTunes sample
        if data is None and song:
            try:
                artist = song["artists"][0]["name"]
                title = song["name"]
                q = f"{artist} {title}"
                url = "https://itunes.apple.com/search"
                params = {"term": q, "entity": "song", "limit": 1}
                r = requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                js = r.json()
                if js.get("results"):
                    preview = js["results"][0].get("previewUrl")
                    if preview:
                        r2 = requests.get(preview, timeout=10)
                        r2.raise_for_status()
                        data = r2.content
                        source = "iTunes"
            except Exception:
                pass

        if data is None:
            print("🔇 No preview available (Spotify/iTunes).")
            return False

        try:
            self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            self.temp_file.write(data)
            self.temp_file.close()
            pygame.mixer.music.load(self.temp_file.name)
            pygame.mixer.music.play()
            self.is_playing_preview = True
            print(f"🎵 Playing 30s preview from {source}...")
            return True
        except Exception as e:
            print(f"❌ Preview error: {e}")
            return False

    def stop_preview(self):
        """Stop the currently playing preview."""
        try:
            if AUDIO_AVAILABLE and pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_playing_preview = False
        if self.temp_file and os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except Exception:
                pass
            self.temp_file = None

    def display_song_info(self, song):
        """Display information about the current song."""
        self.clear_screen()
        self.print_header()
        self.print_progress()

        artists = ", ".join(a["name"] for a in song.get("artists", [])[:3]) or "Unknown"
        album = (song.get("album") or {}).get("name") or "Unknown"
        release_date = (song.get("album") or {}).get("release_date") or ""
        year = release_date[:4] if release_date else "Unknown"
        duration_ms = song.get("duration_ms") or 0
        popularity = song.get("popularity")
        duration_txt = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"

        print(f"\n🎤 Artist: {artists}")
        print(f"🎧 Song: {song.get('name') or 'Unknown'}")
        print(f"💿 Album: {album}")
        print(f"📅 Year: {year}")
        print(f"⏱️  Duration: {duration_txt}")
        print(f"🔥 Popularity: {popularity if popularity is not None else 'Unknown'}/100")
        print("\n" + "─" * 60)

        # Auto-play the full track on selected device
        ok = self.play_on_device(song)
        if ok:
            print("▶️  Playing on your Spotify device (auto).")
        else:
            print("❌ Could not auto-play on device. Open Spotify on a device and try again with the next song.")

    def show_playlist_options(self):
        """Display available playlist options."""
        print(f"\n📋 PLAYLIST OPTIONS:")
        print("─" * 40)

        option_num = 1
        if self.user_playlists:
            print("🗂️  EXISTING PLAYLISTS:")
            for playlist_name in sorted(self.user_playlists.keys(), key=lambda s: s.lower()):
                print(f"   {option_num:2d}. {playlist_name}")
                option_num += 1

        if self.custom_playlists:
            print("\n🆕 NEW PLAYLISTS (this session):")
            for playlist_name, songs in self.custom_playlists.items():
                print(f"   {option_num:2d}. {playlist_name} ({len(songs)} songs)")
                option_num += 1

        print(f"\n   n.  Create new playlist (adds this song)")
        print(f"   s.  Skip this song (also Enter)")
        print(f"   p.  Play/stop 30s local preview (optional)")
        print(f"   o.  Open in Spotify")
        print(f"   b.  Go back to previous song")
        print(f"   q.  Quit and save progress")
        print("\n💡 Tip: Enter multiple numbers separated by commas to add to several playlists, e.g. 1,3,5")
        return option_num - 1

    def parse_multi_numbers(self, s, max_option):
        """Parse '1,3,5' into [1,3,5]. Return None if invalid."""
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if not parts:
            return None
        nums = []
        for p in parts:
            if not p.isdigit():
                return None
            n = int(p)
            if not (1 <= n <= max_option):
                return None
            nums.append(n)
        # De-duplicate but preserve order
        seen = set()
        result = []
        for n in nums:
            if n not in seen:
                seen.add(n)
                result.append(n)
        return result

    def get_user_choice(self, max_option):
        """Get user input for playlist selection."""
        while True:
            try:
                choice = input(f"\n🎯 Enter your choice: ").strip().lower()
                if choice == "":
                    return "skip"
                if choice in {"q", "quit"}:
                    return "quit"
                if choice in {"s", "skip"}:
                    return "skip"
                if choice in {"n", "new"}:
                    return "new"
                if choice in {"p", "preview"}:
                    return "preview"
                if choice in {"o", "open", "spotify"}:
                    return "spotify"
                if choice in {"b", "back"}:
                    return "back"
                # Multi-number (comma-separated) or single number
                if "," in choice or choice.isdigit():
                    nums = self.parse_multi_numbers(choice, max_option)
                    if nums:
                        return nums  # list of ints
                    print(f"❌ Enter numbers between 1 and {max_option}, separated by commas.")
                else:
                    print("❌ Invalid choice. Try again.")
            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                return "quit"
            except Exception:
                print("❌ Invalid input. Try again.")

    def create_new_playlist_name(self):
        """Get name for a new playlist from user."""
        while True:
            try:
                name = input("\n🏷️  Enter new playlist name: ").strip()
                if name:
                    if name not in self.user_playlists and name not in self.custom_playlists:
                        return name
                    else:
                        print("❌ Playlist with that name already exists!")
                else:
                    print("❌ Please enter a valid name!")
            except KeyboardInterrupt:
                return None

    def add_song_to_existing_playlist(self, song, playlist_index):
        """Add song to an existing Spotify playlist."""
        try:
            playlist_names = sorted(self.user_playlists.keys(), key=lambda s: s.lower())
            playlist_name = playlist_names[playlist_index - 1]
            playlist_id = self.user_playlists[playlist_name]
            self.sp.playlist_add_items(playlist_id, [song["uri"]])
            print(f"✅ Added to '{playlist_name}'")
            return True
        except Exception as e:
            print(f"❌ Error adding to playlist: {e}")
            return False

    def add_song_to_custom_playlist(self, song, playlist_index):
        """Add song to a custom (new) playlist."""
        try:
            existing_count = len(self.user_playlists)
            custom_names = list(self.custom_playlists.keys())
            playlist_name = custom_names[playlist_index - existing_count - 1]
            self.custom_playlists[playlist_name].append(song)
            print(f"✅ Added to new playlist '{playlist_name}' ({len(self.custom_playlists[playlist_name])} songs)")
            return True
        except Exception as e:
            print(f"❌ Error adding to custom playlist: {e}")
            return False

    def handle_playlist_choice(self, song, choice, max_option):
        """Handle adding song to selected playlist."""
        existing_count = len(self.user_playlists)
        if choice <= existing_count:
            return self.add_song_to_existing_playlist(song, choice)
        else:
            return self.add_song_to_custom_playlist(song, choice)

    def create_custom_playlists(self):
        """Create all custom playlists on Spotify."""
        if not self.custom_playlists:
            return
        print("\n🚀 Creating new playlists on Spotify...")
        self.logger.info("Starting to create custom playlists on Spotify")
        for playlist_name, songs in self.custom_playlists.items():
            try:
                print(f"   Creating '{playlist_name}'...")
                playlist = self.sp.user_playlist_create(
                    user=self.user_id,
                    name=playlist_name,
                    public=False,
                    description=f"Created with Spotify Organizer CLI - {len(songs)} songs",
                )
                song_uris = [s["uri"] for s in songs if s.get("uri")]
                for i in range(0, len(song_uris), 100):
                    self.sp.playlist_add_items(playlist["id"], song_uris[i: i + 100])
                print(f"✅ Created '{playlist_name}' with {len(songs)} songs")

                # Log playlist creation
                self.log_session_action("CREATED_PLAYLIST", playlist_name=playlist_name)
                self.logger.info(f"Successfully created playlist '{playlist_name}' with {len(songs)} songs")

            except Exception as e:
                print(f"❌ Error creating playlist '{playlist_name}': {e}")
                self.logger.error(f"Error creating playlist '{playlist_name}': {e}")

    def start_organizing(self):
        """Main organizing loop."""
        print("\n🎵 SPOTIFY PLAYLIST ORGANIZER CLI")
        print("=" * 50)
        self.logger.info("Starting organizing session")
        self.log_session_action("SESSION_START")

        self.get_user_playlists()
        self.get_liked_songs()
        if not self.songs:
            print("❌ No liked songs found!")
            self.logger.warning("No liked songs found")
            return

        # Filter out already-processed songs
        initial_total = len(self.songs)
        self.songs = [t for t in self.songs if t.get("id") not in self.processed_ids]
        if len(self.songs) < initial_total:
            skipped_count = initial_total - len(self.songs)
            print(f"🧠 Skipping {skipped_count} previously processed songs (from log).")
            self.logger.info(f"Filtered out {skipped_count} previously processed songs")

        # Pick device once and auto-play thereafter
        self.select_device_once()

        print(f"\n🎯 Ready to organize {len(self.songs)} songs!")
        print("ℹ️  Auto-plays each track on your selected device.")
        print("ℹ️  Press Enter to skip; numbers add to a playlist; 'n' makes a new playlist; use commas for multiple.")
        input("\nPress Enter to start...")

        self.logger.info(f"Starting main organizing loop with {len(self.songs)} songs")

        while 0 <= self.current_index < len(self.songs):
            song = self.songs[self.current_index]

            # If this song was processed meanwhile, skip it
            if song.get("id") in self.processed_ids:
                self.current_index += 1
                continue

            # Show info & auto-play on device
            self.display_song_info(song)

            # Options
            max_option = self.show_playlist_options()
            choice = self.get_user_choice(max_option)

            # Stop any local preview if running
            self.stop_preview()

            track_name = f"{song.get('name', 'Unknown')} - {', '.join(a['name'] for a in song.get('artists', []))}"

            if choice == "quit":
                print("\n💾 Saving progress and quitting...")
                self.logger.info("User quit the session")
                self.log_session_action("SESSION_QUIT")
                break

            elif choice == "skip":
                self.skipped_count += 1
                # Mark processed so we don't see it again next run
                self.mark_processed(song.get("id"))
                self.log_session_action("SKIPPED", track_name)
                self.logger.debug(f"User skipped track: {track_name}")
                self.current_index += 1
                continue

            elif choice == "back":
                if self.current_index > 0:
                    self.current_index -= 1
                    self.logger.debug("User went back to previous song")
                else:
                    print("❌ Already at first song")
                continue

            elif choice == "preview":
                # Optional local 30s preview (doesn't affect device playback)
                if self.is_playing_preview:
                    self.stop_preview()
                    print("⏸️  Preview stopped")
                else:
                    if not self.play_preview(song.get("preview_url"), song):
                        print("🔇 No preview available")
                time.sleep(0.4)
                continue

            elif choice == "spotify":
                url = song.get("external_urls", {}).get("spotify")
                if url:
                    webbrowser.open(url)
                    print("🎧 Opened in Spotify")
                    self.log_session_action("OPENED_IN_SPOTIFY", track_name)
                else:
                    print("❌ No Spotify URL for this track")
                time.sleep(0.4)
                continue

            elif choice == "new":
                new_name = self.create_new_playlist_name()
                if new_name:
                    self.custom_playlists[new_name] = [song]
                    print(f"✅ Created new playlist '{new_name}' and added song")
                    # Persist & next
                    self.mark_processed(song.get("id"))
                    self.log_session_action("CREATED_NEW_PLAYLIST_WITH_SONG", track_name, new_name)
                    self.logger.info(f"Created new playlist '{new_name}' with track '{track_name}'")
                    self.current_index += 1
                continue

            elif isinstance(choice, list):
                # Add to multiple playlists by numbers
                any_success = False
                for opt in choice:
                    if self.handle_playlist_choice(song, opt, max_option):
                        any_success = True
                if any_success:
                    self.mark_processed(song.get("id"))
                    self.current_index += 1
                else:
                    print("⚠️  Could not add to any selected playlists.")
                continue

        # Wrap up
        if self.custom_playlists:
            self.create_custom_playlists()

        self.clear_screen()
        self.print_header()
        print("🎉 ORGANIZING COMPLETE!")
        print("=" * 50)
        print(f"📊 Total songs processed: {self.current_index}")
        print(f"⏭️  Songs skipped: {self.skipped_count}")
        if self.custom_playlists:
            print(f"🆕 New playlists created: {len(self.custom_playlists)}")
            for name, songs in self.custom_playlists.items():
                print(f"   • {name}: {len(songs)} songs")
        print("\n✨ All done! Check your Spotify app for the new playlists.")

        # Final logging
        self.log_session_action("SESSION_COMPLETE")
        self.logger.info(
            f"Session completed. Processed: {self.current_index}, Skipped: {self.skipped_count}, New playlists: {len(self.custom_playlists)}")
        self.songs = [t for t in self.songs if t.get("id") not in self.processed_ids]
        if len(self.songs) < initial_total:
            print(f"🧠 Skipping {initial_total - len(self.songs)} previously processed songs (from log).")

        # Pick device once and auto-play thereafter
        self.select_device_once()

        print(f"\n🎯 Ready to organize {len(self.songs)} songs!")
        print("ℹ️  Auto-plays each track on your selected device.")
        print("ℹ️  Press Enter to skip; numbers add to a playlist; 'n' makes a new playlist; use commas for multiple.")
        input("\nPress Enter to start...")

        while 0 <= self.current_index < len(self.songs):
            song = self.songs[self.current_index]

            # If this song was processed meanwhile, skip it
            if song.get("id") in self.processed_ids:
                self.current_index += 1
                continue

            # Show info & auto-play on device
            self.display_song_info(song)

            # Options
            max_option = self.show_playlist_options()
            choice = self.get_user_choice(max_option)

            # Stop any local preview if running
            self.stop_preview()

            if choice == "quit":
                print("\n💾 Saving progress and quitting...")
                break

            elif choice == "skip":
                self.skipped_count += 1
                # Mark processed so we don't see it again next run
                self.mark_processed(song.get("id"))
                self.current_index += 1
                continue

            elif choice == "back":
                if self.current_index > 0:
                    self.current_index -= 1
                else:
                    print("❌ Already at first song")
                continue

            elif choice == "preview":
                # Optional local 30s preview (doesn't affect device playback)
                if self.is_playing_preview:
                    self.stop_preview()
                    print("⏸️  Preview stopped")
                else:
                    if not self.play_preview(song.get("preview_url"), song):
                        print("🔇 No preview available")
                time.sleep(0.4)
                continue

            elif choice == "spotify":
                url = song.get("external_urls", {}).get("spotify")
                if url:
                    webbrowser.open(url)
                    print("🎧 Opened in Spotify")
                else:
                    print("❌ No Spotify URL for this track")
                time.sleep(0.4)
                continue

            elif choice == "new":
                new_name = self.create_new_playlist_name()
                if new_name:
                    self.custom_playlists[new_name] = [song]
                    print(f"✅ Created new playlist '{new_name}' and added song")
                    # Persist & next
                    self.mark_processed(song.get("id"))
                    self.current_index += 1
                continue

            elif isinstance(choice, list):
                # Add to multiple playlists by numbers
                any_success = False
                for opt in choice:
                    if self.handle_playlist_choice(song, opt, max_option):
                        any_success = True
                if any_success:
                    self.mark_processed(song.get("id"))
                    self.current_index += 1
                else:
                    print("⚠️  Could not add to any selected playlists.")
                continue

        # Wrap up
        if self.custom_playlists:
            self.create_custom_playlists()

        self.clear_screen()
        self.print_header()
        print("🎉 ORGANIZING COMPLETE!")
        print("=" * 50)
        print(f"📊 Total songs processed: {self.current_index}")
        print(f"⏭️  Songs skipped: {self.skipped_count}")
        if self.custom_playlists:
            print(f"🆕 New playlists created: {len(self.custom_playlists)}")
            for name, songs in self.custom_playlists.items():
                print(f"   • {name}: {len(songs)} songs")
        print("\n✨ All done! Check your Spotify app for the new playlists.")


def show_homepage():
    """Display the CLI homepage."""

    # ===== Fancy ASCII banner (homepage) =====
    title = "SPOTIFY PLAYLIST ORGANIZER"
    subtitle = "CLI"
    width = 70
    top = "╔" + "═" * width + "╗"
    mid_empty = "║" + " " * width + "║"
    line_title = "║" + title.center(width) + "║"
    line_sub = "║" + ("♪ ♫ ♪  ORGANIZE YOUR LIKED SONGS  ♪ ♫ ♪").center(width) + "║"
    bottom = "╚" + "═" * width + "╝"
    print("\033[92m" + top)
    print(mid_empty)
    print(line_title)
    print("║" + subtitle.center(width) + "║")
    print(line_sub)
    print(mid_empty)
    print(bottom + "\033[0m")
    print()
    # =========================================
    print("📖 ABOUT:")
    print("   A powerful CLI tool to help you organize your Spotify liked songs")
    print("   into playlists with automatic device playback support.")
    print()
    print("✨ FEATURES:")
    print("   • Auto-play songs on your Spotify devices while organizing")
    print("   • Create new playlists or add to existing ones")
    print("   • Add songs to multiple playlists at once")
    print("   • Resume where you left off (tracks processed songs)")
    print("   • Optional 30-second local previews")
    print("   • Open songs directly in Spotify")
    print()
    print("🔧 REQUIREMENTS:")
    print("   • Python 3.6+")
    print("   • spotipy library")
    print("   • Spotify Developer App credentials")
    print("   • pygame (optional, for local previews)")
    print()
    print("📝 SETUP:")
    print("   1. Create a Spotify Developer App at https://developer.spotify.com")
    print("   2. Set redirect URI to http://127.0.0.1:8888")
    print("   3. Run the app - it will prompt for your Client ID and Secret")
    print("   4. Credentials are saved to .config file for future use")
    print()
    print("🚀 USAGE:")
    print("   python main.py                    # Interactive mode")
    print("   python main.py --organize         # Start organizing immediately")
    print("   python main.py --help             # Show help")
    print()
    print("🎯 CONTROLS (during organizing):")
    print("   Enter / 's'    : Skip song")
    print("   1,2,3...       : Add to playlist(s) by number")
    print("   1,3,5          : Add to multiple playlists")
    print("   'n'            : Create new playlist")
    print("   'p'            : Play/stop local preview")
    print("   'o'            : Open in Spotify")
    print("   'b'            : Go back to previous song")
    print("   'q'            : Quit and save progress")
    print()
    print("=" * 76)


def load_credentials():
    """Load Spotify credentials from environment variables or .env file."""
    # Try to load from .env file
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8888')

    if not client_id or not client_secret:
        print("❌ Missing Spotify credentials!")
        print("   Please set environment variables or create a .env file with:")
        print("   SPOTIFY_CLIENT_ID=your_client_id")
        print("   SPOTIFY_CLIENT_SECRET=your_client_secret")
        print("   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888")
        sys.exit(1)

    return client_id, client_secret, redirect_uri


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Spotify Playlist Organizer CLI')
    parser.add_argument('--organize', action='store_true',
                        help='Start organizing immediately (skip homepage)')
    parser.add_argument('--version', action='version', version='1.0.0')

    args = parser.parse_args()

    if not args.organize:
        show_homepage()

        while True:
            choice = input("\n🎯 \033[96mWhat would you like to do?\033[0m\n"
                           "   \033[92m1.\033[0m Start organizing songs\n"
                           "   \033[91m2.\033[0m Exit\n"
                           "   \033[93mChoice:\033[0m ").strip()

            if choice == '1':
                break
            elif choice == '2':
                print("👋 Goodbye!")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")

    try:
        client_id, client_secret, redirect_uri = load_credentials()
        app = SpotifyOrganizerCLI(client_id, client_secret, redirect_uri)
        app.start_organizing()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your Spotify credentials, redirect URI, and that Spotify is open on a device.")


if __name__ == "__main__":
    main()