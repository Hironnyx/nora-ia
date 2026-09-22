"""
QG de Nora (Franxx HUD Dashboard) :
- Mini-Dashboard visuel rétractable aux couleurs de Zero Two
- Garde-Robe Zero Two : 3 tenues sélectionnables (Pilote Franxx, Écolière, Hoodie)
- Mode Gaming (Boost FPS, Purge RAM Windows, Mode Silence Ne Pas Déranger)
- Typographie agrandie et haute lisibilité (contrastes nets, polices 13-15px)
- Télémétrie système en temps réel (CPU, RAM, Disque, Score Sécurité sur 100)
- Statut en direct de l'équipe de 5 agents
- Boîte d'initiatives interactive avec boutons Valider et Refuser
- Raccourcis d'actions rapides en 1 clic
"""
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QProgressBar, QFrame, QScrollArea, QGraphicsDropShadowEffect, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QFont, QCursor

import system_monitor
import agent_security
import nora_initiatives
import gaming_mode
import memory_manager
import mascot_assets

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

class QGDashboard(QWidget):
    """Panneau de contrôle rétractable style Franxx HUD avec texte clair et agrandi."""

    initiative_accepted = pyqtSignal(str)
    initiative_refused = pyqtSignal(str)
    action_requested = pyqtSignal(str)
    outfit_changed = pyqtSignal(str)
    gaming_mode_toggled = pyqtSignal(bool)
    ram_boost_requested = pyqtSignal()
    screen_vision_requested = pyqtSignal()
    voice_cloning_toggled = pyqtSignal(bool)

    def __init__(self, parent_mascot=None):
        super().__init__()
        self.parent_mascot = parent_mascot
        self.current_outfit = memory_manager.get_current_outfit()
        self.init_ui()

        # Timer de rafraîchissement des sondes en temps réel (toutes les 2.5 secondes)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_telemetry)
        self.refresh_timer.start(2500)

        self.update_telemetry()
        self.update_outfit_buttons(self.current_outfit)
        self.update_gaming_ui()
        self.update_vc_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 775)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Conteneur principal avec bordure rose Zero Two
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.98);
                border: 2px solid #fb7185;
                border-radius: 18px;
            }
        """)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(14, 14, 14, 14)
        container_layout.setSpacing(10)

        # 1. En-tête HUD Classique & Esthétique
        header_layout = QHBoxLayout()
        title_label = QLabel("🌸 QG DE NORA - QUARTIER GÉNÉRAL")
        title_label.setStyleSheet("""
            color: #fda4af;
            font-weight: 800;
            font-size: 14px;
            letter-spacing: 0.5px;
            border: none;
        """)
        header_layout.addWidget(title_label)

        # Bouton Réduire / Masquer
        min_btn = QPushButton("—")
        min_btn.setFixedSize(26, 26)
        min_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        min_btn.setToolTip("Réduire / Masquer le QG")
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #ffffff;
                border: none;
                border-radius: 13px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        min_btn.clicked.connect(self.hide)
        header_layout.addWidget(min_btn)

        # Bouton Fermer
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setToolTip("Fermer le QG")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #ffffff;
                border: none;
                border-radius: 13px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e11d48;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        container_layout.addLayout(header_layout)

        # 2. Section Métriques Systèmes en Direct
        metrics_box = QFrame()
        metrics_box.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.7);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 8px;
        """)
        metrics_layout = QVBoxLayout(metrics_box)
        metrics_layout.setSpacing(6)

        # CPU
        self.cpu_label = QLabel("⚡ Processeur : --%")
        self.cpu_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold; border: none;")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setStyleSheet("""
            QProgressBar { background-color: #0f172a; border-radius: 5px; height: 8px; text-align: right; border: none; }
            QProgressBar::chunk { background-color: #06b6d4; border-radius: 5px; }
        """)
        metrics_layout.addWidget(self.cpu_label)
        metrics_layout.addWidget(self.cpu_bar)

        # RAM
        self.ram_label = QLabel("🧠 Mémoire RAM : --%")
        self.ram_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold; border: none;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setStyleSheet("""
            QProgressBar { background-color: #0f172a; border-radius: 5px; height: 8px; border: none; }
            QProgressBar::chunk { background-color: #e11d48; border-radius: 5px; }
        """)
        metrics_layout.addWidget(self.ram_label)
        metrics_layout.addWidget(self.ram_bar)

        # Disque & Sécurité
        stats_row = QHBoxLayout()
        self.disk_label = QLabel("💾 Disque C: -- Go libre")
        self.disk_label.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 600; border: none;")
        
        self.sec_label = QLabel("🛡️ Sécurité : 85/100")
        self.sec_label.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 800; border: none;")
        
        stats_row.addWidget(self.disk_label)
        stats_row.addWidget(self.sec_label)
        metrics_layout.addLayout(stats_row)

        container_layout.addWidget(metrics_box)

        # 3. GARDE-ROBE ZERO TWO (3 Tenues)
        wardrobe_box = QFrame()
        wardrobe_box.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.6);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 8px;
        """)
        wardrobe_layout = QVBoxLayout(wardrobe_box)
        wardrobe_layout.setSpacing(6)

        lbl_wardrobe = QLabel("👗 GARDE-ROBE ZERO TWO :")
        lbl_wardrobe.setStyleSheet("color: #fb7185; font-size: 12px; font-weight: 800; border: none;")
        wardrobe_layout.addWidget(lbl_wardrobe)

        outfits_row = QHBoxLayout()
        outfits_row.setSpacing(6)

        self.btn_franxx = QPushButton("🚀 Pilote Franxx")
        self.btn_school = QPushButton("🎓 Écolière")
        self.btn_hoodie = QPushButton("🧸 Hoodie")

        for b in [self.btn_franxx, self.btn_school, self.btn_hoodie]:
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.btn_franxx.clicked.connect(lambda: self.on_select_outfit("franxx"))
        self.btn_school.clicked.connect(lambda: self.on_select_outfit("school"))
        self.btn_hoodie.clicked.connect(lambda: self.on_select_outfit("hoodie"))

        outfits_row.addWidget(self.btn_franxx)
        outfits_row.addWidget(self.btn_school)
        outfits_row.addWidget(self.btn_hoodie)
        wardrobe_layout.addLayout(outfits_row)
        container_layout.addWidget(wardrobe_box)

        # 4. MODE GAMING & BOOST RAM
        gaming_box = QFrame()
        gaming_box.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.6);
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 8px;
        """)
        gaming_layout = QHBoxLayout(gaming_box)
        gaming_layout.setSpacing(8)

        self.btn_gaming_toggle = QPushButton("🎮 Mode Gaming : INACTIF ⚪")
        self.btn_gaming_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_gaming_toggle.clicked.connect(self.on_toggle_gaming)

        self.btn_ram_boost = QPushButton("⚡ Boost RAM")
        self.btn_ram_boost.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ram_boost.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: 1px solid #38bdf8;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_ram_boost.clicked.connect(self.on_ram_boost_click)

        gaming_layout.addWidget(self.btn_gaming_toggle, stretch=2)
        gaming_layout.addWidget(self.btn_ram_boost, stretch=1)
        container_layout.addWidget(gaming_box)

        # 4b. CLONAGE VOCAL ZERO TWO RVC (RTX 4080)
        vc_box = QFrame()
        vc_box.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.6);
            border: 1px solid #fb7185;
            border-radius: 12px;
            padding: 6px 8px;
        """)
        vc_layout = QHBoxLayout(vc_box)
        vc_layout.setSpacing(8)

        self.btn_vc_toggle = QPushButton("🎙️ Voix Zero Two RVC : ACTIVE 💖")
        self.btn_vc_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_vc_toggle.clicked.connect(self.on_toggle_voice_cloning)

        self.lbl_vc_gpu = QLabel("⚡ RTX 4080")
        self.lbl_vc_gpu.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold; border: none;")
        self.lbl_vc_gpu.setAlignment(Qt.AlignmentFlag.AlignCenter)

        vc_layout.addWidget(self.btn_vc_toggle, stretch=3)
        vc_layout.addWidget(self.lbl_vc_gpu, stretch=1)
        container_layout.addWidget(vc_box)

        # 5. Section Statut des Agents IA
        agents_box = QFrame()
        agents_box.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.4);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 6px 10px;
        """)
        agents_layout = QVBoxLayout(agents_box)
        agents_layout.setSpacing(4)

        sec_title = QLabel("🤖 ÉQUIPE D'AGENTS FRANXX :")
        sec_title.setStyleSheet("color: #fb7185; font-size: 11px; font-weight: 800; border: none;")
        agents_layout.addWidget(sec_title)

        agents_grid = QHBoxLayout()
        col1 = QVBoxLayout()
        self.lbl_a1 = QLabel("👑 Orchestrateur : 🟢")
        self.lbl_a2 = QLabel("💻 Contrôleur PC : 🟢")
        self.lbl_a3 = QLabel("🌐 Pilote Web : 🟢")
        self.lbl_a4 = QLabel("🎨 Agent Designer : 🟢")
        for lbl in [self.lbl_a1, self.lbl_a2, self.lbl_a3, self.lbl_a4]:
            lbl.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: 500; border: none; padding: 1px 0;")
            col1.addWidget(lbl)

        col2 = QVBoxLayout()
        self.lbl_a5 = QLabel("🛡️ Agent Sécurité : 🛡️ Actif")
        self.lbl_a6 = QLabel("🌸 Zero Two : 💖 Prête")
        self.lbl_a7 = QLabel("🏠 Domotique : 🟢 Hue")
        for lbl in [self.lbl_a5, self.lbl_a6, self.lbl_a7]:
            lbl.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: 500; border: none; padding: 1px 0;")
            col2.addWidget(lbl)

        agents_grid.addLayout(col1)
        agents_grid.addLayout(col2)
        agents_layout.addLayout(agents_grid)
        container_layout.addWidget(agents_box)

        # 6. Boîte d'Initiative Proactive
        self.init_box = QFrame()
        self.init_box.setStyleSheet("""
            background-color: rgba(225, 29, 72, 0.15);
            border: 2px solid #fb7185;
            border-radius: 12px;
            padding: 8px;
        """)
        self.init_layout = QVBoxLayout(self.init_box)
        self.init_layout.setSpacing(6)

        self.init_title = QLabel("💡 INITIATIVE PROPOSÉE PAR NORA :")
        self.init_title.setStyleSheet("color: #fecdd3; font-size: 11px; font-weight: 800; border: none;")
        
        self.init_text = QLabel("Nora observe ton PC. Aucune initiative requise pour le moment !")
        self.init_text.setWordWrap(True)
        self.init_text.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 500;
            line-height: 1.3;
            border: none;
            padding: 1px 0;
        """)
        
        self.init_buttons_layout = QHBoxLayout()
        self.init_buttons_layout.setSpacing(8)

        self.btn_validate = QPushButton("Oui, vas-y ! ✅")
        self.btn_validate.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_validate.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_validate.clicked.connect(self.on_validate_initiative)

        self.btn_refuse = QPushButton("Non merci ❌")
        self.btn_refuse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_refuse.setStyleSheet("""
            QPushButton {
                background-color: #475569;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #64748b;
            }
        """)
        self.btn_refuse.clicked.connect(self.on_refuse_initiative)

        self.init_buttons_layout.addWidget(self.btn_validate)
        self.init_buttons_layout.addWidget(self.btn_refuse)

        self.init_layout.addWidget(self.init_title)
        self.init_layout.addWidget(self.init_text)
        self.init_layout.addLayout(self.init_buttons_layout)
        container_layout.addWidget(self.init_box)

        # 7. Raccourcis d'actions rapides
        actions_row = QHBoxLayout()
        actions_row.setSpacing(6)

        btn_scan = QPushButton("🛡️ Scan")
        btn_scan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #ffffff;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e11d48;
                border-color: #fb7185;
            }
        """)
        btn_scan.clicked.connect(lambda: self.action_requested.emit("security_scan"))

        btn_clean = QPushButton("🧹 Ranger")
        btn_clean.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_clean.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #ffffff;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e11d48;
                border-color: #fb7185;
            }
        """)
        btn_clean.clicked.connect(lambda: self.action_requested.emit("organize_downloads"))

        btn_web = QPushButton("🌐 Web")
        btn_web.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_web.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #ffffff;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e11d48;
                border-color: #fb7185;
            }
        """)
        btn_web.clicked.connect(lambda: self.action_requested.emit("web_search"))

        btn_vision = QPushButton("👁️ Vision")
        btn_vision.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_vision.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                border: 1px solid #2dd4bf;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0d9488;
                border-color: #5eead4;
            }
        """)
        btn_home = QPushButton("🏠 Maison")
        btn_home.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_home.setStyleSheet("""
            QPushButton {
                background-color: #4338ca;
                color: #ffffff;
                border: 1px solid #818cf8;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3730a3;
                border-color: #a5b4fc;
            }
        """)
        btn_home.clicked.connect(lambda: self.action_requested.emit("smart_home_panel"))

        actions_row.addWidget(btn_vision)
        actions_row.addWidget(btn_scan)
        actions_row.addWidget(btn_home)
        actions_row.addWidget(btn_clean)
        actions_row.addWidget(btn_web)
        container_layout.addLayout(actions_row)

        # 8. Barre de Saisie & Chat Direct Classique
        chat_box = QFrame()
        chat_box.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.95);
                border: 2px solid #f43f5e;
                border-radius: 12px;
            }
        """)
        chat_layout = QHBoxLayout(chat_box)
        chat_layout.setContentsMargins(8, 4, 8, 4)
        chat_layout.setSpacing(6)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Écrire à Nora ou lui donner un ordre... (Entrée pour envoyer)")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: #ffffff;
                border: none;
                font-size: 12px;
                font-weight: 500;
                padding: 4px;
            }
        """)
        self.input_field.returnPressed.connect(self.submit_qg_chat)
        chat_layout.addWidget(self.input_field)

        self.btn_send = QPushButton("➤")
        self.btn_send.setFixedSize(28, 28)
        self.btn_send.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_send.setToolTip("Envoyer le message")
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #e11d48;
                color: white;
                border-radius: 14px;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover { background-color: #f43f5e; }
        """)
        self.btn_send.clicked.connect(self.submit_qg_chat)
        chat_layout.addWidget(self.btn_send)

        self.btn_mic = QPushButton("🎙️")
        self.btn_mic.setFixedSize(28, 28)
        self.btn_mic.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_mic.setToolTip("Parler au micro à Nora")
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background-color: #be185d;
                color: white;
                border-radius: 14px;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover { background-color: #db2777; }
        """)
        self.btn_mic.clicked.connect(self.on_mic_click)
        chat_layout.addWidget(self.btn_mic)

        self.btn_handsfree = QPushButton("🎧")
        self.btn_handsfree.setFixedSize(28, 28)
        self.btn_handsfree.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_handsfree.setToolTip("Mode Mains-Libres ('Dis Nora')")
        self.btn_handsfree.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #94a3b8;
                border-radius: 14px;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        self.btn_handsfree.clicked.connect(self.on_handsfree_click)
        chat_layout.addWidget(self.btn_handsfree)

        container_layout.addWidget(chat_box)

        layout.addWidget(self.container)
        self.setLayout(layout)

    def submit_qg_chat(self):
        """Envoie le message saisi dans le QG à Nora."""
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            if self.parent_mascot:
                self.parent_mascot.process_user_message(text)

    def on_mic_click(self):
        """Déclenche la capture vocale via Nora."""
        if self.parent_mascot:
            self.parent_mascot.start_voice_input()

    def on_handsfree_click(self):
        """Bascule le mode mains-libres 'Dis Nora'."""
        if self.parent_mascot:
            self.parent_mascot.toggle_hands_free()
            self.update_handsfree_button()

    def update_handsfree_button(self):
        """Met à jour l'apparence du bouton mains-libres selon son état."""
        if self.parent_mascot:
            active = getattr(self.parent_mascot, 'hands_free_enabled', False)
            if active:
                self.btn_handsfree.setStyleSheet("""
                    QPushButton { background-color: #10b981; color: white; border-radius: 14px; font-size: 13px; border: none; }
                    QPushButton:hover { background-color: #059669; }
                """)
            else:
                self.btn_handsfree.setStyleSheet("""
                    QPushButton { background-color: #334155; color: #94a3b8; border-radius: 14px; font-size: 13px; border: none; }
                    QPushButton:hover { background-color: #475569; }
                """)

    def on_select_outfit(self, outfit: str):
        """Sélectionne une tenue et prévient les écouteurs."""
        self.current_outfit = outfit
        self.update_outfit_buttons(outfit)
        self.outfit_changed.emit(outfit)

    def update_outfit_buttons(self, active_outfit: str):
        """Met en surbrillance la tenue active."""
        self.current_outfit = active_outfit
        buttons = {
            "franxx": self.btn_franxx,
            "school": self.btn_school,
            "hoodie": self.btn_hoodie
        }
        for key, btn in buttons.items():
            if key == active_outfit:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e11d48;
                        color: #ffffff;
                        border: 2px solid #fda4af;
                        border-radius: 8px;
                        padding: 6px 6px;
                        font-size: 11px;
                        font-weight: 800;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1e293b;
                        color: #cbd5e1;
                        border: 1px solid #475569;
                        border-radius: 8px;
                        padding: 6px 6px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #334155;
                        color: #ffffff;
                    }
                """)

    def on_toggle_gaming(self):
        """Bascule l'état du mode gaming."""
        new_state, msg = gaming_mode.toggle_gaming_mode()
        self.update_gaming_ui()
        self.update_telemetry()
        self.gaming_mode_toggled.emit(new_state)

    def update_gaming_ui(self):
        """Met à jour l'état visuel du bouton Gaming."""
        active = gaming_mode.is_gaming_mode()
        if active:
            self.btn_gaming_toggle.setText("🎮 Mode Gaming : ACTIF 🟢")
            self.btn_gaming_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #059669;
                    color: #ffffff;
                    border: 2px solid #34d399;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-size: 11px;
                    font-weight: 800;
                }
                QPushButton:hover {
                    background-color: #047857;
                }
            """)
        else:
            self.btn_gaming_toggle.setText("🎮 Mode Gaming : INACTIF ⚪")
            self.btn_gaming_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #94a3b8;
                    border: 1px solid #475569;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #ffffff;
                }
            """)

    def on_ram_boost_click(self):
        """Déclenche la purge RAM manuelle."""
        count, freed = gaming_mode.optimize_ram_boost()
        self.update_telemetry()
        self.ram_boost_requested.emit()
        self.init_box.show()
        self.init_title.setText("⚡ BOOST RAM TERMINÉ :")
        self.init_text.setText(f"{count} applications en arrière-plan purgées. {freed} Mo de RAM libérés pour vos jeux !")
        self.btn_validate.hide()
        self.btn_refuse.hide()

    def update_vc_ui(self):
        """Met à jour l'état visuel du bouton Voix Zero Two."""
        active = memory_manager.is_voice_cloning_enabled()
        if active:
            self.btn_vc_toggle.setText("🎙️ Voix Zero Two RVC : ACTIVE 💖")
            self.btn_vc_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #be185d;
                    color: #ffffff;
                    border: 1px solid #f472b6;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-size: 11px;
                    font-weight: 800;
                }
                QPushButton:hover {
                    background-color: #9d174d;
                }
            """)
            if hasattr(self, 'lbl_a6'):
                self.lbl_a6.setText("🌸 Zero Two : 💖 Voix RVC")
        else:
            self.btn_vc_toggle.setText("🎙️ Voix Zero Two RVC : INACTIVE ⚪")
            self.btn_vc_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #94a3b8;
                    border: 1px solid #475569;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #ffffff;
                }
            """)
            if hasattr(self, 'lbl_a6'):
                self.lbl_a6.setText("🌸 Zero Two : ⏸️ Standard")

    def on_toggle_voice_cloning(self):
        """Bascule l'activation de la voix IA Zero Two (RVC GPU)."""
        new_state = not memory_manager.is_voice_cloning_enabled()
        memory_manager.set_voice_cloning_enabled(new_state)
        self.update_vc_ui()
        self.voice_cloning_toggled.emit(new_state)

    def update_telemetry(self):
        """Met à jour les sondes et vérifie les initiatives disponibles."""
        stats = system_monitor.get_system_stats()
        cpu = stats["cpu_percent"]
        ram = stats["ram_percent"]
        free_gb = stats["disk"]["free_gb"]

        self.cpu_label.setText(f"⚡ Processeur : {cpu}%")
        self.cpu_bar.setValue(int(cpu))

        self.ram_label.setText(f"🧠 Mémoire RAM : {ram}% ({stats['ram_used_gb']} Go / {stats['ram_total_gb']} Go)")
        self.ram_bar.setValue(int(ram))

        self.disk_label.setText(f"💾 Disque C: {free_gb} Go libres")

        # Sonde Domotique Philips Hue
        try:
            import agent_home
            if agent_home.smart_home.is_hue_paired():
                self.lbl_a7.setText("🏠 Domotique : 💖 Hue Connecté")
            else:
                self.lbl_a7.setText("🏠 Domotique : 🟢 Hue Détecté")
        except Exception:
            pass

        # Vérifier l'initiative
        current_init = nora_initiatives.get_pending_initiative()
        if not current_init:
            current_init = nora_initiatives.scan_for_initiatives()

        if current_init:
            self.init_box.show()
            self.init_title.setText(f"💡 IDÉE DE NORA : {current_init['title'].upper()}")
            self.init_text.setText(current_init["speech"])
            self.btn_validate.show()
            self.btn_refuse.show()
        else:
            self.init_title.setText("💡 VEILLE PROACTIVE :")
            self.init_text.setText("Tout est propre et sous haute sécurité, Maverick. Aucune action requise !")
            self.btn_validate.hide()
            self.btn_refuse.hide()

    def on_validate_initiative(self):
        init = nora_initiatives.get_pending_initiative()
        if init:
            self.initiative_accepted.emit(init["id"])
            self.update_telemetry()

    def on_refuse_initiative(self):
        init = nora_initiatives.get_pending_initiative()
        if init:
            self.initiative_refused.emit(init["id"])
            self.update_telemetry()

    def mousePressEvent(self, event):
        """Permet de déplacer le QG librement avec la souris."""
        self.raise_()
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Déplacement fluide du QG sur n'importe quel écran."""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_pos'):
            self._user_moved = True
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def toggle_near(self, point: QPoint, mascot_width: int = 240):
        """Ouvre ou ferme le dashboard de façon esthétique."""
        if self.isVisible():
            self.hide()
        else:
            if not getattr(self, '_user_moved', False):
                self.position_near(point, mascot_width)
            self.update_telemetry()
            self.update_outfit_buttons(memory_manager.get_current_outfit())
            self.update_gaming_ui()
            self.update_vc_ui()
            self.update_handsfree_button()
            self.show()
            self.raise_()
            self.activateWindow()
            if hasattr(self, 'input_field'):
                self.input_field.setFocus()

    def position_near(self, point: QPoint, mascot_width: int = 310):
        """Positionne le QG intelligemment sans AUCUN chevauchement sur tous les écrans."""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.screenAt(point) or QApplication.primaryScreen()
        s_geom = screen.availableGeometry()

        qg_w = self.width()
        qg_h = self.height()

        # 1. Tenter de placer à gauche de Nora
        dash_x = point.x() - qg_w - 15

        # 2. Si pas assez de place à gauche sur cet écran, placer à droite de Nora
        if dash_x < s_geom.left():
            dash_x = point.x() + mascot_width + 15

        # 3. Si même à droite ça dépasse l'écran, s'aligner sur le bord droit
        if dash_x + qg_w > s_geom.right():
            dash_x = s_geom.right() - qg_w

        # 4. Ajustement vertical sans sortir de l'écran
        dash_y = point.y() - 80
        dash_y = max(s_geom.top() + 10, min(s_geom.bottom() - qg_h - 10, dash_y))

        self.move(dash_x, dash_y)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dash = QGDashboard()
    dash.show()
    sys.exit(app.exec())
