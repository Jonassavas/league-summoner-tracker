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

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedHeight(40)
        self.search_btn.clicked.connect(self.on_search)
        self.toggle_btn = QPushButton("Show Flex Ranking")
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.clicked.connect(self.toggle_flex)
        self.toggle_btn.hide()
        self.champ_btn = QPushButton("Show Champ-Select")
        self.champ_btn.setFixedHeight(40)
        self.champ_btn.clicked.connect(self.on_show_champ)
        self.summoner_label = QLabel("")
        self.summoner_label.setAlignment(Qt.AlignCenter)
        self.summoner_label.setWordWrap(True)

        self.left_column.addWidget(self.search_btn)
        self.left_column.addWidget(self.toggle_btn)
        self.left_column.addWidget(self.champ_btn)
        self.left_column.addStretch()
        self.left_column.addWidget(self.summoner_label)
        content_layout.addLayout(self.left_column, 1)

        # Right column for rank info
        self.rank_layout = QHBoxLayout()
        # Solo/Duo
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

        # Flex
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

        self.rank_layout.addWidget(self.solo_container, 1)
        self.rank_layout.addWidget(self.flex_container, 1)
        content_layout.addLayout(self.rank_layout, 4)
        main_layout.addLayout(content_layout)

        # Font scaling
        self.base_font = QFont()
        self.base_font.setPointSize(12)
        for widget in [self.solo_text, self.flex_text, self.solo_label_title, self.flex_label_title, self.summoner_label]:
            widget.setFont(self.base_font)

        self.solo_original_pixmap = None
        self.flex_original_pixmap = None

        self.stack.addWidget(self.main_screen)

        # --------------------------------------------------
        # CHAMP SELECT SCREEN
        # --------------------------------------------------
        self.champ_screen = QWidget()
        self.champ_layout = QVBoxLayout(self.champ_screen)

        # Back button
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.go_back)
        self.champ_layout.addWidget(self.back_btn)

        # Info label
        self.champ_select_label = QLabel("Champion select will appear here.")
        self.champ_select_label.setAlignment(Qt.AlignCenter)
        self.champ_select_label.setWordWrap(True)
        self.champ_layout.addWidget(self.champ_select_label)

        # Empty box lists
        self.my_team_labels = [QLabel() for _ in range(5)]
        self.enemy_team_labels = [QLabel() for _ in range(5)]
        self.my_ban_labels = [QLabel() for _ in range(5)]
        self.enemy_ban_labels = [QLabel() for _ in range(5)]

        # Set default empty boxes
        for i, lbl in enumerate(self.my_team_labels):
            lbl.setFixedSize(64, 64)
            lbl.setStyleSheet("border:2px solid gray; background-color: #ddeeff;")  # default blue
        for i, lbl in enumerate(self.enemy_team_labels):
            lbl.setFixedSize(64, 64)
            lbl.setStyleSheet("border:2px solid gray; background-color: #ffdddd;")  # default red
        # Blue side bans (ally)
        for i, lbl in enumerate(self.my_ban_labels):
            lbl.setFixedSize(48, 48)
            lbl.setStyleSheet("border:2px solid gray; background-color: #ddeeff;")  # blue inner color

        # Red side bans (enemy)
        for i, lbl in enumerate(self.enemy_ban_labels):
            lbl.setFixedSize(48, 48)
            lbl.setStyleSheet("border:2px solid gray; background-color: #ffdddd;")  # red inner color


        # Ban layout container
        self.bans_container = QWidget()
        self.bans_layout = QHBoxLayout(self.bans_container)
        for lbl in self.my_ban_labels:  # left side (blue)
            self.bans_layout.addWidget(lbl)
        self.bans_layout.addStretch()
        for lbl in self.enemy_ban_labels:  # right side (red)
            self.bans_layout.addWidget(lbl)
        self.champ_layout.addWidget(self.bans_container)
        self.bans_container.hide()  # initially hidden until champ select


        # Picks layout container
        self.picks_container = QWidget()
        self.picks_layout = QHBoxLayout(self.picks_container)

        # Blue side picks layout (left)
        self.blue_team_layout = QVBoxLayout()
        for lbl in self.my_team_labels:
            self.blue_team_layout.addWidget(lbl)
        self.picks_layout.addLayout(self.blue_team_layout)

        self.picks_layout.addStretch()

        # Red side picks layout (right)
        self.red_team_layout = QVBoxLayout()
        for lbl in self.enemy_team_labels:
            self.red_team_layout.addWidget(lbl)
        self.picks_layout.addLayout(self.red_team_layout)

        self.champ_layout.addWidget(self.picks_container)
        self.picks_container.hide()  # initially hidden until champ select


        self.stack.addWidget(self.champ_screen)


        # Timer
        self.champ_timer = QTimer(self)
        self.champ_timer.setInterval(1000)
        self.champ_timer.timeout.connect(self.update_champ_select)


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
        self.stack.setCurrentIndex(1)
        self.champ_timer.start()
        self.update_champ_select()

    def go_back(self):
        self.champ_timer.stop()
        self.stack.setCurrentIndex(0)

    def update_champ_select(self):
        client = LeagueClient()
        status, data = client.get_champ_select()

        # Reset all boxes first
        for lbl in self.my_team_labels + self.enemy_team_labels + self.my_ban_labels + self.enemy_ban_labels:
            lbl.clear()

        if status != 200 or not data:
            # No champ select
            self.champ_select_label.setText("Not in champ select.")
            self.champ_select_label.show()
            self.bans_container.hide()
            self.picks_container.hide()
            return

        # Champ select active
        self.champ_select_label.hide()
        self.bans_container.show()
        self.picks_container.show()


        # Determine blue/red side
        blue_team = []
        red_team = []
        for champ in data.get("myTeam", []) + data.get("theirTeam", []):
            if champ.get("team") == 1:
                blue_team.append(champ)
            else:
                red_team.append(champ)

        # Update picks
        for i, champ in enumerate(blue_team):
            if i >= 5:
                continue
            icon_path = self.champ_data.get_champion_icon(champ.get("championId"))
            if icon_path:
                pix = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl = self.blue_team_layout.itemAt(i).widget()
                lbl.setPixmap(pix)
                lbl.setStyleSheet("border:2px solid #0000ff; background-color: #ddeeff;")

        for i, champ in enumerate(red_team):
            if i >= 5:
                continue
            icon_path = self.champ_data.get_champion_icon(champ.get("championId"))
            if icon_path:
                pix = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl = self.red_team_layout.itemAt(i).widget()
                lbl.setPixmap(pix)
                lbl.setStyleSheet("border:2px solid #ff0000; background-color: #ffdddd;")

        # Update bans
        blue_ban_index = 0
        red_ban_index = 4
        for group in data.get("actions", []):
            for action in group:
                if action.get("type") != "ban" or not action.get("completed"):
                    continue
                champ_id = action.get("championId")
                icon_path = self.champ_data.get_champion_icon(champ_id)
                if not icon_path:
                    continue
                pix = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                team_side = 1 if action.get("isAllyAction") else 2
                if team_side == 1 and blue_ban_index < 5:
                    lbl = self.my_ban_labels[blue_ban_index]
                    lbl.setPixmap(pix)
                    lbl.setStyleSheet("border:2px solid #0000ff; background-color: #ddeeff;")
                    blue_ban_index += 1
                elif team_side == 2 and red_ban_index >= 0:
                    lbl = self.enemy_ban_labels[red_ban_index]
                    lbl.setPixmap(pix)
                    lbl.setStyleSheet("border:2px solid #ff0000; background-color: #ffdddd;")
                    red_ban_index -= 1


        # Update bans
        blue_ban_index = 0
        red_ban_index = 4

        for group in data.get("actions", []):
            for action in group:
                if action.get("type") != "ban" or not action.get("completed"):
                    continue
                champ_id = action.get("championId")
                icon_path = self.champ_data.get_champion_icon(champ_id)
                if not icon_path:
                    continue
                pix = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                team_side = 1 if action.get("isAllyAction") else 2
                if team_side == 1 and blue_ban_index < 5:  # Blue side bans (left)
                    lbl = self.my_ban_labels[blue_ban_index]
                    lbl.setPixmap(pix)
                    lbl.setStyleSheet("border:2px solid #0000ff; background-color: #ddeeff;")
                    blue_ban_index += 1
                elif team_side == 2 and red_ban_index >= 0:  # Red side bans (right)
                    lbl = self.enemy_ban_labels[red_ban_index]
                    lbl.setPixmap(pix)
                    lbl.setStyleSheet("border:2px solid #ff0000; background-color: #ffdddd;")
                    red_ban_index -= 1




        # Update bans using isAllyAction
        # Blue side bans → left → right
        # Red side bans → right → left
        blue_ban_index = 0
        red_ban_index = 4

        blue_ban_index = 0
        red_ban_index = 4

        for group in data.get("actions", []):
            for action in group:
                if action.get("type") != "ban" or not action.get("completed"):
                    continue
                champ_id = action.get("championId")
                icon_path = self.champ_data.get_champion_icon(champ_id)
                if not icon_path:
                    continue
                pix = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                team_side = 1 if action.get("isAllyAction") else 2
                if team_side == 1 and blue_ban_index < 5:  # Blue side bans (left)
                    lbl = self.my_ban_labels[blue_ban_index]
                    lbl.setPixmap(pix)
                    lbl.setStyleSheet("border:2px solid #0000ff; background-color: #ddeeff;")
                    blue_ban_index += 1
                elif team_side == 2 and red_ban_index >= 0:  # Red side bans (right)
                    lbl = self.enemy_ban_labels[red_ban_index]
                    lbl.setPixmap(pix)
                    lbl.setStyleSheet("border:2px solid #ff0000; background-color: #ffdddd;")
                    red_ban_index -= 1



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
        # Track normal geometry when not maximized/fullscreen
        if not (self.windowState() & Qt.WindowMaximized) and not (self.windowState() & Qt.WindowFullScreen):
            try:
                self.normal_geometry_rect = self.geometry()
                self.normal_geometry_data = self.saveGeometry()
            except Exception:
                pass

        # Scale fonts
        self.scale_fonts()
        
        # Scale emblems (solo/flex)
        QTimer.singleShot(0, self.scale_emblems)
        
        # Dynamically scale champion picks and bans
        QTimer.singleShot(0, self.update_box_sizes)
        
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

    def update_box_sizes(self):
        # Original fixed sizes
        pick_orig_w, pick_orig_h = 64, 64
        ban_orig_w, ban_orig_h = 48, 48

        # Determine available space in the champ screen
        total_width = self.champ_screen.width()
        total_height = self.champ_screen.height()

        # Picks: left/right vertical stacks (5 boxes)
        max_pick_height = total_height // 2  # leave room for other widgets, adjust if needed
        pick_scale_factor = min(max_pick_height / (pick_orig_h * 5), 1.0)  # don't shrink below original

        pick_size = QSize(int(pick_orig_w * pick_scale_factor), int(pick_orig_h * pick_scale_factor))

        # Blue picks
        for lbl in self.my_team_labels:
            lbl.setFixedSize(pick_size)
            self.scale_pixmap_to_label(lbl)

        # Red picks
        for lbl in self.enemy_team_labels:
            lbl.setFixedSize(pick_size)
            self.scale_pixmap_to_label(lbl)

        # Bans: horizontal, keep a small gap between blue/red side
        max_ban_width = (total_width - 40) // 10  # 5 per side, 40px total gap
        ban_scale_factor = min(max_ban_width / ban_orig_w, 1.0)  # don't shrink below original
        ban_size = QSize(int(ban_orig_w * ban_scale_factor), int(ban_orig_h * ban_scale_factor))

        # Blue bans
        for lbl in self.my_ban_labels:
            lbl.setFixedSize(ban_size)
            self.scale_pixmap_to_label(lbl)

        # Red bans
        for lbl in self.enemy_ban_labels:
            lbl.setFixedSize(ban_size)
            self.scale_pixmap_to_label(lbl)

    def scale_pixmap_to_label(self, lbl):
        pixmap = lbl.pixmap()
        if pixmap:
            # Keep the original pixmap aspect ratio
            scaled = pixmap.scaled(
                lbl.width(), lbl.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            lbl.setPixmap(scaled)

