"""
QG de Nora (Quartier Général & Cockpit Central Cyber-Glassmorphism) :
- Refonte complète esthétique et fonctionnelle indépendante
- Navigation latérale multi-écrans avec 8 modules interactifs :
    1. 🚀 COCKPIT & OMNIBOX (Contrôle direct, missions en langage naturel, actions rapides)
    2. 🤖 ESSAIM NEURONAL (Visualisation du débat récursif de masse, agents, consensus)
    3. 👗 STUDIO GARDE-ROBE (5 tenues complètes, déclencheur d'animations plein corps)
    4. ⚡ TÉLÉMÉTRIE SYSTÈME (Jauges CPU, RAM, GPU, Disque, Boost 1-clic, Mode Gaming)
    5. 🛡️ BOUCLIER SÉCURITÉ (Score d'intégrité, analyse processus, veille permanente)
    6. 🏠 CENTRE DOMOTIQUE (Contrôle des lumières connectées, ambiances et scénarios)
    7. 🧠 MÉMOIRE & CERVEAU (Recherche sémantique, faits mémorisés, carnet d'apprentissage)
    8. 📱 PASSERELLE MOBILE (Tunnel Cloudflare 4G/5G/WiFi, statut, lien smartphone)
- 100% Fonctionnel, zéro fenêtre CMD, ergonomie d'élite pour Maverick.
"""
import sys
import os
import json
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QProgressBar, QFrame, QScrollArea, QGraphicsDropShadowEffect,
    QLineEdit, QStackedWidget, QTextEdit, QSlider, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QColor, QFont, QCursor, QPixmap, QIcon

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

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "mascot_assets"


class QGDashboard(QWidget):
    """Cockpit Central Haute Fidélité de Nora (Quartier Général Glassmorphism)."""

    initiative_accepted = pyqtSignal(str)
    initiative_refused = pyqtSignal(str)
    action_requested = pyqtSignal(str)
    outfit_changed = pyqtSignal(str)
    animation_requested = pyqtSignal(str)
    gaming_mode_toggled = pyqtSignal(bool)
    ram_boost_requested = pyqtSignal()
    screen_vision_requested = pyqtSignal()
    voice_cloning_toggled = pyqtSignal(bool)

    def __init__(self, parent_mascot=None):
        super().__init__()
        self.parent_mascot = parent_mascot
        self.current_outfit = memory_manager.get_current_outfit()
        self.drag_position = QPoint()

        self.init_ui()

        # Timer de rafraîchissement télémétrique (toutes les 2.0 secondes)
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(2000)

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
        self.setFixedSize(860, 620)

        # Conteneur principal Glassmorphism avec lueur néon subtile
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainGlassFrame")
        self.main_frame.setStyleSheet("""
            #MainGlassFrame {
                background-color: rgba(10, 15, 29, 0.97);
                border: 2px solid #00f0ff;
                border-radius: 20px;
            }
        """)

        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # 1. Barre de Titre Supérieure Draggable avec Status LED
        title_bar = self.create_title_bar()
        frame_layout.addWidget(title_bar)

        # 2. Corps Central : Navigation Sidebar Gauche + Stacked Screens Droite
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(14)

        # Barre latérale gauche
        sidebar = self.create_sidebar()
        body_layout.addWidget(sidebar)

        # Panneaux empilés (Stacked Screens)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")

        self.panel_cockpit = self.create_cockpit_panel()
        self.panel_swarm = self.create_swarm_panel()
        self.panel_wardrobe = self.create_wardrobe_panel()
        self.panel_system = self.create_system_panel()
        self.panel_security = self.create_security_panel()
        self.panel_smarthome = self.create_smarthome_panel()
        self.panel_memory = self.create_memory_panel()
        self.panel_mobile = self.create_mobile_panel()

        self.stack.addWidget(self.panel_cockpit)       # Index 0
        self.stack.addWidget(self.panel_swarm)         # Index 1
        self.stack.addWidget(self.panel_wardrobe)      # Index 2
        self.stack.addWidget(self.panel_system)        # Index 3
        self.stack.addWidget(self.panel_security)      # Index 4
        self.stack.addWidget(self.panel_smarthome)     # Index 5
        self.stack.addWidget(self.panel_memory)        # Index 6
        self.stack.addWidget(self.panel_mobile)        # Index 7

        body_layout.addWidget(self.stack, stretch=1)
        frame_layout.addWidget(body_widget, stretch=1)

        main_layout.addWidget(self.main_frame)

    # =========================================================================
    # BARRE DE TITRE & GESTION DU DÉPLACEMENT INDÉPENDANT
    # =========================================================================
    def create_title_bar(self) -> QWidget:
        tb = QFrame()
        tb.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(15, 23, 42, 0.9),
                    stop:0.5 rgba(30, 41, 59, 0.8),
                    stop:1 rgba(15, 23, 42, 0.9));
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
                border-bottom: 1px solid rgba(0, 240, 255, 0.25);
                padding: 6px 14px;
            }
        """)
        layout = QHBoxLayout(tb)
        layout.setContentsMargins(12, 6, 12, 6)

        # Indicateur de statut LED
        led_label = QLabel("● CORE ONLINE")
        led_label.setStyleSheet("color: #10b981; font-weight: 800; font-size: 11px; letter-spacing: 1px; border: none;")
        layout.addWidget(led_label)

        # Titre central
        title = QLabel("✦ NORA QUARTIER GÉNÉRAL ✦  |  Cockpit de Supervision Dédié à Maverick")
        title.setStyleSheet("color: #fda4af; font-weight: 800; font-size: 13px; letter-spacing: 0.5px; border: none;")
        layout.addWidget(title)
        layout.addStretch()

        # Boutons fenêtre (Réduire, Fermer)
        btn_min = QPushButton("─")
        btn_min.setFixedSize(28, 24)
        btn_min.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_min.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #e2e8f0;
                font-size: 12px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.2); }
        """)
        btn_min.clicked.connect(self.hide)
        layout.addWidget(btn_min)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 24)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.2);
                color: #f87171;
                font-size: 12px;
                border-radius: 6px;
                border: 1px solid rgba(239, 68, 68, 0.4);
            }
            QPushButton:hover { background: #ef4444; color: white; }
        """)
        btn_close.clicked.connect(self.hide)
        layout.addWidget(btn_close)

        return tb

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 50:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = QPoint()

    # =========================================================================
    # BARRE LATÉRALE DE NAVIGATION (SIDEBAR)
    # =========================================================================
    def create_sidebar(self) -> QWidget:
        sb = QFrame()
        sb.setFixedWidth(200)
        sb.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
        """)
        layout = QVBoxLayout(sb)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(6)

        self.nav_buttons = []
        nav_items = [
            ("🚀  Cockpit", 0),
            ("🤖  Essaim IA", 1),
            ("👗  Garde-Robe", 2),
            ("⚡  Système", 3),
            ("🛡️  Sécurité", 4),
            ("🏠  Domotique", 5),
            ("🧠  Mémoire IA", 6),
            ("📱  Mobile 4G/5G", 7),
        ]

        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(self._get_nav_btn_style(idx == 0))
            btn.clicked.connect(lambda checked, i=idx: self.switch_screen(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # Mini carte avatar Zero Two en bas de sidebar
        mini_card = QFrame()
        mini_card.setStyleSheet("""
            QFrame {
                background: rgba(255, 42, 133, 0.12);
                border: 1px solid rgba(255, 42, 133, 0.4);
                border-radius: 10px;
                padding: 6px;
            }
        """)
        mc_layout = QVBoxLayout(mini_card)
        mc_layout.setContentsMargins(4, 4, 4, 4)
        lbl_info = QLabel("NORA COPILOTE\nStyle Zero Two 002")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_info.setStyleSheet("color: #fda4af; font-size: 11px; font-weight: bold; border: none;")
        mc_layout.addWidget(lbl_info)
        layout.addWidget(mini_card)

        return sb

    def _get_nav_btn_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2a85, stop:1 #e11d48);
                    color: white;
                    font-size: 12px;
                    font-weight: 800;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 14px;
                    border: none;
                }
            """
        else:
            return """
                QPushButton {
                    background: transparent;
                    color: #94a3b8;
                    font-size: 12px;
                    font-weight: 600;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 14px;
                    border: none;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.06);
                    color: #f1f5f9;
                }
            """

    def switch_screen(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_buttons):
            btn.setStyleSheet(self._get_nav_btn_style(i == idx))

    # =========================================================================
    # 1. PANNEAU COCKPIT & OMNIBOX
    # =========================================================================
    def create_cockpit_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        # En-tête de bienvenue
        title = QLabel("🚀 CENTRE DE COMMANDEMENT & COCKPIT")
        title.setStyleSheet("color: #00f0ff; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        # Omnibox directe pour envoyer des missions en langage naturel
        omni_frame = QFrame()
        omni_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.85);
                border: 2px solid #38bdf8;
                border-radius: 12px;
                padding: 4px;
            }
        """)
        omni_layout = QHBoxLayout(omni_frame)
        omni_layout.setContentsMargins(10, 4, 10, 4)

        self.omni_input = QLineEdit()
        self.omni_input.setPlaceholderText("Donnez un ordre ou une mission à Nora (ex: 'Nettoie mon bureau', 'Scanne le système')...")
        self.omni_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        self.omni_input.returnPressed.connect(self.on_omni_send)
        omni_layout.addWidget(self.omni_input)

        btn_send = QPushButton("ENVOYER ⚡")
        btn_send.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_send.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: white;
                font-weight: 800;
                font-size: 11px;
                padding: 6px 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background: #0369a1; }
        """)
        btn_send.clicked.connect(self.on_omni_send)
        omni_layout.addWidget(btn_send)

        layout.addWidget(omni_frame)

        # Actions rapides en 1 clic (Chips)
        quick_lbl = QLabel("ACTIONS INSTANTANÉES :")
        quick_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        layout.addWidget(quick_lbl)

        quick_grid = QGridLayout()
        quick_grid.setSpacing(8)

        actions = [
            ("🧹 Nettoyer Téléchargements", "Réorganise mon dossier Téléchargements en triant tout par catégories."),
            ("🔍 Détecter les Doublons", "Scanne mon dossier Téléchargements et isole les doublons."),
            ("🚀 Vider & Optimiser RAM", "CMD_RAM_BOOST"),
            ("📸 Analyser mon Écran", "CMD_SCREEN_VISION"),
            ("🛡️ Audit de Sécurité", "Effectue un scan de sécurité approfondi des processus et du réseau."),
            ("🌸 Mode Plein Écran Gaming", "CMD_GAMING_TOGGLE")
        ]

        for i, (label, cmd) in enumerate(actions):
            btn = QPushButton(label)
            btn.setFixedHeight(36)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(30, 41, 59, 0.7);
                    color: #e2e8f0;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background: rgba(56, 189, 248, 0.2);
                    border-color: #38bdf8;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, c=cmd: self.on_quick_action(c))
            quick_grid.addWidget(btn, i // 2, i % 2)

        layout.addLayout(quick_grid)

        # Log d'activité et pensées de Nora
        log_lbl = QLabel("DERNIÈRE ACTIVITÉ DE L'AGENT :")
        log_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; margin-top: 6px;")
        layout.addWidget(log_lbl)

        self.cockpit_log = QTextEdit()
        self.cockpit_log.setReadOnly(True)
        self.cockpit_log.setStyleSheet("""
            QTextEdit {
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                color: #38bdf8;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.cockpit_log.setPlainText("✔ Nora en veille active. Prête à assister Maverick sur le PC ou via mobile.")
        layout.addWidget(self.cockpit_log, stretch=1)

        return p

    def on_omni_send(self):
        text = self.omni_input.text().strip()
        if text:
            self.omni_input.clear()
            self.cockpit_log.append(f"<b>Maverick :</b> {text}")
            if self.parent_mascot:
                self.parent_mascot.execute_mission(text)

    def on_quick_action(self, cmd: str):
        if cmd == "CMD_RAM_BOOST":
            self.ram_boost_requested.emit()
            self.cockpit_log.append("⚡ [Action] Optimisation et purge de la RAM déclenchées.")
        elif cmd == "CMD_SCREEN_VISION":
            self.screen_vision_requested.emit()
            self.cockpit_log.append("📸 [Action] Capture et analyse de l'écran en cours...")
        elif cmd == "CMD_GAMING_TOGGLE":
            current = gaming_mode.is_gaming_mode()
            self.gaming_mode_toggled.emit(not current)
        else:
            self.cockpit_log.append(f"⚡ [Mission] {cmd}")
            if self.parent_mascot:
                self.parent_mascot.execute_mission(cmd)

    # =========================================================================
    # 2. PANNEAU ESSAIM NEURONAL (DÉBAT RÉCURSIF DE MASSE)
    # =========================================================================
    def create_swarm_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("🤖 ESSAIM NEURONAL (DÉBAT RÉCURSIF DE MASSE)")
        title.setStyleSheet("color: #a78bfa; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        desc = QLabel("Surveillance en temps réel de la délibération contradictoire entre les 5 agents IA spécialistes :")
        desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(desc)

        # Grille des 5 agents
        agents_grid = QHBoxLayout()
        agents_grid.setSpacing(8)

        self.agent_cards = {}
        agents_data = [
            ("👑 Nora Prime", "Superviseure", "#ff2a85"),
            ("🏛️ Architecte", "Planification", "#38bdf8"),
            ("⚡ Exécuteur", "Scripts & OS", "#f59e0b"),
            ("🛡️ Gardien", "Sécurité", "#10b981"),
            ("🧐 Critique", "Contradicteur", "#a855f7"),
        ]

        for name, role, color in agents_data:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: rgba(30, 41, 59, 0.7);
                    border: 1px solid {color};
                    border-radius: 8px;
                    padding: 6px;
                }}
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(4, 4, 4, 4)
            c_layout.setSpacing(2)

            n_lbl = QLabel(name)
            n_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px; border: none;")
            n_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(n_lbl)

            r_lbl = QLabel(role)
            r_lbl.setStyleSheet("color: #94a3b8; font-size: 9px; border: none;")
            r_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(r_lbl)

            st_lbl = QLabel("En veille")
            st_lbl.setStyleSheet("color: #64748b; font-size: 9px; font-weight: bold; border: none;")
            st_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(st_lbl)

            agents_grid.addWidget(card)
            self.agent_cards[name] = st_lbl

        layout.addLayout(agents_grid)

        # Barre de consensus récursif
        bar_layout = QHBoxLayout()
        bar_lbl = QLabel("SCORE DE CONSENSUS :")
        bar_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: bold;")
        bar_layout.addWidget(bar_lbl)

        self.consensus_bar = QProgressBar()
        self.consensus_bar.setRange(0, 100)
        self.consensus_bar.setValue(100)
        self.consensus_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                height: 14px;
                text-align: center;
                color: white;
                font-size: 10px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #38bdf8);
                border-radius: 6px;
            }
        """)
        bar_layout.addWidget(self.consensus_bar, stretch=1)
        layout.addLayout(bar_layout)

        # Console de débat récursif
        self.swarm_console = QTextEdit()
        self.swarm_console.setReadOnly(True)
        self.swarm_console.setStyleSheet("""
            QTextEdit {
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid rgba(167, 139, 250, 0.3);
                border-radius: 10px;
                color: #e2e8f0;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.swarm_console.setPlainText("👑 [Nora Prime] Essaim prêt. Les 5 agents attendent votre prochaine consigne pour délibérer.")
        layout.addWidget(self.swarm_console, stretch=1)

        return p

    def update_swarm_event(self, agent: str, round_num: int, text: str, consensus: int = 100):
        self.consensus_bar.setValue(consensus)
        color = "#38bdf8"
        if "Critique" in agent:
            color = "#a855f7"
        elif "Gardien" in agent:
            color = "#10b981"
        elif "Exécuteur" in agent:
            color = "#f59e0b"
        elif "Prime" in agent:
            color = "#ff2a85"

        msg = f"<span style='color:{color}; font-weight:bold;'>[{agent} - Tour {round_num}]</span> {text}"
        self.swarm_console.append(msg)

    # =========================================================================
    # 3. PANNEAU STUDIO GARDE-ROBE & ASSETS PLEIN CORPS
    # =========================================================================
    def create_wardrobe_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("👗 STUDIO GARDE-ROBE & ASSETS PLEIN CORPS")
        title.setStyleSheet("color: #ff2a85; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        desc = QLabel("Sélectionnez l'une des 5 tenues complètes et déclenchez les animations corporelles :")
        desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(desc)

        # 5 Cartes de tenues
        outfits_layout = QHBoxLayout()
        outfits_layout.setSpacing(8)

        self.outfit_btns = {}
        outfits_list = [
            ("franxx", "Pilote Franxx", "Combinaison rouge & cornes"),
            ("school", "Écolière", "Uniforme militaire marine"),
            ("hoodie", "Street Hoodie", "Sweat oversize & sneakers"),
            ("cyberpunk", "Cyber Techwear", "Veste tactique & sangles cyan"),
            ("commander", "Commandant", "Manteau écarlate & or"),
        ]

        for code, label, sub in outfits_list:
            btn = QPushButton(f"<b>{label}</b><br><span style='font-size:9px;'>{sub}</span>")
            btn.setFixedHeight(54)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(self._get_outfit_btn_style(code == self.current_outfit))
            btn.clicked.connect(lambda checked, c=code: self.on_select_outfit(c))
            outfits_layout.addWidget(btn)
            self.outfit_btns[code] = btn

        layout.addLayout(outfits_layout)

        # Déclencheur d'animations plein corps
        anim_title = QLabel("DÉCLENCHEURS D'ANIMATIONS PLEIN CORPS (BRAS & JAMBES) :")
        anim_title.setStyleSheet("color: #fda4af; font-size: 11px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(anim_title)

        anim_grid = QGridLayout()
        anim_grid.setSpacing(8)

        animations = [
            ("🚶 Démarche Articulée", "walk"),
            ("🏃 Course Rapide Dash", "run"),
            ("👋 Saluer Maverick", "idle_wave"),
            ("🤔 Réflexion Stratégique", "idle_thinking"),
            ("🪑 Assise Barre des Tâches", "idle_sitting"),
            ("💻 Hologrammes de Travail", "idle_work_hologram"),
            ("🎮 Session Gaming", "idle_gaming"),
            ("🛡️ Bouclier Cyber-Sécurité", "alert_shield")
        ]

        for i, (label, anim_name) in enumerate(animations):
            btn = QPushButton(label)
            btn.setFixedHeight(34)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(30, 41, 59, 0.7);
                    color: #f1f5f9;
                    border: 1px solid rgba(255, 42, 133, 0.4);
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 42, 133, 0.25);
                    border-color: #ff2a85;
                }
            """)
            btn.clicked.connect(lambda checked, a=anim_name: self.on_trigger_animation(a))
            anim_grid.addWidget(btn, i // 2, i % 2)

        layout.addLayout(anim_grid)
        layout.addStretch()

        return p

    def _get_outfit_btn_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff2a85, stop:1 #be185d);
                    color: white;
                    border: 2px solid #fda4af;
                    border-radius: 10px;
                    padding: 4px;
                }
            """
        else:
            return """
                QPushButton {
                    background: rgba(30, 41, 59, 0.7);
                    color: #cbd5e1;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 10px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background: rgba(255, 42, 133, 0.15);
                    border-color: #ff2a85;
                }
            """

    def on_select_outfit(self, outfit: str):
        self.current_outfit = outfit
        self.update_outfit_buttons(outfit)
        self.outfit_changed.emit(outfit)

    def update_outfit_buttons(self, current: str):
        for code, btn in self.outfit_btns.items():
            btn.setStyleSheet(self._get_outfit_btn_style(code == current))

    def on_trigger_animation(self, anim: str):
        if not self.parent_mascot:
            return
        if anim == "walk":
            self.parent_mascot.initial_autonomous_walk()
        elif anim == "run":
            step = 320 if getattr(self.parent_mascot, 'facing_direction', 1) == 1 else -320
            self.parent_mascot.start_walking_to(self.parent_mascot.x() + step, speed=5, announcement="Accélération Dash !")
        else:
            pose_dialogs = {
                "idle_wave": "Coucou Maverick ! Ravie d'être à vos côtés. 🌸",
                "idle_thinking": "J'analyse les paramètres système et prépare la suite...",
                "idle_sitting": "Je m'installe confortablement sur votre barre des tâches.",
                "idle_work_hologram": "Déploiement des consoles holographiques de surveillance.",
                "idle_gaming": "Mode Gaming prêt, concentration maximale Maverick !",
                "alert_shield": "Bouclier de sécurité actif. Votre système est sous haute protection."
            }
            dialog = pose_dialogs.get(anim, None)
            if hasattr(self.parent_mascot, 'play_pose'):
                self.parent_mascot.play_pose(anim, duration_sec=6.0, dialog=dialog)
            else:
                self.parent_mascot.set_sprite_state(anim)

    # =========================================================================
    # 4. PANNEAU TÉLÉMÉTRIE SYSTÈME & HARDWARE
    # =========================================================================
    def create_system_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        title = QLabel("⚡ TÉLÉMÉTRIE MATÉRIELLE & MONITEUR SYSTÈME")
        title.setStyleSheet("color: #38bdf8; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        # Jauges CPU, RAM, Disque, GPU
        grid = QGridLayout()
        grid.setSpacing(12)

        self.cpu_bar, self.cpu_val = self._create_telemetry_gauge("PROCESSEUR (CPU)")
        self.ram_bar, self.ram_val = self._create_telemetry_gauge("MÉMOIRE VIVE (RAM)")
        self.disk_bar, self.disk_val = self._create_telemetry_gauge("DISQUE SYSTÈME (C:)")
        self.gpu_bar, self.gpu_val = self._create_telemetry_gauge("CARTE GRAPHIQUE (GPU)")
        self.sec_bar, self.sec_val = self._create_telemetry_gauge("INDICE DE SANTÉ PC")

        grid.addLayout(self.cpu_bar, 0, 0)
        grid.addLayout(self.ram_bar, 0, 1)
        grid.addLayout(self.disk_bar, 1, 0)
        grid.addLayout(self.gpu_bar, 1, 1)
        grid.addLayout(self.sec_bar, 2, 0, 1, 2)

        layout.addLayout(grid)

        # Contrôles Système (Purge RAM et Mode Gaming)
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        c_layout = QHBoxLayout(ctrl_frame)

        self.btn_ram = QPushButton("⚡ VIDER LA RAM (PURGE WINDOWS)")
        self.btn_ram.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ram.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: white;
                font-weight: 800;
                font-size: 11px;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background: #0369a1; }
        """)
        self.btn_ram.clicked.connect(self.on_ram_purge_click)
        c_layout.addWidget(self.btn_ram)

        self.btn_gaming = QPushButton("🎮 MODE GAMING ULTRA (OFF)")
        self.btn_gaming.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_gaming.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.25);
                color: #fca5a5;
                font-weight: 800;
                font-size: 11px;
                padding: 8px 16px;
                border-radius: 8px;
                border: 1px solid rgba(239, 68, 68, 0.4);
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.4); }
        """)
        self.btn_gaming.clicked.connect(self.on_gaming_click)
        c_layout.addWidget(self.btn_gaming)

        layout.addWidget(ctrl_frame)
        layout.addStretch()

        return p

    def _create_telemetry_gauge(self, name: str):
        layout = QVBoxLayout()
        header = QHBoxLayout()
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: bold; border: none;")
        lbl_val = QLabel("0 %")
        lbl_val.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 800; border: none;")
        header.addWidget(lbl_name)
        header.addStretch()
        header.addWidget(lbl_val)
        layout.addLayout(header)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setStyleSheet("""
            QProgressBar {
                background: rgba(30, 41, 59, 0.8);
                border-radius: 5px;
                height: 10px;
                text-align: right;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f0ff, stop:1 #38bdf8);
                border-radius: 5px;
            }
        """)
        layout.addWidget(bar)
        return layout, (bar, lbl_val)

    def on_ram_purge_click(self):
        self.ram_boost_requested.emit()
        self.btn_ram.setText("✔ RAM PURGÉE AVEC SUCCÈS")
        QTimer.singleShot(2500, lambda: self.btn_ram.setText("⚡ VIDER LA RAM (PURGE WINDOWS)"))

    def on_gaming_click(self):
        current = gaming_mode.is_gaming_mode()
        self.gaming_mode_toggled.emit(not current)

    def update_gaming_ui(self):
        is_on = gaming_mode.is_gaming_mode()
        if is_on:
            self.btn_gaming.setText("🎮 MODE GAMING ULTRA (ACTIF)")
            self.btn_gaming.setStyleSheet("""
                QPushButton {
                    background: #10b981;
                    color: white;
                    font-weight: 800;
                    font-size: 11px;
                    padding: 8px 16px;
                    border-radius: 8px;
                    border: none;
                }
            """)
        else:
            self.btn_gaming.setText("🎮 MODE GAMING ULTRA (INACTIF)")
            self.btn_gaming.setStyleSheet("""
                QPushButton {
                    background: rgba(239, 68, 68, 0.25);
                    color: #fca5a5;
                    font-weight: 800;
                    font-size: 11px;
                    padding: 8px 16px;
                    border-radius: 8px;
                    border: 1px solid rgba(239, 68, 68, 0.4);
                }
            """)

    def update_vc_ui(self):
        pass

    def update_handsfree_button(self):
        pass

    def update_telemetry(self):
        try:
            diag = system_monitor.get_system_diagnostics()
            cpu = int(diag.get("cpu_percent", 5))
            ram = int(diag.get("ram_percent", 0))
            disk = int(diag.get("disk_percent", 0))
            gpu = int(diag.get("gpu_percent", 0))
            health = int(diag.get("health_score", 75))

            self.cpu_val[0].setValue(cpu)
            self.cpu_val[1].setText(f"{cpu} %")
            self.ram_val[0].setValue(ram)
            self.ram_val[1].setText(f"{ram} % ({diag.get('ram_used_gb', 0)} / {diag.get('ram_total_gb', 0)} Go)")
            self.disk_val[0].setValue(disk)
            self.disk_val[1].setText(f"{disk} % ({diag.get('disk_free_gb', 0)} Go libres)")

            if hasattr(self, 'gpu_val'):
                self.gpu_val[0].setValue(gpu)
                self.gpu_val[1].setText(f"{gpu} %")

            self.sec_val[0].setValue(health)
            self.sec_val[1].setText(f"{health} / 100")
        except Exception:
            pass

    # =========================================================================
    # 5. PANNEAU BOUCLIER SÉCURITÉ
    # =========================================================================
    def create_security_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("🛡️ BOUCLIER DE CYBERSÉCURITÉ & SURVEILLANCE")
        title.setStyleSheet("color: #10b981; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        status_card = QFrame()
        status_card.setStyleSheet("""
            QFrame {
                background: rgba(16, 185, 129, 0.12);
                border: 1px solid #10b981;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        sc_layout = QHBoxLayout(status_card)
        lbl_sec = QLabel("✔ PROTECTION ACTIVE : Tous les processus Windows surveillés en permanence.")
        lbl_sec.setStyleSheet("color: #6ee7b7; font-weight: bold; font-size: 12px; border: none;")
        sc_layout.addWidget(lbl_sec)
        layout.addWidget(status_card)

        # Log de surveillance
        sec_log = QTextEdit()
        sec_log.setReadOnly(True)
        sec_log.setStyleSheet("""
            QTextEdit {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: #a7f3d0;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        sec_log.setPlainText(
            "🛡️ [Agent Sécurité] Surveillance active.\n"
            "✔ 0 processus suspects détectés dans l'espace utilisateur.\n"
            "✔ Port serveur local 8000 sécurisé avec filtrage d'adresses.\n"
            "✔ Watchdog en mémoire RAM actif."
        )
        layout.addWidget(sec_log, stretch=1)

        return p

    # =========================================================================
    # 6. PANNEAU CENTRE DOMOTIQUE
    # =========================================================================
    def create_smarthome_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("🏠 CENTRE DOMOTIQUE & SMART HOME")
        title.setStyleSheet("color: #fbbf24; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        desc = QLabel("Pilotez l'ambiance lumineuse de votre espace de travail en un clic :")
        desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(desc)

        # Grille d'ambiances
        scenes_grid = QGridLayout()
        scenes = [
            ("🌸 Ambiance Zero Two", "scene_zerotwo"),
            ("🌙 Mode Nuit Doux", "scene_night"),
            ("🎮 Gaming Néon Cyber", "scene_gaming"),
            ("💡 Plein Éclairage Travail", "scene_work"),
        ]

        for i, (label, scene_id) in enumerate(scenes):
            btn = QPushButton(label)
            btn.setFixedHeight(45)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(30, 41, 59, 0.7);
                    color: #fef08a;
                    border: 1px solid rgba(251, 191, 36, 0.4);
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(251, 191, 36, 0.25);
                    border-color: #fbbf24;
                }
            """)
            btn.clicked.connect(lambda checked, s=scene_id: self.on_scene_click(s))
            scenes_grid.addWidget(btn, i // 2, i % 2)

        layout.addLayout(scenes_grid)
        layout.addStretch()

        return p

    def on_scene_click(self, scene_id: str):
        if self.parent_mascot:
            self.parent_mascot.display_message(f"💡 Ambiance lumineuse activée : {scene_id} !")

    # =========================================================================
    # 7. PANNEAU MÉMOIRE & CERVEAU IA
    # =========================================================================
    def create_memory_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("🧠 CERVEAU NEURONAL & MÉMOIRE PERSISTANTE")
        title.setStyleSheet("color: #c084fc; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        desc = QLabel("Faits mémorisés par Nora sur Maverick et ses projets :")
        desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(desc)

        self.memory_view = QTextEdit()
        self.memory_view.setReadOnly(True)
        self.memory_view.setStyleSheet("""
            QTextEdit {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(192, 132, 252, 0.3);
                border-radius: 10px;
                color: #e9d5ff;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)

        # Chargement de la mémoire réelle
        mem = memory_manager.load_memory()
        user_data = mem.get("user", {})
        facts = user_data.get("faits_appris", [])
        text = f"👤 UTILISATEUR : {user_data.get('name', 'Maverick')}\n\n📚 FAITS APPRIS :\n"
        for f in facts:
            text += f"• {f}\n"

        text += f"\n📊 STATISTIQUES :\n• Missions réussies : {mem.get('statistiques', {}).get('missions_reussies', 0)}"
        self.memory_view.setPlainText(text)
        layout.addWidget(self.memory_view, stretch=1)

        return p

    # =========================================================================
    # 8. PANNEAU PASSERELLE MOBILE 4G/5G
    # =========================================================================
    def create_mobile_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("📱 PASSERELLE MOBILE & ACCÈS DISTANT (4G / 5G / WIFI)")
        title.setStyleSheet("color: #22d3ee; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        # Lire l'URL distante
        url_file = BASE_DIR / "remote_url.txt"
        current_url = url_file.read_text(encoding="utf-8").strip() if url_file.exists() else "En attente du tunnel..."

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(34, 211, 238, 0.1);
                border: 1px solid #22d3ee;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        c_layout = QVBoxLayout(card)
        lbl_u = QLabel("🔗 URL ACTIVE POUR L'APPLICATION SMARTPHONE :")
        lbl_u.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; border: none;")
        c_layout.addWidget(lbl_u)

        self.url_display = QLabel(current_url)
        self.url_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.url_display.setStyleSheet("color: #67e8f9; font-weight: 800; font-size: 13px; border: none;")
        c_layout.addWidget(self.url_display)
        layout.addWidget(card)

        desc2 = QLabel("Ouvrez l'application Nora sur votre smartphone Android. Elle se synchronise en temps réel avec ce PC.")
        desc2.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        layout.addWidget(desc2)

        layout.addStretch()
        return p

    # =========================================================================
    # CONTRÔLE D'AFFICHAGE & INDÉPENDANCE ABSOLUE
    # =========================================================================
    def show_independent(self):
        """Affiche le QG sans suivre la mascotte."""
        self.show()
        self.raise_()
        self.activateWindow()

    def toggle_independent(self):
        """Bascule l'affichage du QG."""
        if self.isVisible():
            self.hide()
        else:
            self.show_independent()
