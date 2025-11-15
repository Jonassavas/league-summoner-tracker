# ui/main_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QFormLayout, QSizePolicy,
    QStackedLayout
)
from PySide6.QtCore import Qt, QEvent, QTimer, QRect, QSize
from PySide6.QtGui import QPixmap, QFont
from api.riot_api import RiotAPI
from utils.assets import get_emblem_path
from api.league_client import LeagueClient
from api.champion_data import ChampionData
from PySide6.QtWidgets import QHBoxLayout, QLabel



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # API
        self.api = RiotAPI()
        self.rank_data = None
        self.flex_visible = False
        self.champ_data = ChampionData()  # builds id->name mapping, caches patch


        # Window settings
        self.setWindowTitle("League Summoner Tracker")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Save initial geometry for restore
        self.normal_geometry_data = self.saveGeometry()
        self.normal_geometry_rect = self.geometry()
        self.was_maximized = False
        self.is_fullscreen = False

        # --------------------------------------------------
        # STACKED LAYOUT FOR MULTIPLE SCREENS
        # --------------------------------------------------
        self.stack = QStackedLayout()
        self.setLayout(self.stack)

        # --------------------------------------------------
        # MAIN SCREEN
        # --------------------------------------------------
        self.main_screen = QWidget()
        main_layout = QVBoxLayout(self.main_screen)

        # Form layout Name/Tag
        self.name_input = QLineEdit()
        self.tag_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Jone")
        self.tag_input.setPlaceholderText("e.g. SWE")

        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Tag Line #:", self.tag_input)
        main_layout.addLayout(form_layout)

        # Horizontal content
        content_layout = QHBoxLayout()
        self.left_column = QVBoxLayout()

        # Buttons
        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedHeight(40)
        self.search_btn.clicked.connect(self.on_search)

        self.toggle_btn = QPushButton("Show Flex Ranking")
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.clicked.connect(self.toggle_flex)
        self.toggle_btn.hide()

        # Champ select button
        self.champ_btn = QPushButton("Show Champ-Select")
        self.champ_btn.setFixedHeight(40)
        self.champ_btn.clicked.connect(self.on_show_champ)

        # Summoner label
        self.summoner_label = QLabel("")
        self.summoner_label.setAlignment(Qt.AlignCenter)
        self.summoner_label.setWordWrap(True)

        # Add to left column
        self.left_column.addWidget(self.search_btn)
        self.left_column.addWidget(self.toggle_btn)
        self.left_column.addWidget(self.champ_btn)
        self.left_column.addStretch()
        self.left_column.addWidget(self.summoner_label)
        content_layout.addLayout(self.left_column, 1)

        # Right column (rank info)
        self.rank_layout = QHBoxLayout()

        # SOLO container
        self.solo_container = QWidget()
        self.solo_vbox = QVBoxLayout(self.solo_container)
        self.solo_label_title = QLabel("Solo/Duo")
        self.solo_label_title.setAlignment(Qt.AlignCenter)
        self.solo_emblem = QLabel()
        self.solo_emblem.setAlignment(Qt.AlignCenter)
        self.solo_emblem.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.solo_emblem.setMinimumSize(1, 1)
        self.solo_emblem.installEventFilter(self)
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
        self.flex_emblem.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.flex_emblem.setMinimumSize(1, 1)
        self.flex_emblem.installEventFilter(self)
        self.flex_text = QLabel("")
        self.flex_text.setAlignment(Qt.AlignCenter)
        self.flex_text.setWordWrap(True)
        self.flex_vbox.addWidget(self.flex_label_title)
        self.flex_vbox.addWidget(self.flex_emblem, 1)
        self.flex_vbox.addWidget(self.flex_text)
        self.flex_container.hide()

        # Add rank widgets
        self.rank_layout.addWidget(self.solo_container, 1)
        self.rank_layout.addWidget(self.flex_container, 1)
        content_layout.addLayout(self.rank_layout, 4)

        main_layout.addLayout(content_layout)

        # Scaling
        self.base_font = QFont()
        self.base_font.setPointSize(12)
        self.solo_text.setFont(self.base_font)
        self.flex_text.setFont(self.base_font)
        self.solo_label_title.setFont(self.base_font)
        self.flex_label_title.setFont(self.base_font)
        self.summoner_label.setFont(self.base_font)

        # Pixmaps
        self.solo_original_pixmap = None
        self.flex_original_pixmap = None

        # Register main screen in stack
        self.stack.addWidget(self.main_screen)

        # -------------------
        # CHAMP SELECT SCREEN
        # -------------------
        self.champ_screen = QWidget()
        self.champ_layout = QVBoxLayout(self.champ_screen)  # store as self

        # Back button (always stays)
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.go_back)
        self.champ_layout.addWidget(self.back_btn)

        # Timer for live champ-select updates
        self.champ_timer = QTimer(self)
        self.champ_timer.setInterval(1000)  # 1 second
        self.champ_timer.timeout.connect(self.update_champ_select)


        # Label for messages
        self.champ_select_label = QLabel("Champion select will appear here.")
        self.champ_select_label.setAlignment(Qt.AlignCenter)
        self.champ_select_label.setWordWrap(True)
        self.champ_layout.addWidget(self.champ_select_label)

        # Add champ screen to stacked layout
        self.stack.addWidget(self.champ_screen)


    # --------------------------------------------------
    # Search button logic
    # --------------------------------------------------
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

        status, puuid_or_error = self.api.get_puuid(name, tag)
        if status != 200:
            self.solo_container.show()
            self.solo_text.setText(f"Error getting PUUID:\n{puuid_or_error}")
            return
        puuid = puuid_or_error

        status, ranked = self.api.get_ranked_data(puuid)
        if status != 200:
            self.solo_container.show()
            self.solo_text.setText(f"Error getting ranked data:\n{ranked}")
            return
        self.rank_data = ranked

        # Solo rank
        solo = ranked.get("solo")
        if solo:
            self.solo_container.show()
            tier = solo["tier"]
            emblem_path = get_emblem_path(tier)
            self.solo_original_pixmap = QPixmap(emblem_path)
            self.solo_emblem.clear()
            QTimer.singleShot(0, self.scale_emblems)
            self.solo_text.setText(
                f"{tier.title()} {solo['rank']} - {solo['leaguePoints']} LP\n"
                f"Wins: {solo['wins']}  Losses: {solo['losses']}"
            )
        else:
            self.solo_container.show()
            self.solo_emblem.clear()
            self.solo_original_pixmap = None
            self.solo_text.setText("Solo/Duo\nUnranked")

        # Flex rank
        flex = ranked.get("flex")
        if flex:
            self.flex_container.show()
            tier = flex["tier"]
            emblem_path = get_emblem_path(tier)
            self.flex_original_pixmap = QPixmap(emblem_path)
            self.flex_emblem.clear()
            QTimer.singleShot(0, self.scale_emblems)
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

    # --------------------------------------------------
    # Toggle flex
    # --------------------------------------------------
    def toggle_flex(self):
        if self.flex_visible:
            self.flex_container.hide()
            self.toggle_btn.setText("Show Flex Ranking")
            self.flex_visible = False
        else:
            self.flex_container.show()
            self.toggle_btn.setText("Hide Flex Ranking")
            self.flex_visible = True
            QTimer.singleShot(0, self.scale_emblems)

    # --------------------------------------------------
    # Champ Select Screen
    # --------------------------------------------------
    def on_show_champ(self):
        # Switch to champ-select screen
        self.stack.setCurrentIndex(1)
        self.champ_timer.start()
        self.update_champ_select()

    def go_back(self):
        self.champ_timer.stop()
        self.stack.setCurrentIndex(0)

    def update_champ_select(self):
        client = LeagueClient()
        status, data = client.get_champ_select()

        if status != 200 or not data:
            self.champ_select_label.setText("Not in champ select.")
            return

        # Clear previous picks/bans layouts but keep first two widgets (back button + label)
        while self.champ_layout.count() > 2:
            item = self.champ_layout.takeAt(2)
            if item.widget():
                item.widget().deleteLater()

        # Layouts for picks, enemy team, bans
        my_team_layout = QHBoxLayout()
        enemy_team_layout = QHBoxLayout()
        bans_layout = QHBoxLayout()

        # Fill my team picks
        for champ in data.get("myTeam", []):
            champ_id = champ.get("championId")
            label = QLabel()
            icon_path = self.champ_data.get_champion_icon(champ_id)
            if icon_path:
                pix = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pix)
            my_team_layout.addWidget(label)

        # Fill enemy team picks
        for champ in data.get("theirTeam", []):
            champ_id = champ.get("championId")
            label = QLabel()
            icon_path = self.champ_data.get_champion_icon(champ_id)
            if icon_path:
                pix = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pix)
            enemy_team_layout.addWidget(label)

        # Fill bans
        for group in data.get("actions", []):
            for action in group:
                if action.get("type") == "ban" and action.get("completed"):
                    champ_id = action.get("championId")
                    label = QLabel()
                    icon_path = self.champ_data.get_champion_icon(champ_id)
                    if icon_path:
                        pix = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        label.setPixmap(pix)
                    bans_layout.addWidget(label)

        # Add layouts to main champ layout
        self.champ_layout.addLayout(my_team_layout)
        self.champ_layout.addLayout(enemy_team_layout)
        self.champ_layout.addLayout(bans_layout)


    # --------------------------------------------------
    # Scaling + Events
    # --------------------------------------------------
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            now_maximized = bool(self.windowState() & Qt.WindowMaximized)
            if now_maximized:
                self.was_maximized = True
            else:
                if self.was_maximized:
                    try:
                        self.showNormal()
                    except Exception:
                        pass
                    QTimer.singleShot(50, self._apply_saved_normal_geometry_and_scale)
                self.was_maximized = False

            if self.windowState() & Qt.WindowFullScreen:
                self.is_fullscreen = True
            else:
                if self.is_fullscreen:
                    try:
                        self.restoreGeometry(self.normal_geometry_data)
                    except Exception:
                        pass
                    self.is_fullscreen = False

        super().changeEvent(event)

    def _apply_saved_normal_geometry_and_scale(self):
        try:
            screen = self.screen()
            scr_geom = screen.availableGeometry() if screen else None
        except Exception:
            scr_geom = None

        use_rect = None
        if isinstance(self.normal_geometry_rect, QRect) and not self.normal_geometry_rect.isNull():
            if scr_geom:
                if (self.normal_geometry_rect.width() >= scr_geom.width() * 0.9 or
                        self.normal_geometry_rect.height() >= scr_geom.height() * 0.9):
                    use_rect = None
                else:
                    use_rect = self.normal_geometry_rect
            else:
                use_rect = self.normal_geometry_rect

        if use_rect is None:
            fallback_w, fallback_h = 800, 600
            if scr_geom:
                cx = scr_geom.x() + (scr_geom.width() - fallback_w) // 2
                cy = scr_geom.y() + (scr_geom.height() - fallback_h) // 2
                use_rect = QRect(cx, cy, fallback_w, fallback_h)
            else:
                use_rect = QRect(100, 100, fallback_w, fallback_h)

        try:
            self.setGeometry(use_rect)
        except Exception:
            try:
                self.restoreGeometry(self.normal_geometry_data)
            except Exception:
                pass

        QTimer.singleShot(0, self.scale_emblems)

    def resizeEvent(self, event):
        if not (self.windowState() & Qt.WindowMaximized) and not (self.windowState() & Qt.WindowFullScreen):
            try:
                self.normal_geometry_rect = self.geometry()
                self.normal_geometry_data = self.saveGeometry()
            except Exception:
                pass

        self.scale_fonts()
        QTimer.singleShot(0, self.scale_emblems)
        super().resizeEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            if obj == self.solo_emblem or obj == self.flex_emblem:
                QTimer.singleShot(0, self.scale_emblems)
        return super().eventFilter(obj, event)

    def scale_fonts(self):
        font_size = max(12, self.width() // 35)
        font = QFont(self.base_font)
        font.setPointSize(font_size)
        self.solo_text.setFont(font)
        self.flex_text.setFont(font)
        self.solo_label_title.setFont(font)
        self.flex_label_title.setFont(font)
        self.summoner_label.setFont(font)

    def scale_emblems(self):
        if self.solo_original_pixmap:
            lw, lh = self.solo_emblem.width(), self.solo_emblem.height()
            if lw > 1 and lh > 1:
                scaled = self.solo_original_pixmap.scaled(
                    QSize(lw, lh), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.solo_emblem.setPixmap(scaled)

        if self.flex_original_pixmap:
            lw, lh = self.flex_emblem.width(), self.flex_emblem
