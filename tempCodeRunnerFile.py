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