import sys
import os
import json
import pickle
from PyQt5.QtCore import Qt, QUrl, QTimer, QByteArray, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QLabel,
    QSlider,
    QFileDialog,
    QFrame,
    QSizePolicy,
    QInputDialog,
    QMessageBox,
    QLineEdit,
    QDialog,
    QComboBox,
    QStackedWidget,
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC


# Embedded SVG icons as QIcon for consistent cross-platform look
def icon_from_svg(svg_content):
    pixmap = QPixmap()
    pixmap.loadFromData(QByteArray(svg_content.encode("utf-8")), "SVG")
    return QIcon(pixmap)


SVG_PLAY = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<path d="M8 5v14l11-7z"/>
</svg>
"""

SVG_PAUSE = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<path d="M6 19h4V5H6v14zM14 5v14h4V5h-4z"/>
</svg>
"""

SVG_NEXT = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
</svg>
"""

SVG_PREV = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<path d="M6 6l8.5 6L6 18V6zM16 6v12h2V6h-2z"/>
</svg>
"""

SVG_SEARCH = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
</svg>
"""

SVG_HOME = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
</svg>
"""

SVG_PLAYLIST = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/>
</svg>
"""

SVG_DISCOVER = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<path d="M12 10.9c-.61 0-1.1.49-1.1 1.1s.49 1.1 1.1 1.1c.61 0 1.1-.49 1.1-1.1s-.49-1.1-1.1-1.1zM12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm2.19 12.19L6 18l3.81-8.19L18 6l-3.81 8.19z"/>
</svg>
"""

# Default album art SVG
SVG_DEFAULT_ALBUM = """
<svg height="200px" viewBox="0 0 200 200" width="200px" fill="#E63946" xmlns="http://www.w3.org/2000/svg">
<rect width="200" height="200" fill="#121212"/>
<circle cx="100" cy="100" r="50" fill="#E63946" opacity="0.7"/>
<circle cx="100" cy="100" r="30" fill="#121212"/>
<circle cx="100" cy="100" r="5" fill="#E63946"/>
</svg>
"""


class PlaylistManager:
    def __init__(self):
        self.playlists = {}
        self.current_playlist = "Default"
        self.playlists_file = os.path.join(os.path.expanduser("~"), ".muse_playlists.json")
        self.load_playlists()

    def load_playlists(self):
        try:
            if os.path.exists(self.playlists_file):
                with open(self.playlists_file, 'r') as f:
                    self.playlists = json.load(f)
                    
                if not self.playlists:
                    self.playlists = {"Default": []}
            else:
                self.playlists = {"Default": []}
        except Exception as e:
            print(f"Error loading playlists: {e}")
            self.playlists = {"Default": []}

    def save_playlists(self):
        try:
            with open(self.playlists_file, 'w') as f:
                json.dump(self.playlists, f)
        except Exception as e:
            print(f"Error saving playlists: {e}")

    def create_playlist(self, name):
        if name not in self.playlists:
            self.playlists[name] = []
            self.save_playlists()
            return True
        return False

    def add_to_playlist(self, playlist_name, track_path, track_metadata):
        if playlist_name in self.playlists:
            track_info = {
                "path": track_path,
                "title": track_metadata["title"],
                "artist": track_metadata["artist"]
            }
            self.playlists[playlist_name].append(track_info)
            self.save_playlists()
            return True
        return False

    def remove_from_playlist(self, playlist_name, index):
        if playlist_name in self.playlists and 0 <= index < len(self.playlists[playlist_name]):
            self.playlists[playlist_name].pop(index)
            self.save_playlists()
            return True
        return False

    def delete_playlist(self, name):
        if name in self.playlists and name != "Default":
            del self.playlists[name]
            self.save_playlists()
            return True
        return False

    def get_playlist(self, name):
        return self.playlists.get(name, [])

    def get_playlist_names(self):
        return list(self.playlists.keys())


class SearchDialog(QDialog):
    def __init__(self, parent=None, track_paths=None, track_metadatas=None):
        super().__init__(parent)
        self.setWindowTitle("Search Music")
        self.setMinimumWidth(400)
        self.setStyleSheet(parent.dark_theme_stylesheet())

        self.track_paths = track_paths or []
        self.track_metadatas = track_metadatas or []

        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title or artist...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        self.search_input.textChanged.connect(self.perform_search)

        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #121212;
                color: #b3b3b3;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item:selected {
                background-color: #E63946;
                color: white;
            }
        """)

        layout.addWidget(QLabel("Search Your Music"))
        layout.addWidget(self.search_input)
        layout.addWidget(self.results_list)

        button_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #E63946;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F56476;
            }
        """)
        self.play_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def perform_search(self, query):
        self.results_list.clear()
        if not query.strip():
            return

        query = query.lower()
        for i, metadata in enumerate(self.track_metadatas):
            title = metadata.get("title", "").lower()
            artist = metadata.get("artist", "").lower()
            
            if query in title or query in artist:
                display_name = metadata.get("title", "Unknown")
                if metadata.get("artist"):
                    display_name += f" - {metadata['artist']}"
                self.results_list.addItem(display_name)
                # Store the index as item data
                self.results_list.item(self.results_list.count() - 1).setData(Qt.UserRole, i)

    def get_selected_index(self):
        current_item = self.results_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return -1


class SpotifyLikePlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Muse Music Player")
        self.setGeometry(200, 100, 900, 600)
        self.setMinimumSize(700, 400)
        self.setStyleSheet(self.dark_theme_stylesheet())
        
        # Track file paths and metadata for album art retrieval
        self.track_paths = []
        self.track_metadatas = []
        self.current_track_info = {"title": "", "artist": ""}
        self.last_folder_path = ""
        self.library_file = os.path.join(os.path.expanduser("~"), ".muse_library.dat")

        # Playlist manager
        self.playlist_manager = PlaylistManager()

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Content area with stacked widget for different views
        self.content_area = QStackedWidget()
        main_layout.addWidget(self.content_area)

        # Create different views
        self.main_view = self.create_main_view()
        self.playlist_view = self.create_playlist_view()

        # Add views to stacked widget
        self.content_area.addWidget(self.main_view)
        self.content_area.addWidget(self.playlist_view)

        # Media player setup
        self.player = QMediaPlayer()
        self.media_playlist = QMediaPlaylist()
        self.player.setPlaylist(self.media_playlist)

        # Connect signals
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected_song)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.media_playlist.currentIndexChanged.connect(self.song_changed)

        # Timer to update slider while playing
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_position)

        # Start with volume 50
        self.player.setVolume(50)
        self.volume_slider.setValue(50)
        
        # Load previous library if it exists
        self.load_library()

    def create_main_view(self):
        main_view = QWidget()
        layout = QVBoxLayout(main_view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Album art and info section
        self.album_section = self.create_album_section()
        layout.addWidget(self.album_section)

        # Title of currently playing / playlist name
        self.title_label = QLabel("Now Playing")
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        layout.addWidget(self.title_label)

        # Playlist widget (list of songs)
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet(
            """
            QListWidget {
                background-color: #121212;
                color: #b3b3b3;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item:selected {
                background-color: #E63946;
                color: white;
            }
            """
        )
        layout.addWidget(self.playlist_widget)

        # Playback controls area
        self.controls_area = self.create_controls()
        layout.addWidget(self.controls_area)

        return main_view

    def create_playlist_view(self):
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Title
        title = QLabel("Your Playlists")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Playlists dropdown
        self.playlists_dropdown = QComboBox()
        self.playlists_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                color: white;
                selection-background-color: #E63946;
            }
        """)
        self.playlists_dropdown.currentIndexChanged.connect(self.load_selected_playlist)
        layout.addWidget(self.playlists_dropdown)

        # Buttons for playlist management
        buttons_layout = QHBoxLayout()
        
        self.new_playlist_btn = QPushButton("New Playlist")
        self.new_playlist_btn.clicked.connect(self.create_new_playlist)
        
        self.delete_playlist_btn = QPushButton("Delete Playlist")
        self.delete_playlist_btn.clicked.connect(self.delete_current_playlist)
        
        self.load_playlist_btn = QPushButton("Load Playlist")
        self.load_playlist_btn.clicked.connect(self.load_playlist_to_player)
        
        for btn in [self.new_playlist_btn, self.delete_playlist_btn, self.load_playlist_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E63946;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #F56476;
                }
            """)
            buttons_layout.addWidget(btn)
            
        layout.addLayout(buttons_layout)

        # Playlist content list
        self.playlist_content_list = QListWidget()
        self.playlist_content_list.setStyleSheet("""
            QListWidget {
                background-color: #121212;
                color: #b3b3b3;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item:selected {
                background-color: #E63946;
                color: white;
            }
        """)
        layout.addWidget(self.playlist_content_list)

        # Button to remove songs from playlist
        self.remove_from_playlist_btn = QPushButton("Remove Selected")
        self.remove_from_playlist_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.remove_from_playlist_btn.clicked.connect(self.remove_from_current_playlist)
        layout.addWidget(self.remove_from_playlist_btn)

        # Update playlists dropdown
        self.update_playlists_dropdown()

        return view

    def create_album_section(self):
        album_widget = QFrame()
        album_widget.setStyleSheet("background-color: #181818; border-radius: 8px;")
        album_widget.setMaximumHeight(240)
        album_layout = QHBoxLayout(album_widget)
        
        # Album art display
        self.album_art = QLabel()
        self.album_art.setFixedSize(200, 200)
        self.album_art.setAlignment(Qt.AlignCenter)
        # Set default album art
        default_pixmap = QPixmap()
        default_pixmap.loadFromData(QByteArray(SVG_DEFAULT_ALBUM.encode('utf-8')), "SVG")
        self.album_art.setPixmap(default_pixmap)
        self.album_art.setScaledContents(True)
        album_layout.addWidget(self.album_art)
        
        # Song info section
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        self.now_playing_label = QLabel("NOW PLAYING")
        self.now_playing_label.setStyleSheet("color: #E63946; font-size: 12px; font-weight: bold;")
        
        self.song_title_label = QLabel("No song selected")
        self.song_title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        self.song_title_label.setWordWrap(True)
        
        self.artist_label = QLabel("")
        self.artist_label.setStyleSheet("color: #b3b3b3; font-size: 16px;")
        
        # Add to playlist button
        self.add_to_playlist_btn = QPushButton("Add to Playlist")
        self.add_to_playlist_btn.setStyleSheet("""
            QPushButton {
                background-color: #E63946;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #F56476;
            }
        """)
        self.add_to_playlist_btn.clicked.connect(self.add_current_to_playlist)
        
        info_layout.addWidget(self.now_playing_label)
        info_layout.addWidget(self.song_title_label)
        info_layout.addWidget(self.artist_label)
        info_layout.addWidget(self.add_to_playlist_btn)
        info_layout.addStretch()
        
        album_layout.addWidget(info_widget)
        
        return album_widget

    def create_sidebar(self):
        sidebar_widget = QFrame()
        sidebar_widget.setMaximumWidth(200)
        sidebar_widget.setStyleSheet("background-color: #040404;")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)

        # Spotify text logo at top
        logo_label = QLabel("Muse")
        logo_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
        logo_label.setStyleSheet("color: #E63946;")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # Buttons
        self.btn_home = QPushButton(" Home")
        self.btn_home.setIcon(icon_from_svg(SVG_HOME))
        
        self.btn_search = QPushButton(" Search")
        self.btn_search.setIcon(icon_from_svg(SVG_SEARCH))
        
        self.btn_playlists = QPushButton(" Your Playlists")
        self.btn_playlists.setIcon(icon_from_svg(SVG_PLAYLIST))
        
        self.btn_add = QPushButton(" Add Folder")

        for btn in [self.btn_home, self.btn_search, self.btn_playlists, self.btn_add]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: transparent;
                    color: #b3b3b3;
                    font-size: 14px;
                    border: none;
                    text-align: left;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    color: white;
                }
                """
            )
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            sidebar_layout.addWidget(btn)

        # Connect buttons to their functions
        self.btn_home.clicked.connect(lambda: self.content_area.setCurrentIndex(0))
        self.btn_search.clicked.connect(self.open_search)
        self.btn_playlists.clicked.connect(lambda: self.content_area.setCurrentIndex(1))
        self.btn_add.clicked.connect(self.add_songs)

        # Add stretch to push buttons up
        sidebar_layout.addStretch()

        return sidebar_widget

    def create_controls(self):
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Slider for position
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: #3e3e3e;
                margin: 0px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #E63946;
                border-radius: 10px;
                width: 16px;
                margin: -5px 0;
            }
            """
        )
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)

        # Labels for current time and duration
        time_layout = QHBoxLayout()
        self.label_current_time = QLabel("00:00")
        self.label_duration = QLabel("00:00")
        for lbl in [self.label_current_time, self.label_duration]:
            lbl.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        time_layout.addWidget(self.label_current_time)
        time_layout.addStretch()
        time_layout.addWidget(self.label_duration)
        controls_layout.addLayout(time_layout)

        # Playback buttons layout
        btn_layout = QHBoxLayout()

        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(icon_from_svg(SVG_PREV))
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setToolTip("Previous")
        btn_layout.addWidget(self.btn_prev)

        self.btn_play = QPushButton()
        self.btn_play.setIcon(icon_from_svg(SVG_PLAY))
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.setToolTip("Play/Pause")
        btn_layout.addWidget(self.btn_play)

        self.btn_next = QPushButton()
        self.btn_next.setIcon(icon_from_svg(SVG_NEXT))
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setToolTip("Next")
        btn_layout.addWidget(self.btn_next)

        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: #3e3e3e;
                margin: 0px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #E63946;
                border-radius: 10px;
                width: 16px;
                margin: -5px 0;
            }
            """
        )
        btn_layout.addStretch()
        btn_layout.addWidget(self.volume_slider)

        controls_layout.addLayout(btn_layout)

        # Connect buttons
        self.btn_play.clicked.connect(self.play_pause)
        self.btn_next.clicked.connect(self.next_song)
        self.btn_prev.clicked.connect(self.prev_song)
        self.volume_slider.valueChanged.connect(self.change_volume)

        return controls_widget

    def dark_theme_stylesheet(self):
        return """
        QWidget {
            background-color: #121212;
            color: #b3b3b3;
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        }
        QScrollBar:vertical {
            background: #222222;
            width: 10px;
            margin: 15px 0 15px 0;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #E63946;
            min-height: 30px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """

    def extract_metadata(self, filepath):
        """Extract metadata from audio files including album art"""
        filename = os.path.basename(filepath)
        title = os.path.splitext(filename)[0]
        artist = ""
        album_art = None
        
        try:
            if filepath.lower().endswith('.mp3'):
                audio = MP3(filepath, ID3=ID3)
                
                # Extract title and artist from ID3 tags
                if audio.tags:
                    if 'TIT2' in audio.tags:
                        title = str(audio.tags['TIT2'])
                    if 'TPE1' in audio.tags:
                        artist = str(audio.tags['TPE1'])
                        
                    # Extract album art
                    for tag in ['APIC:0', 'APIC:1', 'APIC:3', 'APIC:']:
                        if tag in audio.tags:
                            album_art = audio.tags[tag].data
                            break
                            
            elif filepath.lower().endswith('.flac'):
                audio = FLAC(filepath)
                
                # Extract title and artist
                if 'title' in audio:
                    title = audio['title'][0]
                if 'artist' in audio:
                    artist = audio['artist'][0]
                
                # Extract album art
                if audio.pictures:
                    album_art = audio.pictures[0].data
                    
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            
        return {
            "title": title,
            "artist": artist,
            "album_art": album_art
        }

    def set_album_art(self, album_art_data=None):
        """Set album art from binary data or use default"""
        if album_art_data:
            pixmap = QPixmap()
            pixmap.loadFromData(album_art_data)
        else:
            # Use default album art
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(SVG_DEFAULT_ALBUM.encode('utf-8')), "SVG")
            
        self.album_art.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def song_changed(self, index):
        """Handle when a song changes in the playlist"""
        if index >= 0 and index < len(self.track_paths):
            filepath = self.track_paths[index]
            metadata = self.extract_metadata(filepath)
            
            # Update song info display
            self.song_title_label.setText(metadata["title"])
            self.artist_label.setText(metadata["artist"])
            
            # Update album art
            self.set_album_art(metadata["album_art"])
            
            # Update playlist selection
            self.playlist_widget.setCurrentRow(index)
            
            # Store current track info
            self.current_track_info = {
                "title": metadata["title"],
                "artist": metadata["artist"]
            }

    def add_songs(self):
        """Add all songs from a selected folder"""
        # Use last folder as starting directory if available
        start_dir = self.last_folder_path if self.last_folder_path and os.path.exists(self.last_folder_path) else ""
        
        folder = QFileDialog.getExistingDirectory(
            self, "Select Music Folder", start_dir, QFileDialog.ShowDirsOnly
        )
        
        if folder:
            # Save the selected folder as the last folder
            self.last_folder_path = folder
            
            # Scan the folder for audio files
            audio_files = self.scan_folder_for_audio(folder)
            
            if audio_files:
                # Clear existing library
                self.track_paths = []
                self.track_metadatas = []
                self.playlist_widget.clear()
                self.media_playlist.clear()
                
                for f in audio_files:
                    url = QUrl.fromLocalFile(f)
                    self.media_playlist.addMedia(QMediaContent(url))
                    
                    # Extract metadata
                    metadata = self.extract_metadata(f)
                    self.track_paths.append(f)
                    self.track_metadatas.append(metadata)
                    
                    # Display in playlist
                    display_name = metadata["title"]
                    if metadata["artist"]:
                        display_name += f" - {metadata['artist']}"
                        
                    self.playlist_widget.addItem(display_name)
                
                # Save the library
                self.save_library()
                
                if self.player.state() != QMediaPlayer.PlayingState:
                    self.media_playlist.setCurrentIndex(0)
                    self.player.play()
                    self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))
                    self.timer.start()
                
                # Always change view back to main view (home)
                self.content_area.setCurrentIndex(0)
                
                QMessageBox.information(
                    self, "Success", 
                    f"Added {len(audio_files)} songs from folder"
                )
            else:
                QMessageBox.warning(
                    self, "No Audio Files", 
                    "No audio files were found in the selected folder"
                )
    
    def scan_folder_for_audio(self, folder_path):
        """Scan a folder recursively for audio files"""
        audio_extensions = ['.mp3', '.wav', '.flac', '.ogg']
        audio_files = []
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    audio_files.append(os.path.join(root, file))
                    
        return audio_files

    def play_selected_song(self):
        index = self.playlist_widget.currentRow()
        if index >= 0:
            self.media_playlist.setCurrentIndex(index)
            self.player.play()
            self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))
            self.timer.start()

    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play.setIcon(icon_from_svg(SVG_PLAY))
            self.timer.stop()
        else:
            self.player.play()
            self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))
            self.timer.start()

    def next_song(self):
        self.media_playlist.next()
        self.player.play()
        self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))

    def prev_song(self):
        self.media_playlist.previous()
        self.player.play()
        self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))

    def update_position(self, position):
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
        self.label_current_time.setText(self.ms_to_time(position))

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)
        self.label_duration.setText(self.ms_to_time(duration))

    def set_position(self, position):
        self.player.setPosition(position)

    def refresh_position(self):
        pos = self.player.position()
        self.update_position(pos)

    def change_volume(self, value):
        self.player.setVolume(value)

    def ms_to_time(self, ms):
        seconds = (ms // 1000) % 60
        minutes = (ms // 60000)
        return f"{minutes:02}:{seconds:02}"

    # Playlist management functions
    def update_playlists_dropdown(self):
        """Update the playlists dropdown with all available playlists"""
        self.playlists_dropdown.clear()
        playlist_names = self.playlist_manager.get_playlist_names()
        self.playlists_dropdown.addItems(playlist_names)

    def create_new_playlist(self):
        """Create a new playlist"""
        name, ok = QInputDialog.getText(
            self, "New Playlist", "Enter playlist name:", 
            QLineEdit.Normal, ""
        )
        
        if ok and name:
            if self.playlist_manager.create_playlist(name):
                self.update_playlists_dropdown()
                # Select the newly created playlist
                self.playlists_dropdown.setCurrentText(name)
                QMessageBox.information(self, "Success", f"Playlist '{name}' created!")
            else:
                QMessageBox.warning(self, "Error", f"Playlist '{name}' already exists!")

    def delete_current_playlist(self):
        """Delete the currently selected playlist"""
        current_playlist = self.playlists_dropdown.currentText()
        
        if current_playlist == "Default":
            QMessageBox.warning(self, "Error", "Cannot delete the Default playlist!")
            return
            
        result = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete the playlist '{current_playlist}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            if self.playlist_manager.delete_playlist(current_playlist):
                self.update_playlists_dropdown()
                QMessageBox.information(self, "Success", f"Playlist '{current_playlist}' deleted!")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete playlist!")

    def load_selected_playlist(self):
        """Load the selected playlist content into the view"""
        current_playlist = self.playlists_dropdown.currentText()
        playlist_content = self.playlist_manager.get_playlist(current_playlist)
        
        self.playlist_content_list.clear()
        for track in playlist_content:
            display_name = track["title"]
            if track["artist"]:
                display_name += f" - {track['artist']}"
            self.playlist_content_list.addItem(display_name)

    def load_playlist_to_player(self):
        """Load the selected playlist into the media player"""
        current_playlist = self.playlists_dropdown.currentText()
        playlist_content = self.playlist_manager.get_playlist(current_playlist)
        
        if not playlist_content:
            QMessageBox.information(self, "Empty Playlist", "This playlist is empty!")
            return
            
        # Clear current playlist
        self.media_playlist.clear()
        self.playlist_widget.clear()
        self.track_paths = []
        self.track_metadatas = []
        
        # Add tracks from playlist
        for track in playlist_content:
            path = track["path"]
            if os.path.exists(path):
                url = QUrl.fromLocalFile(path)
                self.media_playlist.addMedia(QMediaContent(url))
                
                metadata = self.extract_metadata(path)
                self.track_paths.append(path)
                self.track_metadatas.append(metadata)
                
                display_name = track["title"]
                if track["artist"]:
                    display_name += f" - {track['artist']}"
                self.playlist_widget.addItem(display_name)
        
        # Update title
        self.title_label.setText(f"Playlist: {current_playlist}")
        
        # Start playing if tracks were added
        if self.media_playlist.mediaCount() > 0:
            self.media_playlist.setCurrentIndex(0)
            self.player.play()
            self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))
            self.timer.start()
            
            # Switch to main view
            self.content_area.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "Warning", "No valid tracks found in playlist!")

    def add_current_to_playlist(self):
        """Add currently playing song to a playlist"""
        current_index = self.media_playlist.currentIndex()
        if current_index < 0 or current_index >= len(self.track_paths):
            QMessageBox.information(self, "No Song Playing", "No song is currently playing!")
            return
            
        # Get playlist names
        playlist_names = self.playlist_manager.get_playlist_names()
        
        # Show dialog to select playlist
        playlist_name, ok = QInputDialog.getItem(
            self, "Add to Playlist", 
            "Select playlist:", playlist_names, 0, False
        )
        
        if ok and playlist_name:
            track_path = self.track_paths[current_index]
            metadata = self.track_metadatas[current_index]
            
            if self.playlist_manager.add_to_playlist(playlist_name, track_path, metadata):
                QMessageBox.information(
                    self, "Success", 
                    f"'{metadata['title']}' added to playlist '{playlist_name}'!"
                )
                
                # If currently viewing the playlist that was modified, refresh the view
                if self.playlists_dropdown.currentText() == playlist_name:
                    self.load_selected_playlist()
            else:
                QMessageBox.warning(self, "Error", "Failed to add to playlist!")

    def remove_from_current_playlist(self):
        """Remove selected song from current playlist"""
        current_playlist = self.playlists_dropdown.currentText()
        selected_row = self.playlist_content_list.currentRow()
        
        if selected_row >= 0:
            if self.playlist_manager.remove_from_playlist(current_playlist, selected_row):
                self.playlist_content_list.takeItem(selected_row)
                QMessageBox.information(self, "Success", "Track removed from playlist!")
            else:
                QMessageBox.warning(self, "Error", "Failed to remove track!")
        else:
            QMessageBox.information(self, "No Selection", "Please select a track to remove.")

    def open_search(self):
        """Open search dialog"""
        if not self.track_paths:
            QMessageBox.information(self, "No Music", "Add some music first!")
            return
            
        search_dialog = SearchDialog(self, self.track_paths, self.track_metadatas)
        result = search_dialog.exec_()
        
        if result == QDialog.Accepted:
            index = search_dialog.get_selected_index()
            if index >= 0:
                self.media_playlist.setCurrentIndex(index)
                self.player.play()
                self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))
                self.timer.start()
                # Go to main view
                self.content_area.setCurrentIndex(0)

    def save_library(self):
        """Save the current library to a file"""
        library_data = {
            "track_paths": self.track_paths,
            "track_metadatas": self.track_metadatas,
            "last_folder": self.last_folder_path
        }
        
        try:
            with open(self.library_file, 'wb') as f:
                pickle.dump(library_data, f)
                print(f"Library saved: {len(self.track_paths)} tracks")
        except Exception as e:
            print(f"Error saving library: {e}")
            
    def load_library(self):
        """Load the library from the saved file"""
        if not os.path.exists(self.library_file):
            print("No saved library found.")
            return
            
        try:
            with open(self.library_file, 'rb') as f:
                library_data = pickle.load(f)
                
                self.track_paths = library_data.get("track_paths", [])
                self.track_metadatas = library_data.get("track_metadatas", [])
                self.last_folder_path = library_data.get("last_folder", "")
                
                # Populate the playlist widget and media playlist
                self.playlist_widget.clear()
                self.media_playlist.clear()
                
                for i, (path, metadata) in enumerate(zip(self.track_paths, self.track_metadatas)):
                    if os.path.exists(path):
                        url = QUrl.fromLocalFile(path)
                        self.media_playlist.addMedia(QMediaContent(url))
                        
                        display_name = metadata["title"]
                        if metadata["artist"]:
                            display_name += f" - {metadata['artist']}"
                            
                        self.playlist_widget.addItem(display_name)
                
                print(f"Library loaded: {len(self.track_paths)} tracks")
        except Exception as e:
            print(f"Error loading library: {e}")
            
    def closeEvent(self, event):
        """Save library when closing the application"""
        self.save_library()
        event.accept()


def main():
    app = QApplication(sys.argv)
    player = SpotifyLikePlayer()
    player.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()