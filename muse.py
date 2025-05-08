import sys
from PyQt5.QtCore import Qt, QUrl, QTimer, QByteArray
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
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent


# Embedded SVG icons as QIcon for consistent cross-platform look
def icon_from_svg(svg_content):
    pixmap = QPixmap()
    pixmap.loadFromData(QByteArray(svg_content.encode("utf-8")), "SVG")
    return QIcon(pixmap)


SVG_PLAY = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#1DB954" xmlns="http://www.w3.org/2000/svg">
<path d="M8 5v14l11-7z"/>
</svg>
"""

SVG_PAUSE = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#1DB954" xmlns="http://www.w3.org/2000/svg">
<path d="M6 19h4V5H6v14zM14 5v14h4V5h-4z"/>
</svg>
"""

SVG_NEXT = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#1DB954" xmlns="http://www.w3.org/2000/svg">
<path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
</svg>
"""

SVG_PREV = """
<svg height="24px" viewBox="0 0 24 24" width="24px" fill="#1DB954" xmlns="http://www.w3.org/2000/svg">
<path d="M18 6l-8.5 6L18 18V6zM8 6v12H6V6h2z"/>
</svg>
"""


class SpotifyLikePlayer(QWidget):
    def __init__(self):  # Fixed constructor name
        super().__init__()  # Fixed call to parent constructor
        self.setWindowTitle("Spotify-Like Music Player")
        self.setGeometry(200, 100, 900, 600)
        self.setMinimumSize(700, 400)
        self.setStyleSheet(self.dark_theme_stylesheet())

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Content area
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(10)

        # Title of currently playing / playlist name
        self.title_label = QLabel("Your Playlist")
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.content_layout.addWidget(self.title_label)

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
                background-color: #1db954;
                color: white;
            }
            """
        )
        self.content_layout.addWidget(self.playlist_widget)

        # Playback controls area
        self.controls_area = self.create_controls()
        self.content_layout.addWidget(self.controls_area)

        main_layout.addWidget(self.content_area)

        # Media player
        self.player = QMediaPlayer()
        self.media_playlist = QMediaPlaylist()
        self.player.setPlaylist(self.media_playlist)

        # Connect playlists and controls signals
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected_song)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)

        # Timer to update slider while playing
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_position)

        # Start with volume 50
        self.player.setVolume(50)

    def create_sidebar(self):
        sidebar_widget = QFrame()
        sidebar_widget.setMaximumWidth(200)
        sidebar_widget.setStyleSheet("background-color: #040404;")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)

        # Spotify text logo at top
        logo_label = QLabel("Spotify")
        logo_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
        logo_label.setStyleSheet("color: #1db954;")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # Buttons
        btn_home = QPushButton("Home")
        btn_search = QPushButton("Search")
        btn_library = QPushButton("Your Library")
        btn_add = QPushButton("Add Songs")

        for btn in [btn_home, btn_search, btn_library, btn_add]:
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

        # Add Songs button functionality
        btn_add.clicked.connect(self.add_songs)

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
                background: #1db954;
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
                background: #1db954;
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
            background: #1db954;
            min-height: 30px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """

    def add_songs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add Music Files", "", "Audio Files (*.mp3 *.wav *.flac *.ogg)"
        )
        if files:
            for f in files:
                url = QUrl.fromLocalFile(f)
                self.media_playlist.addMedia(QMediaContent(url))
                filename = f.split("/")[-1]
                self.playlist_widget.addItem(filename)
            if self.player.state() != QMediaPlayer.PlayingState:
                self.media_playlist.setCurrentIndex(0)
                self.player.play()
                self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))
                self.timer.start()

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
        self.playlist_widget.setCurrentRow(self.media_playlist.currentIndex())

    def prev_song(self):
        self.media_playlist.previous()
        self.player.play()
        self.btn_play.setIcon(icon_from_svg(SVG_PAUSE))
        self.playlist_widget.setCurrentRow(self.media_playlist.currentIndex())

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


def main():
    app = QApplication(sys.argv)
    player = SpotifyLikePlayer()
    player.show()
    sys.exit(app.exec_())


if __name__ == "__main__":  # Fixed typo in the condition
    main()