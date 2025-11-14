# ui/main_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from api.riot_api import RiotAPI
from utils.assets import get_emblem_path


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.api = RiotAPI()
        self.rank_data = None
        self.flex_visible = False

        self.setWindowTitle("League Summoner Tracker")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        main_layout = QVBoxLayout()

        # -------------------------
        # Form layout for Name/Tag
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

        # Left column: Buttons
        buttons_layout = QVBoxLayout()
        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedHeight(40)
        self.search_btn.clicked.connect(self.on_search)

        self.toggle_btn = QPushButton("Show Flex Ranking")
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.clicked.connect(self.toggle_flex)
        self.toggle_btn.hide()  # hide until flex exists

        buttons_layout.addWidget(self.search_btn)
        buttons_layout.addWidget(self.toggle_btn)
        buttons_layout.addStretch()
        content_layout.addLayout(buttons_layout, 1)  # ~20% width

        # Right column: Ranked info
        rank_layout = QVBoxLayout()

        # Emblems horizontal
        self.emblem_row = QHBoxLayout()
        self.solo_emblem = QLabel()
        self.flex_emblem = QLabel()
        self.flex_emblem.hide()
        self.solo_emblem.setScaledContents(True)
        self.flex_emblem.setScaledContents(True)

        self.emblem_row.addStretch()
        self.emblem_row.addWidget(self.solo_emblem, alignment=Qt.AlignCenter)
        self.emblem_row.addSpacing(20)
        self.emblem_row.addWidget(self.flex_emblem, alignment=Qt.AlignCenter)
        self.emblem_row.addStretch()
        rank_layout.addLayout(self.emblem_row)

        # Rank labels
        self.solo_label = QLabel("")
        self.flex_label = QLabel("")
        self.flex_label.hide()
        self.solo_label.setAlignment(Qt.AlignCenter)
        self.flex_label.setAlignment(Qt.AlignCenter)
        self.solo_label.setWordWrap(True)
        self.flex_label.setWordWrap(True)
        rank_layout.addWidget(self.solo_label)
        rank_layout.addWidget(self.flex_label)
        rank_layout.addStretch()
        content_layout.addLayout(rank_layout, 4)  # ~80% width

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # Initial font for labels
        self.base_font = QFont()
        self.base_font.setPointSize(12)
        self.solo_label.setFont(self.base_font)
        self.flex_label.setFont(self.base_font)

    # ----------------------------------------------------
    # Search button logic
    # ----------------------------------------------------
    def on_search(self):
        name = self.name_input.text().strip()
        tag = self.tag_input.text().strip()
        self.flex_visible = False
        self.flex_label.hide()
        self.flex_emblem.hide()
        self.toggle_btn.hide()

        if not name or not tag:
            self.solo_label.setText("Please enter both Name and Tag line")
            return

        # Step 1: PUUID
        status, puuid_or_error = self.api.get_puuid(name, tag)
        if status != 200:
            self.solo_label.setText(f"Error getting PUUID:\n{puuid_or_error}")
            return
        puuid = puuid_or_error

        # Step 2: Ranked data
        status, ranked = self.api.get_ranked_data(puuid)
        if status != 200:
            self.solo_label.setText(f"Error getting ranked data:\n{ranked}")
            return
        self.rank_data = ranked

        # SOLO
        solo = ranked["solo"]
        if solo:
            tier = solo["tier"]
            emblem_path = get_emblem_path(tier)

            pix = QPixmap(emblem_path)
            self.solo_emblem.setPixmap(pix)

            self.solo_label.setText(
                f"{tier.title()} {solo['rank']} - {solo['leaguePoints']} LP\n"
                f"Wins: {solo['wins']}  Losses: {solo['losses']}"
            )
        else:
            self.solo_emblem.clear()
            self.solo_label.setText("Solo Rank: Unranked")

        # FLEX
        flex = ranked["flex"]
        if flex:
            tier = flex["tier"]
            emblem_path = get_emblem_path(tier)

            pix = QPixmap(emblem_path)
            self.flex_emblem.setPixmap(pix)

            self.flex_label.setText(
                f"{tier.title()} {flex['rank']} - {flex['leaguePoints']} LP\n"
                f"Wins: {flex['wins']}  Losses: {flex['losses']}"
            )

            # Show toggle button since flex exists
            self.toggle_btn.show()
            self.flex_emblem.hide()
            self.flex_label.hide()
        else:
            self.flex_emblem.clear()
            self.flex_label.setText("Flex Rank: Unranked")
            self.toggle_btn.hide()

    # ----------------------------------------------------
    # Toggle flex visibility
    # ----------------------------------------------------
    def toggle_flex(self):
        if self.flex_visible:
            self.flex_label.hide()
            self.flex_emblem.hide()
            self.toggle_btn.setText("Show Flex Ranking")
            self.flex_visible = False
        else:
            self.flex_label.show()
            self.flex_emblem.show()
            self.toggle_btn.setText("Hide Flex Ranking")
            self.flex_visible = True

    # ----------------------------------------------------
    # Dynamically resize font with window
    # ----------------------------------------------------
    def resizeEvent(self, event):
        new_size = max(12, self.width() // 35)
        font = self.base_font
        font.setPointSize(new_size)
        self.solo_label.setFont(font)
        self.flex_label.setFont(font)
        super().resizeEvent(event)
