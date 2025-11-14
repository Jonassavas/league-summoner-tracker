# ui/main_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPixmap, QFont
from api.riot_api import RiotAPI
from utils.assets import get_emblem_path


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # API
        self.api = RiotAPI()
        self.rank_data = None
        self.flex_visible = False

        # Window settings
        self.setWindowTitle("League Summoner Tracker")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Save initial geometry for restore
        self.normal_geometry_data = self.saveGeometry()
        self.is_fullscreen = False

        main_layout = QVBoxLayout()

        # -------------------------
        # Form layout for Name/Tag input
        # -------------------------
        self.name_input = QLineEdit()
        self.tag_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Jone")
        self.tag_input.setPlaceholderText("e.g. SWE")

        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Tag Line #:", self.tag_input)
        main_layout.addLayout(form_layout)

        # -------------------------
        # Horizontal content layout
        # -------------------------
        content_layout = QHBoxLayout()

        # Left column: Buttons + Name/Tag
        self.left_column = QVBoxLayout()
        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedHeight(40)
        self.search_btn.clicked.connect(self.on_search)

        self.toggle_btn = QPushButton("Show Flex Ranking")
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.clicked.connect(self.toggle_flex)
        self.toggle_btn.hide()

        # Summoner label below buttons
        self.summoner_label = QLabel("")
        self.summoner_label.setAlignment(Qt.AlignCenter)
        self.summoner_label.setWordWrap(True)

        self.left_column.addWidget(self.search_btn)
        self.left_column.addWidget(self.toggle_btn)
        self.left_column.addStretch()
        self.left_column.addWidget(self.summoner_label)
        content_layout.addLayout(self.left_column, 1)  # ~20% width

        # Right column: Ranked info
        self.rank_layout = QHBoxLayout()

        # SOLO container
        self.solo_container = QWidget()
        self.solo_vbox = QVBoxLayout(self.solo_container)
        self.solo_label_title = QLabel("Solo/Duo")
        self.solo_label_title.setAlignment(Qt.AlignCenter)
        self.solo_emblem = QLabel()
        self.solo_emblem.setAlignment(Qt.AlignCenter)
        self.solo_emblem.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.solo_emblem.setMinimumSize(1, 1)
        self.solo_emblem.installEventFilter(self)  # <- event filter for resizing
        self.solo_text = QLabel("")
        self.solo_text.setAlignment(Qt.AlignCenter)
        self.solo_text.setWordWrap(True)
        self.solo_vbox.addWidget(self.solo_label_title)
        self.solo_vbox.addWidget(self.solo_emblem, 1)
        self.solo_vbox.addWidget(self.solo_text)
        self.solo_container.hide()

        # FLEX container
        self.flex_container = QWidget()
        self.flex_vbox = QVBoxLayout(self.flex_container)
        self.flex_label_title = QLabel("Flex")
        self.flex_label_title.setAlignment(Qt.AlignCenter)
        self.flex_emblem = QLabel()
        self.flex_emblem.setAlignment(Qt.AlignCenter)
        self.flex_emblem.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.flex_emblem.setMinimumSize(1, 1)
        self.flex_emblem.installEventFilter(self)
        self.flex_text = QLabel("")
        self.flex_text.setAlignment(Qt.AlignCenter)
        self.flex_text.setWordWrap(True)
        self.flex_vbox.addWidget(self.flex_label_title)
        self.flex_vbox.addWidget(self.flex_emblem, 1)
        self.flex_vbox.addWidget(self.flex_text)
        self.flex_container.hide()

        # Add SOLO/FLEX to rank layout
        self.rank_layout.addWidget(self.solo_container, 1)
        self.rank_layout.addWidget(self.flex_container, 1)
        content_layout.addLayout(self.rank_layout, 4)  # ~80% width

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # Base font for scaling
        self.base_font = QFont()
        self.base_font.setPointSize(12)
        self.solo_text.setFont(self.base_font)
        self.flex_text.setFont(self.base_font)
        self.solo_label_title.setFont(self.base_font)
        self.flex_label_title.setFont(self.base_font)
        self.summoner_label.setFont(self.base_font)

        # Original pixmaps for scaling
        self.solo_original_pixmap = None
        self.flex_original_pixmap = None

    # -------------------------
    # Search button logic
    # -------------------------
    def on_search(self):
        name = self.name_input.text().strip()
        tag = self.tag_input.text().strip()
        self.flex_visible = False
        self.solo_container.hide()
        self.flex_container.hide()
        self.toggle_btn.hide()

        if not name or not tag:
            self.solo_container.show()
            self.solo_text.setText("Please enter both Name and Tag line")
            self.summoner_label.setText("")
            self.solo_emblem.clear()
            self.flex_emblem.clear()
            self.solo_original_pixmap = None
            self.flex_original_pixmap = None
            return

        self.summoner_label.setText(f"{name}\n#{tag}")

        # Step 1: PUUID
        status, puuid_or_error = self.api.get_puuid(name, tag)
        if status != 200:
            self.solo_container.show()
            self.solo_text.setText(f"Error getting PUUID:\n{puuid_or_error}")
            return
        puuid = puuid_or_error

        # Step 2: Ranked data
        status, ranked = self.api.get_ranked_data(puuid)
        if status != 200:
            self.solo_container.show()
            self.solo_text.setText(f"Error getting ranked data:\n{ranked}")
            return
        self.rank_data = ranked

        # SOLO rank
        solo = ranked.get("solo")
        if solo:
            self.solo_container.show()
            tier = solo["tier"]
            emblem_path = get_emblem_path(tier)
            self.solo_original_pixmap = QPixmap(emblem_path)
            self.solo_emblem.setPixmap(self.solo_original_pixmap)

            self.solo_text.setText(
                f"{tier.title()} {solo['rank']} - {solo['leaguePoints']} LP\n"
                f"Wins: {solo['wins']}  Losses: {solo['losses']}"
            )
        else:
            self.solo_container.show()
            self.solo_emblem.clear()
            self.solo_original_pixmap = None
            self.solo_text.setText("Solo/Duo\nUnranked")

        # FLEX rank
        flex = ranked.get("flex")
        if flex:
            self.flex_container.show()
            tier = flex["tier"]
            emblem_path = get_emblem_path(tier)
            self.flex_original_pixmap = QPixmap(emblem_path)
            self.flex_emblem.setPixmap(self.flex_original_pixmap)

            self.flex_text.setText(
                f"{tier.title()} {flex['rank']} - {flex['leaguePoints']} LP\n"
                f"Wins: {flex['wins']}  Losses: {flex['losses']}"
            )
            self.flex_container.hide()
            self.toggle_btn.show()
        else:
            self.flex_container.hide()
            self.flex_emblem.clear()
            self.flex_original_pixmap = None
            self.flex_text.setText("Flex\nUnranked")
            self.toggle_btn.hide()

    # -------------------------
    # Toggle flex visibility
    # -------------------------
    def toggle_flex(self):
        if self.flex_visible:
            self.flex_container.hide()
            self.toggle_btn.setText("Show Flex Ranking")
            self.flex_visible = False
        else:
            self.flex_container.show()
            self.toggle_btn.setText("Hide Flex Ranking")
            self.flex_visible = True

    # -------------------------
    # Fullscreen / restore
    # -------------------------
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowFullScreen:
                self.is_fullscreen = True
            else:
                if self.is_fullscreen:
                    self.restoreGeometry(self.normal_geometry_data)
                    self.is_fullscreen = False
        super().changeEvent(event)

    # -------------------------
    # Resize event (for fonts)
    # -------------------------
    def resizeEvent(self, event):
        if not self.isFullScreen() and isinstance(event, QEvent):
            self.normal_geometry_data = self.saveGeometry()
        self.scale_fonts()
        super().resizeEvent(event)

    # -------------------------
    # Event filter for QLabel resizing
    # -------------------------
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            if obj == self.solo_emblem or obj == self.flex_emblem:
                self.scale_emblems()
        return super().eventFilter(obj, event)

    # -------------------------
    # Scale fonts dynamically
    # -------------------------
    def scale_fonts(self):
        font_size = max(12, self.width() // 35)
        font = QFont(self.base_font)
        font.setPointSize(font_size)
        self.solo_text.setFont(font)
        self.flex_text.setFont(font)
        self.solo_label_title.setFont(font)
        self.flex_label_title.setFont(font)
        self.summoner_label.setFont(font)

    # -------------------------
    # Scale emblems based on QLabel size
    # -------------------------
    def scale_emblems(self):
        if self.solo_original_pixmap:
            scaled = self.solo_original_pixmap.scaled(
                self.solo_emblem.width(),
                self.solo_emblem.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.solo_emblem.setPixmap(scaled)

        if self.flex_original_pixmap:
            scaled = self.flex_original_pixmap.scaled(
                self.flex_emblem.width(),
                self.flex_emblem.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.flex_emblem.setPixmap(scaled)
