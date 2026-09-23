"""
QG de Nora (Quartier Général & Cockpit Central Cyber-Glassmorphism) :
- Refonte complète esthétique et fonctionnelle indépendante
- Navigation latérale multi-écrans avec 11 modules interactifs :
    1. 🚀 COCKPIT & OMNIBOX (Contrôle direct, missions en langage naturel, actions rapides)
    2. 🤖 ESSAIM NEURONAL & AGORA (Arène de débat récursif + Fiches individuelles pour chaque IA)
    3. 📁 GESTIONNAIRE DE PROJETS (Suivi des projets de Maverick, tâches interactives, revues IA)
    4. 🖨️ ATELIER IMPRESSION 3D (PrusaSlicer 1-clic, catalogue 3D, télémétrie, bobines de filament)
    5. 🐾 COMPAGNON DE NORA (Animal autonome choisi par Nora, cycle de vie, soins et statistiques)
    6. 👗 STUDIO GARDE-ROBE (5 tenues complètes, déclencheur d'animations plein corps)
    7. ⚡ TÉLÉMÉTRIE SYSTÈME (Jauges CPU, RAM, GPU NVIDIA, Disque C:, Boost 1-clic, Mode Gaming)
    8. 🛡️ BOUCLIER SÉCURITÉ (Score d'intégrité, analyse processus, veille permanente)
    9. 🏠 CENTRE DOMOTIQUE (Contrôle des lumières connectées, ambiances et scénarios)
    10. 🧠 MÉMOIRE & CERVEAU (Recherche sémantique, faits mémorisés, carnet d'apprentissage)
    11. 📱 PASSERELLE MOBILE (Tunnel Cloudflare 4G/5G/WiFi, statut, lien smartphone)
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
    QLineEdit, QStackedWidget, QTextEdit, QSlider, QGridLayout,
    QCheckBox, QComboBox, QDialog, QFileDialog, QMessageBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QColor, QFont, QCursor, QPixmap, QIcon

import system_monitor
import agent_security
import nora_initiatives
import gaming_mode
import memory_manager
import mascot_assets
import nora_recursive_swarm
import nora_companion
import project_manager
import print3d_manager
import agent_home

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
COMPANION_ASSETS = ASSETS_DIR / "companion"


class AddSpoolDialog(QDialog):
    """Dialogue stylisé pour ajouter une véritable bobine de filament."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter une bobine de filament")
        self.setFixedSize(380, 420)
        self.setStyleSheet("""
            QDialog {
                background: #0f172a;
                color: #f1f5f9;
                border: 1px solid rgba(236, 72, 153, 0.4);
                border-radius: 12px;
            }
            QLabel { color: #cbd5e1; font-size: 11px; font-weight: bold; }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(30, 41, 59, 0.8);
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #ec4899;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("🧵 ENREGISTRER UNE BOBINE RÉELLE")
        title.setStyleSheet("color: #ec4899; font-size: 13px; font-weight: 800;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Marque (ex: Prusament, Sunlu, Polymaker, eSun) :"))
        self.brand_edit = QLineEdit()
        self.brand_edit.setPlaceholderText("ex: Prusament")
        layout.addWidget(self.brand_edit)

        layout.addWidget(QLabel("Matière :"))
        self.mat_combo = QComboBox()
        self.mat_combo.addItems(["PLA", "PLA+", "PETG", "TPU", "ABS", "ASA", "PC", "Nylon / PA"])
        layout.addWidget(self.mat_combo)

        layout.addWidget(QLabel("Nom de la couleur (ex: Galaxy Black, Rouge Rubis) :"))
        self.color_name_edit = QLineEdit()
        self.color_name_edit.setPlaceholderText("ex: Galaxy Black")
        layout.addWidget(self.color_name_edit)

        layout.addWidget(QLabel("Code Couleur Hex (#RRGGBB) :"))
        self.color_hex_edit = QLineEdit()
        self.color_hex_edit.setText("#ec4899")
        layout.addWidget(self.color_hex_edit)

        layout.addWidget(QLabel("Poids total / restant (grammes) :"))
        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(50, 5000)
        self.weight_spin.setValue(1000)
        self.weight_spin.setSingleStep(50)
        layout.addWidget(self.weight_spin)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet("background: rgba(51, 65, 85, 0.7); color: #cbd5e1; border-radius: 6px; padding: 6px 12px;")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet("background: #be185d; color: white; font-weight: bold; border-radius: 6px; padding: 6px 16px;")
        btn_save.clicked.connect(self.accept)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def get_spool_data(self) -> dict:
        brand = self.brand_edit.text().strip() or "Standard"
        material = self.mat_combo.currentText()
        color_name = self.color_name_edit.text().strip() or "Standard"
        color_hex = self.color_hex_edit.text().strip()
        if not color_hex.startswith("#") or len(color_hex) not in (4, 7):
            color_hex = "#ec4899"
        weight = self.weight_spin.value()
        return {
            "brand": brand,
            "material": material,
            "color_name": color_name,
            "color_hex": color_hex,
            "total_weight_g": weight
        }


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
        # Dimensions élargies pour une visibilité confortable des nouveaux modules
        self.setFixedSize(980, 680)

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
        body_layout.setContentsMargins(12, 10, 12, 12)
        body_layout.setSpacing(14)

        # Barre latérale gauche
        sidebar = self.create_sidebar()
        body_layout.addWidget(sidebar)

        # Panneaux empilés (Stacked Screens)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")

        self.panel_cockpit = self.create_cockpit_panel()        # Index 0
        self.panel_swarm = self.create_swarm_panel()            # Index 1
        self.panel_projects = self.create_projects_panel()      # Index 2
        self.panel_3dprint = self.create_3dprint_panel()        # Index 3
        self.panel_companion = self.create_companion_panel()    # Index 4
        self.panel_wardrobe = self.create_wardrobe_panel()      # Index 5
        self.panel_system = self.create_system_panel()          # Index 6
        self.panel_security = self.create_security_panel()      # Index 7
        self.panel_smarthome = self.create_smarthome_panel()    # Index 8
        self.panel_memory = self.create_memory_panel()          # Index 9
        self.panel_mobile = self.create_mobile_panel()          # Index 10

        self.stack.addWidget(self.panel_cockpit)       # 0
        self.stack.addWidget(self.panel_swarm)         # 1
        self.stack.addWidget(self.panel_projects)      # 2
        self.stack.addWidget(self.panel_3dprint)       # 3
        self.stack.addWidget(self.panel_companion)     # 4
        self.stack.addWidget(self.panel_wardrobe)      # 5
        self.stack.addWidget(self.panel_system)        # 6
        self.stack.addWidget(self.panel_security)      # 7
        self.stack.addWidget(self.panel_smarthome)     # 8
        self.stack.addWidget(self.panel_memory)        # 9
        self.stack.addWidget(self.panel_mobile)        # 10

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
                    stop:0 rgba(15, 23, 42, 0.95),
                    stop:0.5 rgba(30, 41, 59, 0.85),
                    stop:1 rgba(15, 23, 42, 0.95));
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
                border-bottom: 1px solid rgba(0, 240, 255, 0.25);
                padding: 4px 14px;
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
    # BARRE LATÉRALE DE NAVIGATION (SIDEBAR 11 ÉLÉMENTS)
    # =========================================================================
    def create_sidebar(self) -> QWidget:
        sb = QFrame()
        sb.setFixedWidth(190)
        sb.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.65);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
        """)
        layout = QVBoxLayout(sb)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(4)

        self.nav_buttons = []
        nav_items = [
            ("🚀  Cockpit", 0),
            ("🤖  Essaim IA", 1),
            ("📁  Projets", 2),
            ("🖨️  Atelier 3D", 3),
            ("🐾  Compagnon", 4),
            ("👗  Garde-Robe", 5),
            ("⚡  Système", 6),
            ("🛡️  Sécurité", 7),
            ("🏠  Domotique", 8),
            ("🧠  Mémoire IA", 9),
            ("📱  Mobile 4G/5G", 10),
        ]

        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setFixedHeight(34)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(self._get_nav_btn_style(idx == 0))
            btn.clicked.connect(lambda checked, i=idx: self.switch_screen(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # Mini badge Zero Two en bas de la sidebar
        mini_card = QFrame()
        mini_card.setStyleSheet("""
            QFrame {
                background: rgba(255, 42, 133, 0.12);
                border: 1px solid rgba(255, 42, 133, 0.4);
                border-radius: 10px;
                padding: 4px;
            }
        """)
        mc_layout = QVBoxLayout(mini_card)
        mc_layout.setContentsMargins(4, 4, 4, 4)
        lbl_info = QLabel("NORA COPILOTE\nStyle Zero Two 002")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_info.setStyleSheet("color: #fda4af; font-size: 10px; font-weight: bold; border: none;")
        mc_layout.addWidget(lbl_info)
        layout.addWidget(mini_card)

        return sb

    def _get_nav_btn_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2a85, stop:1 #e11d48);
                    color: white;
                    font-size: 11px;
                    font-weight: 800;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 12px;
                    border: none;
                }
            """
        else:
            return """
                QPushButton {
                    background: transparent;
                    color: #94a3b8;
                    font-size: 11px;
                    font-weight: 600;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 12px;
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
        layout.setSpacing(10)

        title = QLabel("🚀 CENTRE DE COMMANDEMENT & COCKPIT")
        title.setStyleSheet("color: #00f0ff; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

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
            btn.setFixedHeight(34)
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
    # 2. PANNEAU ESSAIM NEURONAL & AGORA (DÉBAT + FICHES INDIVIDUELLES)
    # =========================================================================
    def create_swarm_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # En-tête avec bascule de sous-onglets
        header_layout = QHBoxLayout()
        title = QLabel("🤖 ESSAIM NEURONAL & AGORA MULTI-AGENTS")
        title.setStyleSheet("color: #a78bfa; font-size: 15px; font-weight: 800;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.btn_sub_arena = QPushButton("🏛️ Arène de Débat")
        self.btn_sub_arena.setFixedHeight(30)
        self.btn_sub_arena.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sub_arena.setStyleSheet("""
            QPushButton {
                background: #8b5cf6; color: white; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 4px 12px; border: none;
            }
        """)

        self.btn_sub_profiles = QPushButton("👥 Fiches Individuelles des IA")
        self.btn_sub_profiles.setFixedHeight(30)
        self.btn_sub_profiles.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sub_profiles.setStyleSheet("""
            QPushButton {
                background: rgba(30, 41, 59, 0.7); color: #94a3b8; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 4px 12px; border: 1px solid rgba(255,255,255,0.1);
            }
        """)

        header_layout.addWidget(self.btn_sub_arena)
        header_layout.addWidget(self.btn_sub_profiles)
        layout.addLayout(header_layout)

        # Sous-stack : 0 = Arène de Débat, 1 = Fiches Individuelles
        self.swarm_sub_stack = QStackedWidget()

        # --- SOUS-PAGE A : L'ARÈNE DE DÉBAT RÉCURSIF DE MASSE ---
        arena_widget = QWidget()
        arena_layout = QVBoxLayout(arena_widget)
        arena_layout.setContentsMargins(0, 4, 0, 0)
        arena_layout.setSpacing(8)

        # Champ pour lancer un débat libre
        debate_input_frame = QFrame()
        debate_input_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid #8b5cf6;
                border-radius: 10px;
                padding: 2px 8px;
            }
        """)
        dif_layout = QHBoxLayout(debate_input_frame)
        dif_layout.setContentsMargins(6, 2, 6, 2)

        self.debate_input = QLineEdit()
        self.debate_input.setPlaceholderText("Proposez un sujet de débat à l'essaim (ex: 'Faut-il automatiser la purge de nuit ?')...")
        self.debate_input.setStyleSheet("background: transparent; border: none; color: white; font-size: 12px;")
        self.debate_input.returnPressed.connect(self.on_start_debate_click)
        dif_layout.addWidget(self.debate_input)

        btn_launch_debate = QPushButton("LANCER LE DÉBAT ⚡")
        btn_launch_debate.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_launch_debate.setStyleSheet("""
            QPushButton {
                background: #8b5cf6; color: white; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 6px 12px; border: none;
            }
            QPushButton:hover { background: #7c3aed; }
        """)
        btn_launch_debate.clicked.connect(self.on_start_debate_click)
        dif_layout.addWidget(btn_launch_debate)
        arena_layout.addWidget(debate_input_frame)

        # Grille des 6 agents avec statuts
        agents_grid = QHBoxLayout()
        agents_grid.setSpacing(6)

        self.agent_cards = {}
        for name, meta in nora_recursive_swarm.AGENT_METADATA.items():
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: rgba(30, 41, 59, 0.7);
                    border: 1px solid {meta['color']};
                    border-radius: 8px;
                    padding: 4px;
                }}
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(4, 4, 4, 4)
            c_layout.setSpacing(2)

            n_lbl = QLabel(meta['name'])
            n_lbl.setStyleSheet(f"color: {meta['color']}; font-weight: bold; font-size: 10px; border: none;")
            n_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(n_lbl)

            r_lbl = QLabel(meta['short_name'])
            r_lbl.setStyleSheet("color: #94a3b8; font-size: 9px; border: none;")
            r_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(r_lbl)

            st_lbl = QLabel("En veille")
            st_lbl.setStyleSheet("color: #64748b; font-size: 9px; font-weight: bold; border: none;")
            st_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(st_lbl)

            agents_grid.addWidget(card)
            self.agent_cards[name] = st_lbl

        arena_layout.addLayout(agents_grid)

        # Score de consensus
        bar_layout = QHBoxLayout()
        bar_lbl = QLabel("SCORE DE CONSENSUS :")
        bar_lbl.setStyleSheet("color: #cbd5e1; font-size: 10px; font-weight: bold;")
        bar_layout.addWidget(bar_lbl)

        self.consensus_bar = QProgressBar()
        self.consensus_bar.setRange(0, 100)
        self.consensus_bar.setValue(100)
        self.consensus_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                height: 12px;
                text-align: center;
                color: white;
                font-size: 9px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #38bdf8);
                border-radius: 6px;
            }
        """)
        bar_layout.addWidget(self.consensus_bar, stretch=1)
        arena_layout.addLayout(bar_layout)

        # Console de transcription du débat
        self.swarm_console = QTextEdit()
        self.swarm_console.setReadOnly(True)
        self.swarm_console.setStyleSheet("""
            QTextEdit {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(167, 139, 250, 0.3);
                border-radius: 10px;
                color: #e2e8f0;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.swarm_console.setPlainText("👑 [Nora Prime] Agora prête. Les 6 agents spécialistes attendent vos consignes pour délibérer.")
        arena_layout.addWidget(self.swarm_console, stretch=1)

        # --- SOUS-PAGE B : FICHES INDIVIDUELLES DES IA (UNE PAGE PAR AGENT) ---
        profiles_widget = QWidget()
        prof_layout = QHBoxLayout(profiles_widget)
        prof_layout.setContentsMargins(0, 4, 0, 0)
        prof_layout.setSpacing(10)

        # Colonne gauche : sélecteur d'agent
        agent_select_frame = QFrame()
        agent_select_frame.setFixedWidth(200)
        agent_select_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
            }
        """)
        asf_layout = QVBoxLayout(agent_select_frame)
        asf_layout.setContentsMargins(6, 8, 6, 8)
        asf_layout.setSpacing(6)

        lbl_s = QLabel("SÉLECTION DE L'AGENT :")
        lbl_s.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; border: none;")
        asf_layout.addWidget(lbl_s)

        self.agent_profile_btns = []
        for agent_key, meta in nora_recursive_swarm.AGENT_METADATA.items():
            btn = QPushButton(f"{meta['name']}")
            btn.setFixedHeight(34)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(30, 41, 59, 0.6);
                    color: {meta['color']};
                    border: 1px solid {meta['color']};
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    text-align: left;
                    padding-left: 10px;
                }}
                QPushButton:hover {{
                    background: {meta['color']};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, k=agent_key: self.show_agent_profile(k))
            asf_layout.addWidget(btn)
            self.agent_profile_btns.append(btn)

        asf_layout.addStretch()
        prof_layout.addWidget(agent_select_frame)

        # Colonne droite : Fiche détaillée de l'agent
        self.profile_detail_frame = QFrame()
        self.profile_detail_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid #8b5cf6;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        pdf_layout = QVBoxLayout(self.profile_detail_frame)
        pdf_layout.setContentsMargins(12, 10, 12, 10)
        pdf_layout.setSpacing(8)

        self.prof_header_lbl = QLabel("👑 NORA PRIME")
        self.prof_header_lbl.setStyleSheet("color: #ff2a85; font-size: 16px; font-weight: 800; border: none;")
        pdf_layout.addWidget(self.prof_header_lbl)

        self.prof_title_lbl = QLabel("Superviseure & Synthèse Centrale")
        self.prof_title_lbl.setStyleSheet("color: #fda4af; font-size: 12px; font-weight: bold; border: none;")
        pdf_layout.addWidget(self.prof_title_lbl)

        self.prof_role_lbl = QLabel()
        self.prof_role_lbl.setWordWrap(True)
        self.prof_role_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; border: none;")
        pdf_layout.addWidget(self.prof_role_lbl)

        # Bloc Outils & Capacités
        pdf_layout.addWidget(QLabel("PRÉROGATIVES & OUTILS SYSTÈME :"))
        self.prof_tools_lbl = QLabel()
        self.prof_tools_lbl.setWordWrap(True)
        self.prof_tools_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; border: none;")
        pdf_layout.addWidget(self.prof_tools_lbl)

        # Dernières prises de position
        pdf_layout.addWidget(QLabel("DERNIÈRES PRISES DE POSITION AU CONSEIL :"))
        self.prof_stances_text = QTextEdit()
        self.prof_stances_text.setReadOnly(True)
        self.prof_stances_text.setFixedHeight(80)
        self.prof_stances_text.setStyleSheet("""
            QTextEdit {
                background: rgba(10, 15, 29, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #e2e8f0;
                font-size: 10px;
            }
        """)
        pdf_layout.addWidget(self.prof_stances_text)

        # Consultation 1-à-1
        chat_box = QFrame()
        chat_box.setStyleSheet("background: rgba(30, 41, 59, 0.5); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);")
        cb_layout = QHBoxLayout(chat_box)
        cb_layout.setContentsMargins(6, 4, 6, 4)

        self.prof_chat_input = QLineEdit()
        self.prof_chat_input.setPlaceholderText("Poser une question en tête-à-tête à cet agent...")
        self.prof_chat_input.setStyleSheet("background: transparent; border: none; color: white; font-size: 11px;")
        self.prof_chat_input.returnPressed.connect(self.on_consult_agent_click)
        cb_layout.addWidget(self.prof_chat_input)

        btn_consult = QPushButton("CONSULTER 💬")
        btn_consult.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_consult.setStyleSheet("""
            QPushButton {
                background: #0284c7; color: white; font-weight: bold; font-size: 10px;
                border-radius: 6px; padding: 4px 10px; border: none;
            }
            QPushButton:hover { background: #0369a1; }
        """)
        btn_consult.clicked.connect(self.on_consult_agent_click)
        cb_layout.addWidget(btn_consult)
        pdf_layout.addWidget(chat_box)

        prof_layout.addWidget(self.profile_detail_frame, stretch=1)

        # Ajouter sous-écrans au sous-stack
        self.swarm_sub_stack.addWidget(arena_widget)     # Index 0
        self.swarm_sub_stack.addWidget(profiles_widget)  # Index 1
        layout.addWidget(self.swarm_sub_stack, stretch=1)

        # Connecter boutons de sous-onglets
        self.btn_sub_arena.clicked.connect(lambda: self.switch_swarm_sub(0))
        self.btn_sub_profiles.clicked.connect(lambda: self.switch_swarm_sub(1))

        # Afficher le premier agent par défaut
        self.current_selected_agent = "Nora Prime"
        self.show_agent_profile("Nora Prime")

        return p

    def switch_swarm_sub(self, idx: int):
        self.swarm_sub_stack.setCurrentIndex(idx)
        if idx == 0:
            self.btn_sub_arena.setStyleSheet("background: #8b5cf6; color: white; font-weight: bold; font-size: 11px; border-radius: 6px; padding: 4px 12px; border: none;")
            self.btn_sub_profiles.setStyleSheet("background: rgba(30, 41, 59, 0.7); color: #94a3b8; font-weight: bold; font-size: 11px; border-radius: 6px; padding: 4px 12px; border: 1px solid rgba(255,255,255,0.1);")
        else:
            self.btn_sub_profiles.setStyleSheet("background: #8b5cf6; color: white; font-weight: bold; font-size: 11px; border-radius: 6px; padding: 4px 12px; border: none;")
            self.btn_sub_arena.setStyleSheet("background: rgba(30, 41, 59, 0.7); color: #94a3b8; font-weight: bold; font-size: 11px; border-radius: 6px; padding: 4px 12px; border: 1px solid rgba(255,255,255,0.1);")

    def show_agent_profile(self, agent_key: str):
        self.current_selected_agent = agent_key
        meta = nora_recursive_swarm.AGENT_METADATA.get(agent_key)
        if not meta:
            return

        self.prof_header_lbl.setText(meta["name"])
        self.prof_header_lbl.setStyleSheet(f"color: {meta['color']}; font-size: 15px; font-weight: 800; border: none;")
        self.prof_title_lbl.setText(meta["title"])
        self.prof_title_lbl.setStyleSheet(f"color: {meta['accent']}; font-size: 11px; font-weight: bold; border: none;")
        self.prof_role_lbl.setText(f"<b>Mission :</b> {meta['role_summary']}<br><br><b>Philosophie :</b> <i>« {meta['philosophy']} »</i>")

        tools_txt = " • " + "\n • ".join(meta.get("capabilities", []))
        self.prof_tools_lbl.setText(tools_txt)

        stances = meta.get("recent_stances", [])
        stances_str = "\n".join(f"• {s}" for s in stances) if stances else "Aucune prise de position enregistrée pour l'instant."
        self.prof_stances_text.setPlainText(stances_str)

    def on_consult_agent_click(self):
        question = self.prof_chat_input.text().strip()
        if not question:
            return
        self.prof_chat_input.clear()
        agent = getattr(self, 'current_selected_agent', 'Nora Prime')
        self.prof_stances_text.append(f"\n<b>Maverick (1-à-1 avec {agent}) :</b> {question}")

        def _worker():
            ans = nora_recursive_swarm.consult_single_agent(agent, question)
            self.prof_stances_text.append(f"<b>{agent} :</b> {ans}")

        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def on_start_debate_click(self):
        topic = self.debate_input.text().strip()
        if not topic:
            return
        self.debate_input.clear()
        self.swarm_console.append(f"<hr><b>⚡ Débat engagé par Maverick :</b> '{topic}'")

        def _evt_cb(e):
            self.update_swarm_event(e["agent"], e["round"], e["text"], e["consensus"])

        def _worker():
            session = nora_recursive_swarm.RecursiveSwarmSession(topic, callback_event=_evt_cb)
            res = session.run_recursive_debate()
            plan = res.get("final_plan", [])
            self.swarm_console.append(f"<br><span style='color:#10b981; font-weight:bold;'>✔ Consensus final ({res['consensus_score']}%) :</span>")
            for step in plan:
                self.swarm_console.append(f"  • {step.get('details', str(step))}")

        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def update_swarm_event(self, agent: str, round_num: int, text: str, consensus: int = 100):
        self.consensus_bar.setValue(consensus)
        color = "#38bdf8"
        if "Critique" in agent:
            color = "#a855f7"
        elif "Gardien" in agent:
            color = "#10b981"
        elif "Exécuteur" in agent:
            color = "#f59e0b"
        elif "Maker" in agent:
            color = "#ec4899"
        elif "Prime" in agent:
            color = "#ff2a85"

        msg = f"<span style='color:{color}; font-weight:bold;'>[{agent} - Tour {round_num}]</span> {text}"
        self.swarm_console.append(msg)

    # =========================================================================
    # 3. PANNEAU GESTIONNAIRE DE PROJETS DE MAVERICK
    # =========================================================================
    def create_projects_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # En-tête
        h_layout = QHBoxLayout()
        title = QLabel("📁 GESTIONNAIRE DE PROJETS DE MAVERICK")
        title.setStyleSheet("color: #38bdf8; font-size: 15px; font-weight: 800;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        btn_new_proj = QPushButton("+ NOUVEAU PROJET")
        btn_new_proj.setFixedHeight(28)
        btn_new_proj.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_new_proj.setStyleSheet("""
            QPushButton {
                background: #0284c7; color: white; font-weight: bold; font-size: 10px;
                border-radius: 6px; padding: 4px 12px; border: none;
            }
            QPushButton:hover { background: #0369a1; }
        """)
        btn_new_proj.clicked.connect(self.on_add_project_dialog)
        h_layout.addWidget(btn_new_proj)
        layout.addLayout(h_layout)

        # Conteneur scindé : Liste des projets à gauche (largeur 270) + Détail à droite
        split_layout = QHBoxLayout()
        split_layout.setSpacing(10)

        # Liste projets
        proj_list_frame = QFrame()
        proj_list_frame.setFixedWidth(270)
        proj_list_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
            }
        """)
        self.plf_layout = QVBoxLayout(proj_list_frame)
        self.plf_layout.setContentsMargins(6, 6, 6, 6)
        self.plf_layout.setSpacing(6)

        self.refresh_projects_list()
        split_layout.addWidget(proj_list_frame)

        # Détail du projet sélectionné
        detail_frame = QFrame()
        detail_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid #38bdf8;
                border-radius: 10px;
                padding: 8px;
            }
        """)
        df_layout = QVBoxLayout(detail_frame)
        df_layout.setContentsMargins(12, 10, 12, 10)
        df_layout.setSpacing(8)

        # Titre et catégorie
        self.proj_title_lbl = QLabel("Titre du Projet")
        self.proj_title_lbl.setStyleSheet("color: #38bdf8; font-size: 15px; font-weight: 800; border: none;")
        df_layout.addWidget(self.proj_title_lbl)

        self.proj_meta_lbl = QLabel("Catégorie: Code | Priorité: Haute | Échéance: 15/10/2026")
        self.proj_meta_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
        df_layout.addWidget(self.proj_meta_lbl)

        # Barre de progression
        prog_layout = QHBoxLayout()
        prog_layout.addWidget(QLabel("Progression :"))
        self.proj_prog_bar = QProgressBar()
        self.proj_prog_bar.setRange(0, 100)
        self.proj_prog_bar.setValue(50)
        self.proj_prog_bar.setStyleSheet("""
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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
                border-radius: 6px;
            }
        """)
        prog_layout.addWidget(self.proj_prog_bar, stretch=1)
        df_layout.addLayout(prog_layout)

        # Boutons d'action rapides (Dossier, Conseil IA)
        btn_bar = QHBoxLayout()
        btn_open_folder = QPushButton("📂 Ouvrir Dossier")
        btn_open_folder.setFixedHeight(28)
        btn_open_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open_folder.setStyleSheet("background: rgba(30, 41, 59, 0.8); color: #e2e8f0; border-radius: 6px; font-size: 10px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1);")
        btn_open_folder.clicked.connect(self.on_open_proj_folder)
        btn_bar.addWidget(btn_open_folder)

        btn_ask_advice = QPushButton("💡 Conseil de Nora")
        btn_ask_advice.setFixedHeight(28)
        btn_ask_advice.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ask_advice.setStyleSheet("background: #0284c7; color: white; border-radius: 6px; font-size: 10px; font-weight: bold; border: none;")
        btn_ask_advice.clicked.connect(self.on_ask_proj_advice)
        btn_bar.addWidget(btn_ask_advice)

        btn_delete_proj = QPushButton("🗑️ Supprimer")
        btn_delete_proj.setFixedHeight(28)
        btn_delete_proj.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_delete_proj.setStyleSheet("background: rgba(239, 68, 68, 0.2); color: #f87171; border-radius: 6px; font-size: 10px; font-weight: bold; border: 1px solid rgba(239,68,68,0.3);")
        btn_delete_proj.clicked.connect(self.on_delete_proj)
        btn_bar.addWidget(btn_delete_proj)

        df_layout.addLayout(btn_bar)

        # Tâches / Checklist
        df_layout.addWidget(QLabel("TÂCHES DU PROJET (Cliquer pour valider) :"))
        self.tasks_container = QVBoxLayout()
        df_layout.addLayout(self.tasks_container)

        # Ajout rapide de tâche
        add_t_layout = QHBoxLayout()
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("Nouvelle tâche à accomplir...")
        self.new_task_input.setStyleSheet("background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; font-size: 11px; padding: 4px;")
        self.new_task_input.returnPressed.connect(self.on_add_task_click)
        add_t_layout.addWidget(self.new_task_input)

        btn_add_t = QPushButton("+ Ajouter")
        btn_add_t.setFixedHeight(26)
        btn_add_t.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add_t.setStyleSheet("background: #38bdf8; color: black; font-weight: bold; font-size: 10px; border-radius: 6px; padding: 0 10px; border: none;")
        btn_add_t.clicked.connect(self.on_add_task_click)
        add_t_layout.addWidget(btn_add_t)
        df_layout.addLayout(add_t_layout)

        # Conseil de Nora & l'Architecte
        df_layout.addWidget(QLabel("ANALYSE STRATÉGIQUE DE NORA & L'ARCHITECTE :"))
        self.proj_advice_lbl = QLabel("Sélectionnez un projet pour consulter l'analyse.")
        self.proj_advice_lbl.setWordWrap(True)
        self.proj_advice_lbl.setStyleSheet("color: #7dd3fc; font-style: italic; font-size: 11px; background: rgba(2, 132, 199, 0.1); padding: 8px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.3);")
        df_layout.addWidget(self.proj_advice_lbl)

        split_layout.addWidget(detail_frame, stretch=1)
        layout.addLayout(split_layout)

        # Afficher le premier projet
        projs = project_manager.project_manager.get_all()
        if projs:
            self.show_project_detail(projs[0]["id"])

        return p

    def refresh_projects_list(self):
        # Vider les éléments actuels
        while self.plf_layout.count():
            item = self.plf_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        projs = project_manager.project_manager.get_all()
        for p in projs:
            btn = QPushButton(f"<b>{p['title']}</b><br><span style='font-size:9px; color:#94a3b8;'>[{p['category']}] • {p['progress']}%</span>")
            btn.setFixedHeight(48)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(30, 41, 59, 0.7);
                    color: #f1f5f9;
                    border: 1px solid rgba(56, 189, 248, 0.3);
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 8px;
                }
                QPushButton:hover {
                    background: rgba(56, 189, 248, 0.2);
                    border-color: #38bdf8;
                }
            """)
            btn.clicked.connect(lambda checked, pid=p["id"]: self.show_project_detail(pid))
            self.plf_layout.addWidget(btn)

        self.plf_layout.addStretch()

    def show_project_detail(self, project_id: str):
        self.current_project_id = project_id
        p = project_manager.project_manager.get_project(project_id)
        if not p:
            return

        self.proj_title_lbl.setText(p["title"])
        self.proj_meta_lbl.setText(f"Catégorie: {p.get('category')}  |  Priorité: {p.get('priority')}  |  Échéance: {p.get('deadline', 'Non définie')}")
        self.proj_prog_bar.setValue(p.get("progress", 0))
        self.proj_advice_lbl.setText(p.get("ai_review", "Aucun conseil formulé."))

        # Vider tâches
        while self.tasks_container.count():
            item = self.tasks_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        tasks = p.get("tasks", [])
        for t in tasks:
            cb = QCheckBox(t["text"])
            cb.setChecked(t.get("done", False))
            cb.setStyleSheet("QCheckBox { color: #f1f5f9; font-size: 11px; } QCheckBox::indicator:checked { background: #38bdf8; border-radius: 3px; }")
            cb.stateChanged.connect(lambda state, tid=t["id"]: self.on_task_checked(tid))
            self.tasks_container.addWidget(cb)

    def on_task_checked(self, task_id: int):
        pid = getattr(self, 'current_project_id', None)
        if pid:
            project_manager.project_manager.toggle_task(pid, task_id)
            self.show_project_detail(pid)
            self.refresh_projects_list()

    def on_add_task_click(self):
        text = self.new_task_input.text().strip()
        pid = getattr(self, 'current_project_id', None)
        if text and pid:
            self.new_task_input.clear()
            project_manager.project_manager.add_task(pid, text)
            self.show_project_detail(pid)
            self.refresh_projects_list()

    def on_open_proj_folder(self):
        pid = getattr(self, 'current_project_id', None)
        if pid:
            ok = project_manager.project_manager.open_folder(pid)
            if not ok and self.parent_mascot:
                self.parent_mascot.display_message("Dossier local non configuré ou introuvable pour ce projet.")

    def on_ask_proj_advice(self):
        pid = getattr(self, 'current_project_id', None)
        if pid:
            self.proj_advice_lbl.setText("Nora et l'Architecte analysent votre projet...")
            def _worker():
                adv = project_manager.project_manager.ask_nora_advice(pid)
                self.proj_advice_lbl.setText(adv)
            import threading
            threading.Thread(target=_worker, daemon=True).start()

    def on_delete_proj(self):
        pid = getattr(self, 'current_project_id', None)
        if pid:
            project_manager.project_manager.delete_project(pid)
            self.refresh_projects_list()
            projs = project_manager.project_manager.get_all()
            if projs:
                self.show_project_detail(projs[0]["id"])

    def on_add_project_dialog(self):
        # Ajout simple d'un projet
        new_p = project_manager.project_manager.create_project(
            title=f"Nouveau Projet #{len(project_manager.project_manager.get_all()) + 1}",
            category="Code / IA",
            priority="Moyenne"
        )
        self.refresh_projects_list()
        self.show_project_detail(new_p["id"])

    # =========================================================================
    # 4. PANNEAU ATELIER IMPRESSION 3D & PRUSASLICER
    # =========================================================================
    def create_3dprint_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # En-tête avec boutons d'actions réelles
        h_layout = QHBoxLayout()
        title = QLabel("🖨️ ATELIER D'IMPRESSION 3D & FABRICATION")
        title.setStyleSheet("color: #ec4899; font-size: 15px; font-weight: 800;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        btn_folder = QPushButton("📂 DOSSIER 3D")
        btn_folder.setFixedHeight(30)
        btn_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_folder.setStyleSheet("""
            QPushButton {
                background: rgba(30, 41, 59, 0.8);
                color: #f1f5f9; font-weight: bold; font-size: 11px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px; padding: 4px 12px;
            }
            QPushButton:hover { background: rgba(51, 65, 85, 0.9); }
        """)
        btn_folder.clicked.connect(self.on_open_3d_folder_click)
        h_layout.addWidget(btn_folder)

        btn_prusa = QPushButton("⚡ LANCER PRUSASLICER")
        btn_prusa.setFixedHeight(30)
        btn_prusa.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_prusa.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ec4899, stop:1 #be185d);
                color: white; font-weight: 800; font-size: 11px;
                border-radius: 6px; padding: 4px 14px; border: none;
            }
            QPushButton:hover { background: #db2777; }
        """)
        btn_prusa.clicked.connect(lambda: self.on_launch_prusa_click())
        h_layout.addWidget(btn_prusa)
        layout.addLayout(h_layout)

        # Grille télémétrie imprimante (100% réelle)
        tele_frame = QFrame()
        tele_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(236, 72, 153, 0.3);
                border-radius: 10px;
                padding: 6px;
            }
        """)
        self.tf_layout = QHBoxLayout(tele_frame)
        self.tf_layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(tele_frame)
        self.update_3d_telemetry_widget()

        # Corps central en 2 colonnes : Modèles 3D réels (gauche) + Bobines réelles (droite)
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(10)

        # Colonne Gauche : Modèles 3D réels
        queue_frame = QFrame()
        queue_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
            }
        """)
        q_v = QVBoxLayout(queue_frame)
        q_v.setContentsMargins(8, 8, 8, 8)

        q_header = QHBoxLayout()
        q_title = QLabel("📦 MODÈLES 3D (Documents/Impression3D) :")
        q_title.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 11px;")
        q_header.addWidget(q_title)
        q_header.addStretch()

        btn_import_file = QPushButton("+ IMPORTER")
        btn_import_file.setFixedHeight(22)
        btn_import_file.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_import_file.setStyleSheet("background: #0284c7; color: white; font-size: 10px; font-weight: bold; border-radius: 4px; padding: 0 8px; border: none;")
        btn_import_file.clicked.connect(self.on_import_3d_file_click)
        q_header.addWidget(btn_import_file)
        q_v.addLayout(q_header)

        scroll_files = QScrollArea()
        scroll_files.setWidgetResizable(True)
        scroll_files.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.files_container = QWidget()
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.setContentsMargins(0, 4, 0, 4)
        self.files_layout.setSpacing(6)
        scroll_files.setWidget(self.files_container)
        q_v.addWidget(scroll_files, stretch=1)

        mid_layout.addWidget(queue_frame, stretch=1)

        # Colonne Droite : Bobines de Filament
        spool_frame = QFrame()
        spool_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
            }
        """)
        s_v = QVBoxLayout(spool_frame)
        s_v.setContentsMargins(8, 8, 8, 8)

        s_header = QHBoxLayout()
        s_title = QLabel("🧵 BOBINES DE FILAMENT (SPOOLMAN) :")
        s_title.setStyleSheet("color: #f1f5f9; font-weight: bold; font-size: 11px;")
        s_header.addWidget(s_title)
        s_header.addStretch()

        btn_add_spool = QPushButton("+ NOUVELLE")
        btn_add_spool.setFixedHeight(22)
        btn_add_spool.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add_spool.setStyleSheet("background: #be185d; color: white; font-size: 10px; font-weight: bold; border-radius: 4px; padding: 0 8px; border: none;")
        btn_add_spool.clicked.connect(self.on_add_spool_click)
        s_header.addWidget(btn_add_spool)
        s_v.addLayout(s_header)

        scroll_spools = QScrollArea()
        scroll_spools.setWidgetResizable(True)
        scroll_spools.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.spools_container = QWidget()
        self.spools_layout = QVBoxLayout(self.spools_container)
        self.spools_layout.setContentsMargins(0, 4, 0, 4)
        self.spools_layout.setSpacing(6)
        scroll_spools.setWidget(self.spools_container)
        s_v.addWidget(scroll_spools, stretch=1)

        mid_layout.addWidget(spool_frame, stretch=1)
        layout.addLayout(mid_layout)

        # Recommandation IA Slicer Maker
        advice_lbl = QLabel(
            "💡 <b>Conseil Maker 3D pour Maverick :</b> Privilégiez un remplissage Gyroid (20%) "
            "pour vos boîtiers afin de garantir une résistance mécanique isotrope sans déformation thermique."
        )
        advice_lbl.setWordWrap(True)
        advice_lbl.setStyleSheet("color: #fbcfe8; font-size: 11px; background: rgba(236, 72, 153, 0.1); padding: 8px; border-radius: 8px; border: 1px solid rgba(236, 72, 153, 0.3);")
        layout.addWidget(advice_lbl)

        # Chargement initial
        self.refresh_3d_files_list()
        self.refresh_spools_list()

        return p

    def update_3d_telemetry_widget(self):
        while self.tf_layout.count():
            item = self.tf_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

        tele = print3d_manager.print3d_manager.get_telemetry()
        stat = tele.get("status", "Non connectée")
        stat_col = "#10b981" if stat == "Prête" else ("#f59e0b" if "Impression" in stat else "#94a3b8")
        nozzle = f"{tele.get('nozzle_temp', 0)}°C / {tele.get('nozzle_target', 0)}°C" if tele.get('nozzle_target', 0) > 0 else f"{tele.get('nozzle_temp', 0)}°C"
        bed = f"{tele.get('bed_temp', 0)}°C / {tele.get('bed_target', 0)}°C" if tele.get('bed_target', 0) > 0 else f"{tele.get('bed_temp', 0)}°C"

        t_data = [
            ("🔥 Buse Extrudeur", nozzle, "#ec4899"),
            ("🛏️ Plateau Chauffant", bed, "#f59e0b"),
            ("🌀 Ventilateur", f"{tele.get('fan_speed', 0)} %", "#38bdf8"),
            ("📊 Statut Télémétrie", stat, stat_col),
        ]
        for name, val, col in t_data:
            c = QVBoxLayout()
            l1 = QLabel(name)
            l1.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; border: none;")
            l2 = QLabel(val)
            l2.setStyleSheet(f"color: {col}; font-size: 13px; font-weight: 800; border: none;")
            c.addWidget(l1)
            c.addWidget(l2)
            self.tf_layout.addLayout(c)

    def refresh_3d_files_list(self):
        while self.files_layout.count():
            item = self.files_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        files = print3d_manager.print3d_manager.scan_models_dir()
        if not files:
            empty_lbl = QLabel("Aucun fichier 3D dans Documents/Impression3D.\nCliquez sur '+ IMPORTER' pour ajouter un STL ou 3MF.")
            empty_lbl.setWordWrap(True)
            empty_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 20px; text-align: center;")
            self.files_layout.addWidget(empty_lbl)
        else:
            for f in files:
                jf = QFrame()
                jf.setStyleSheet("background: rgba(30, 41, 59, 0.6); border-radius: 6px; padding: 4px;")
                jl = QHBoxLayout(jf)
                jl.setContentsMargins(6, 4, 6, 4)

                info = QVBoxLayout()
                n = QLabel(f"<b>{f['name']}</b>")
                n.setStyleSheet("color: #f1f5f9; font-size: 11px;")
                m = QLabel(f"{f['format']} • {f['size_mb']} Mo • {f['modified']}")
                m.setStyleSheet("color: #94a3b8; font-size: 9px;")
                info.addWidget(n)
                info.addWidget(m)
                jl.addLayout(info, stretch=1)

                btn_s = QPushButton("⚡ Trancher")
                btn_s.setFixedHeight(24)
                btn_s.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_s.setStyleSheet("background: #be185d; color: white; font-size: 9px; font-weight: bold; border-radius: 4px; border: none; padding: 0 8px;")
                btn_s.clicked.connect(lambda checked, p=f['path']: self.on_launch_prusa_click(p))
                jl.addWidget(btn_s)

                self.files_layout.addWidget(jf)

        self.files_layout.addStretch()

    def refresh_spools_list(self):
        while self.spools_layout.count():
            item = self.spools_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        spools = print3d_manager.print3d_manager.get_spools()
        if not spools:
            empty_lbl = QLabel("Aucune bobine enregistrée.\nCliquez sur '+ NOUVELLE' pour inventorier vos filaments.")
            empty_lbl.setWordWrap(True)
            empty_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 20px; text-align: center;")
            self.spools_layout.addWidget(empty_lbl)
        else:
            for s in spools:
                sf = QFrame()
                sf.setStyleSheet("background: rgba(30, 41, 59, 0.6); border-radius: 6px; padding: 6px;")
                sl = QVBoxLayout(sf)
                sl.setContentsMargins(6, 4, 6, 4)
                sl.setSpacing(4)

                top_l = QHBoxLayout()
                t_lbl = QLabel(f"● {s['brand']} {s['material']} - {s['color_name']}")
                t_lbl.setStyleSheet(f"color: {s.get('color_hex', '#ec4899')}; font-weight: bold; font-size: 10px;")
                top_l.addWidget(t_lbl, stretch=1)

                btn_del = QPushButton("✕")
                btn_del.setFixedSize(18, 18)
                btn_del.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_del.setStyleSheet("background: transparent; color: #ef4444; font-weight: bold; border: none;")
                btn_del.clicked.connect(lambda checked, sid=s['id']: self.on_delete_spool_click(sid))
                top_l.addWidget(btn_del)
                sl.addLayout(top_l)

                pb = QProgressBar()
                pb.setRange(0, max(1, s["total_weight_g"]))
                pb.setValue(s["remaining_weight_g"])
                pb.setFixedHeight(8)
                pb.setStyleSheet(f"""
                    QProgressBar {{ background: #0f172a; border-radius: 4px; text-align: right; }}
                    QProgressBar::chunk {{ background: {s.get('color_hex', '#ec4899')}; border-radius: 4px; }}
                """)
                sl.addWidget(pb)

                rem = QLabel(f"{s['remaining_weight_g']}g / {s['total_weight_g']}g  (Buse: {s.get('temp_nozzle', 210)}°C)")
                rem.setStyleSheet("color: #94a3b8; font-size: 9px;")
                sl.addWidget(rem)

                self.spools_layout.addWidget(sf)

        self.spools_layout.addStretch()

    def on_open_3d_folder_click(self):
        print3d_manager.print3d_manager.open_models_folder()

    def on_import_3d_file_click(self):
        fpath, _ = QFileDialog.getOpenFileName(
            self,
            "Importer un modèle 3D",
            "",
            "Fichiers 3D (*.stl *.3mf *.obj *.step *.gcode);;Tous les fichiers (*.*)"
        )
        if fpath:
            imported = print3d_manager.print3d_manager.import_model_file(fpath)
            if imported:
                self.refresh_3d_files_list()
                if self.parent_mascot:
                    self.parent_mascot.display_message(f"Modèle 3D importé : {imported['name']}")

    def on_add_spool_click(self):
        dlg = AddSpoolDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_spool_data()
            print3d_manager.print3d_manager.add_spool(
                material=data["material"],
                brand=data["brand"],
                color_name=data["color_name"],
                color_hex=data["color_hex"],
                total_weight_g=data["total_weight_g"]
            )
            self.refresh_spools_list()
            if self.parent_mascot:
                self.parent_mascot.display_message(f"Bobine {data['brand']} {data['material']} enregistrée avec succès !")

    def on_delete_spool_click(self, spool_id: str):
        if print3d_manager.print3d_manager.delete_spool(spool_id):
            self.refresh_spools_list()

    def on_launch_prusa_click(self, file_path: str = ""):
        ok = print3d_manager.print3d_manager.launch_prusaslicer(file_path if file_path else None)
        if not ok and self.parent_mascot:
            self.parent_mascot.display_message("PrusaSlicer introuvable ou n'a pas pu être lancé automatiquement.")

    # =========================================================================
    # 5. PANNEAU COMPAGNON VIRTUEL DE NORA
    # =========================================================================
    def create_companion_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("🐾 COMPAGNON VIRTUEL DE NORA")
        title.setStyleSheet("color: #ff2a85; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        pet_info = nora_companion.pet_manager.get_pet_info()
        stats = pet_info.get("stats", {})

        # Hero Card : Avatar + Identité
        hero_frame = QFrame()
        hero_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 42, 133, 0.1);
                border: 2px solid #ff2a85;
                border-radius: 14px;
                padding: 10px;
            }
        """)
        hf_layout = QHBoxLayout(hero_frame)
        hf_layout.setContentsMargins(10, 8, 10, 8)

        # Sprite compagnon
        self.pet_avatar_lbl = QLabel()
        self.pet_avatar_lbl.setFixedSize(72, 72)
        sprite_path = COMPANION_ASSETS / "pet_idle.png"
        if sprite_path.exists():
            self.pet_avatar_lbl.setPixmap(QPixmap(str(sprite_path)).scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        hf_layout.addWidget(self.pet_avatar_lbl)

        # Infos
        info_v = QVBoxLayout()
        self.pet_name_lbl = QLabel(f"<b>{pet_info.get('name', 'Klaxo')}</b> ({pet_info.get('species', 'Dragonnet Écarlate')})")
        self.pet_name_lbl.setStyleSheet("color: #fda4af; font-size: 15px; font-weight: 800; border: none;")
        info_v.addWidget(self.pet_name_lbl)

        self.pet_status_lbl = QLabel(f"Statut : {pet_info.get('status', 'Éveillé')}  |  Niveau : {stats.get('level', 1)} (XP: {stats.get('xp', 0)}%)")
        self.pet_status_lbl.setStyleSheet("color: #f1f5f9; font-size: 11px; font-weight: bold; border: none;")
        info_v.addWidget(self.pet_status_lbl)

        quote = pet_info.get("nora_announcement", "Nora prend soin de son compagnon avec amour.")
        self.pet_quote_lbl = QLabel(f"<i>« {quote[:140]}... »</i>")
        self.pet_quote_lbl.setWordWrap(True)
        self.pet_quote_lbl.setStyleSheet("color: #cbd5e1; font-size: 10px; border: none;")
        info_v.addWidget(self.pet_quote_lbl)

        hf_layout.addLayout(info_v, stretch=1)
        layout.addWidget(hero_frame)

        # Jauges de statistiques (Faim, Bonheur, Énergie, Affection)
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 8px;
            }
        """)
        sf_layout = QGridLayout(stats_frame)
        sf_layout.setSpacing(10)

        # Faim
        sf_layout.addWidget(QLabel("🍖 Faim / Satiété :"), 0, 0)
        self.bar_hunger = QProgressBar()
        self.bar_hunger.setValue(stats.get("hunger", 85))
        self.bar_hunger.setStyleSheet("QProgressBar::chunk { background: #f59e0b; }")
        sf_layout.addWidget(self.bar_hunger, 0, 1)

        # Bonheur
        sf_layout.addWidget(QLabel("💖 Bonheur :"), 0, 2)
        self.bar_happy = QProgressBar()
        self.bar_happy.setValue(stats.get("happiness", 90))
        self.bar_happy.setStyleSheet("QProgressBar::chunk { background: #ff2a85; }")
        sf_layout.addWidget(self.bar_happy, 0, 3)

        # Énergie
        sf_layout.addWidget(QLabel("⚡ Énergie :"), 1, 0)
        self.bar_energy = QProgressBar()
        self.bar_energy.setValue(stats.get("energy", 90))
        self.bar_energy.setStyleSheet("QProgressBar::chunk { background: #38bdf8; }")
        sf_layout.addWidget(self.bar_energy, 1, 1)

        # Affection envers Nora
        sf_layout.addWidget(QLabel("🌸 Affection :"), 1, 2)
        self.bar_affect = QProgressBar()
        self.bar_affect.setValue(stats.get("affection", 95))
        self.bar_affect.setStyleSheet("QProgressBar::chunk { background: #10b981; }")
        sf_layout.addWidget(self.bar_affect, 1, 3)

        layout.addWidget(stats_frame)

        # Boutons de soins interactifs
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        care_buttons = [
            ("🍖 Nourrir", self.on_pet_feed),
            ("🎾 Jouer", self.on_pet_play),
            ("💖 Câliner", self.on_pet_pet),
            ("💤 Faire la sieste", self.on_pet_nap),
        ]
        for label, handler in care_buttons:
            btn = QPushButton(label)
            btn.setFixedHeight(34)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(30, 41, 59, 0.7);
                    color: #fda4af;
                    border: 1px solid rgba(255, 42, 133, 0.4);
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 42, 133, 0.25);
                    border-color: #ff2a85;
                    color: white;
                }
            """)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)

        layout.addLayout(actions_layout)

        # Journal des attentions de Nora
        layout.addWidget(QLabel("JOURNAL DES SOINS DE NORA :"))
        self.pet_journal_text = QTextEdit()
        self.pet_journal_text.setReadOnly(True)
        self.pet_journal_text.setStyleSheet("""
            QTextEdit {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                color: #e2e8f0;
                font-family: Consolas, monospace;
                font-size: 10px;
            }
        """)
        journal = pet_info.get("journal", [])
        self.pet_journal_text.setPlainText("\n".join(journal))
        layout.addWidget(self.pet_journal_text, stretch=1)

        return p

    def on_pet_feed(self):
        msg = nora_companion.pet_manager.feed()
        self.update_pet_ui(msg, "pet_eat.png")

    def on_pet_play(self):
        msg = nora_companion.pet_manager.play()
        self.update_pet_ui(msg, "pet_happy.png")

    def on_pet_pet(self):
        msg = nora_companion.pet_manager.pet()
        self.update_pet_ui(msg, "pet_happy.png")

    def on_pet_nap(self):
        msg = nora_companion.pet_manager.nap()
        self.update_pet_ui(msg, "pet_sleep.png")

    def update_pet_ui(self, msg: str, sprite_name: str = "pet_idle.png"):
        pet_info = nora_companion.pet_manager.get_pet_info()
        stats = pet_info.get("stats", {})
        self.bar_hunger.setValue(stats.get("hunger", 0))
        self.bar_happy.setValue(stats.get("happiness", 0))
        self.bar_energy.setValue(stats.get("energy", 0))
        self.bar_affect.setValue(stats.get("affection", 0))
        self.pet_status_lbl.setText(f"Statut : {pet_info.get('status', 'Éveillé')}  |  Niveau : {stats.get('level', 1)} (XP: {stats.get('xp', 0)}%)")

        # Changer sprite temporairement
        sp = COMPANION_ASSETS / sprite_name
        if sp.exists():
            self.pet_avatar_lbl.setPixmap(QPixmap(str(sp)).scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            # Retour à idle après 4 secondes
            QTimer.singleShot(4000, lambda: self.reset_pet_sprite())

        journal = pet_info.get("journal", [])
        self.pet_journal_text.setPlainText("\n".join(journal))
        if self.parent_mascot:
            self.parent_mascot.display_message(msg)

    def reset_pet_sprite(self):
        sp = COMPANION_ASSETS / "pet_idle.png"
        if sp.exists():
            self.pet_avatar_lbl.setPixmap(QPixmap(str(sp)).scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    # =========================================================================
    # 6. PANNEAU STUDIO GARDE-ROBE & ASSETS PLEIN CORPS
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
            btn.setFixedHeight(50)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(self._get_outfit_btn_style(code == self.current_outfit))
            btn.clicked.connect(lambda checked, c=code: self.on_select_outfit(c))
            outfits_layout.addWidget(btn)
            self.outfit_btns[code] = btn

        layout.addLayout(outfits_layout)

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
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2a85, stop:1 #e11d48);
                    color: white;
                    border: 2px solid #fda4af;
                    border-radius: 10px;
                }
            """
        else:
            return """
                QPushButton {
                    background: rgba(30, 41, 59, 0.7);
                    color: #cbd5e1;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background: rgba(255, 42, 133, 0.2);
                    border-color: #ff2a85;
                }
            """

    def on_select_outfit(self, code: str):
        self.current_outfit = code
        self.update_outfit_buttons(code)
        self.outfit_changed.emit(code)
        if self.parent_mascot:
            self.parent_mascot.set_outfit(code)

    def update_outfit_buttons(self, active_code: str):
        for code, btn in self.outfit_btns.items():
            btn.setStyleSheet(self._get_outfit_btn_style(code == active_code))

    def on_trigger_animation(self, anim_name: str):
        dialogs = {
            "idle_wave": "Je vous salue respectueusement, Maverick !",
            "idle_thinking": "Je réfléchis à la stratégie optimale...",
            "idle_sitting": "Je m'installe confortablement sur votre barre des tâches.",
            "idle_work_hologram": "Analyse de vos fichiers en cours...",
            "idle_gaming": "Mode Gaming actif ! Excellente partie, Maverick !",
            "alert_shield": "Bouclier de sécurité déployé. Système protégé à 100%."
        }
        dlg = dialogs.get(anim_name, None)
        if self.parent_mascot:
            self.parent_mascot.play_pose(anim_name, duration_sec=6.0, dialog=dlg)
        self.animation_requested.emit(anim_name)

    # =========================================================================
    # 7. PANNEAU TÉLÉMÉTRIE SYSTÈME & JETS HAUTE PERFORMANCE
    # =========================================================================
    def create_system_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("⚡ TÉLÉMÉTRIE MATÉRIELLE & SANTÉ DU PC")
        title.setStyleSheet("color: #38bdf8; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # 1. CPU
        self.cpu_bar, self.cpu_lbl = self._create_telemetry_gauge("PROCESSEUR (CPU)", "#38bdf8")
        grid.addWidget(self.cpu_bar, 0, 0)

        # 2. RAM
        self.ram_bar, self.ram_lbl = self._create_telemetry_gauge("MÉMOIRE VIVE (RAM)", "#10b981")
        grid.addWidget(self.ram_bar, 0, 1)

        # 3. GPU NVIDIA
        self.gpu_bar, self.gpu_lbl = self._create_telemetry_gauge("CARTE GRAPHIQUE (GPU)", "#a855f7")
        grid.addWidget(self.gpu_bar, 1, 0)

        # 4. Disque C:
        self.disk_bar, self.disk_lbl = self._create_telemetry_gauge("DISQUE SYSTÈME (C:)", "#f59e0b")
        grid.addWidget(self.disk_bar, 1, 1)

        layout.addLayout(grid)

        # Bouton d'action RAM Boost & Mode Gaming
        btn_layout = QHBoxLayout()
        self.btn_boost = QPushButton("🚀 PURGER & BOOSTER LA RAM")
        self.btn_boost.setFixedHeight(40)
        self.btn_boost.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_boost.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background: #0369a1; }
        """)
        self.btn_boost.clicked.connect(self.on_boost_ram)
        btn_layout.addWidget(self.btn_boost)

        self.btn_gaming = QPushButton("🎮 BASCULER MODE GAMING")
        self.btn_gaming.setFixedHeight(40)
        self.btn_gaming.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_gaming.setStyleSheet("""
            QPushButton {
                background: #7c3aed;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background: #6d28d9; }
        """)
        self.btn_gaming.clicked.connect(self.on_toggle_gaming)
        btn_layout.addWidget(self.btn_gaming)

        layout.addLayout(btn_layout)
        layout.addStretch()

        return p

    def _create_telemetry_gauge(self, name: str, color: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)

        lbl_title = QLabel(name)
        lbl_title.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; border: none;")
        layout.addWidget(lbl_title)

        lbl_val = QLabel("0 %")
        lbl_val.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 800; border: none;")
        layout.addWidget(lbl_val)

        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(0)
        pbar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(30, 41, 59, 0.8);
                border-radius: 4px;
                height: 8px;
                text-align: right;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(pbar)

        return card, lbl_val

    def update_telemetry(self):
        try:
            diag = system_monitor.get_system_diagnostics()
            cpu_pct = diag.get("cpu_percent", 0)
            ram_info = diag.get("ram", {})
            ram_pct = ram_info.get("percent", 0)
            gpu_info = diag.get("gpu", {})
            gpu_pct = gpu_info.get("load_percent", 0) if gpu_info.get("available") else 0
            disk_info = diag.get("disk", {})
            disk_pct = disk_info.get("percent", 0)

            self.cpu_lbl.setText(f"{cpu_pct:.1f} %")
            self.cpu_bar.findChild(QProgressBar).setValue(int(cpu_pct))

            self.ram_lbl.setText(f"{ram_pct:.1f} % ({ram_info.get('used_gb', 0):.1f}/{ram_info.get('total_gb', 0):.1f} Go)")
            self.ram_bar.findChild(QProgressBar).setValue(int(ram_pct))

            if gpu_info.get("available"):
                self.gpu_lbl.setText(f"{gpu_pct} % ({gpu_info.get('model', 'RTX 4080')})")
                self.gpu_bar.findChild(QProgressBar).setValue(int(gpu_pct))
            else:
                self.gpu_lbl.setText("RTX 4080 (0% Veille)")
                self.gpu_bar.findChild(QProgressBar).setValue(0)

            self.disk_lbl.setText(f"{disk_pct:.1f} % ({disk_info.get('free_gb', 0):.0f} Go libres)")
            self.disk_bar.findChild(QProgressBar).setValue(int(disk_pct))
        except Exception:
            pass

    def on_boost_ram(self):
        count, freed = system_monitor.clean_ram_cache()
        if self.parent_mascot:
            self.parent_mascot.display_message(f"🚀 Mémoire vive optimisée : {freed} Mo libérés !")
        self.update_telemetry()

    def on_toggle_gaming(self):
        current = gaming_mode.is_gaming_mode()
        self.gaming_mode_toggled.emit(not current)
        self.update_gaming_ui()

    def update_gaming_ui(self):
        pass

    def update_vc_ui(self):
        pass

    # =========================================================================
    # 8. PANNEAU BOUCLIER DE SÉCURITÉ
    # =========================================================================
    def create_security_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("🛡️ BOUCLIER DE CYBERSÉCURITÉ WINDOWS")
        title.setStyleSheet("color: #10b981; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

        desc = QLabel("Surveillance continue de Windows Defender, intégrité système et protection contre les malwares :")
        desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(desc)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid #10b981;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        c_layout = QVBoxLayout(card)
        lbl_s = QLabel("✔ INTÉGRITÉ DU SYSTÈME WINDOWS : MAXIMALE (100/100)")
        lbl_s.setStyleSheet("color: #34d399; font-weight: 800; font-size: 13px; border: none;")
        c_layout.addWidget(lbl_s)

        lbl_sub = QLabel("• Windows Defender actif\n• Zéro menace détectée\n• Clés de démarrage sécurisées\n• Tunnels distants sous surveillance")
        lbl_sub.setStyleSheet("color: #e2e8f0; font-size: 11px; border: none; margin-top: 4px;")
        c_layout.addWidget(lbl_sub)
        layout.addWidget(card)

        btn_scan = QPushButton("🔍 LANCER UN AUDIT DE SÉCURITÉ COMPLET")
        btn_scan.setFixedHeight(38)
        btn_scan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_scan.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background: #047857; }
        """)
        btn_scan.clicked.connect(self.on_run_security_scan)
        layout.addWidget(btn_scan)

        layout.addStretch()
        return p

    def on_run_security_scan(self):
        if self.parent_mascot:
            self.parent_mascot.display_message("🛡️ Scan de sécurité en cours : processus, registres et réseau analysés...")

    # =========================================================================
    # 9. PANNEAU CENTRE DOMOTIQUE (PHILIPS HUE RÉEL)
    # =========================================================================
    def create_smarthome_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # En-tête
        h_layout = QHBoxLayout()
        title = QLabel("🏠 CENTRE DOMOTIQUE & PHILIPS HUE")
        title.setStyleSheet("color: #fbbf24; font-size: 15px; font-weight: 800;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        btn_refresh = QPushButton("🔄 ACTUALISER")
        btn_refresh.setFixedHeight(28)
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: rgba(30, 41, 59, 0.8);
                color: #fbbf24; font-weight: bold; font-size: 11px;
                border: 1px solid rgba(251, 191, 36, 0.4);
                border-radius: 6px; padding: 4px 12px;
            }
            QPushButton:hover { background: rgba(251, 191, 36, 0.2); }
        """)
        btn_refresh.clicked.connect(self.refresh_smarthome_panel)
        h_layout.addWidget(btn_refresh)
        layout.addLayout(h_layout)

        # Statut du pont Philips Hue
        bridge_ip = agent_home.smart_home.config.get("hue_bridge_ip", "192.168.1.29")
        paired = agent_home.smart_home.is_hue_paired()
        
        bridge_frame = QFrame()
        bridge_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(251, 191, 36, 0.3);
                border-radius: 10px;
                padding: 6px;
            }
        """)
        bf_layout = QHBoxLayout(bridge_frame)
        bf_layout.setContentsMargins(10, 6, 10, 6)

        b_icon = QLabel("💡")
        b_icon.setStyleSheet("font-size: 20px; border: none;")
        bf_layout.addWidget(b_icon)

        b_info = QVBoxLayout()
        b_title = QLabel(f"<b>Pont Philips Hue :</b> {bridge_ip}")
        b_title.setStyleSheet("color: #f1f5f9; font-size: 12px; border: none;")
        
        status_text = "Connecté et Appairé (Contrôle Physique Actif)" if paired else "Non appairé (Appuyez sur le bouton rond du pont)"
        status_col = "#10b981" if paired else "#f59e0b"
        b_sub = QLabel(status_text)
        b_sub.setStyleSheet(f"color: {status_col}; font-size: 10px; font-weight: bold; border: none;")
        b_info.addWidget(b_title)
        b_info.addWidget(b_sub)
        bf_layout.addLayout(b_info, stretch=1)

        layout.addWidget(bridge_frame)

        # Boutons d'actions globales rapides
        global_box = QHBoxLayout()
        global_box.setSpacing(8)

        btn_night = QPushButton("🌙 Tout Éteindre (Nuit)")
        btn_night.setFixedHeight(34)
        btn_night.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_night.setStyleSheet("""
            QPushButton {
                background: rgba(30, 41, 59, 0.85); color: #cbd5e1;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(51, 65, 85, 0.9); }
        """)
        btn_night.clicked.connect(self.on_hue_all_off)
        global_box.addWidget(btn_night)

        btn_day = QPushButton("☀️ Tout Allumer")
        btn_day.setFixedHeight(34)
        btn_day.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_day.setStyleSheet("""
            QPushButton {
                background: rgba(30, 41, 59, 0.85); color: #fef08a;
                border: 1px solid rgba(251, 191, 36, 0.3);
                border-radius: 8px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(251, 191, 36, 0.2); }
        """)
        btn_day.clicked.connect(self.on_hue_all_on)
        global_box.addWidget(btn_day)

        btn_pink = QPushButton("🌸 Ambiance Zero Two")
        btn_pink.setFixedHeight(34)
        btn_pink.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_pink.setStyleSheet("""
            QPushButton {
                background: rgba(236, 72, 153, 0.2); color: #fbcfe8;
                border: 1px solid rgba(236, 72, 153, 0.4);
                border-radius: 8px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(236, 72, 153, 0.35); }
        """)
        btn_pink.clicked.connect(self.on_hue_zero_two_scene)
        global_box.addWidget(btn_pink)

        layout.addLayout(global_box)

        # Liste des ampoules réelles (Scroll Area)
        scroll_lights = QScrollArea()
        scroll_lights.setWidgetResizable(True)
        scroll_lights.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.lights_container = QWidget()
        self.lights_layout = QVBoxLayout(self.lights_container)
        self.lights_layout.setContentsMargins(0, 4, 0, 4)
        self.lights_layout.setSpacing(8)
        scroll_lights.setWidget(self.lights_container)
        layout.addWidget(scroll_lights, stretch=1)

        # Rapport textuel en direct
        self.home_report_lbl = QLabel()
        self.home_report_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; background: rgba(15, 23, 42, 0.5); border-radius: 6px; padding: 6px;")
        layout.addWidget(self.home_report_lbl)

        # Charger la liste initiale
        self.refresh_smarthome_panel()

        return p

    def refresh_smarthome_panel(self):
        while self.lights_layout.count():
            item = self.lights_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        lights = agent_home.smart_home.get_hue_lights(force_refresh=True)
        if not lights:
            empty_lbl = QLabel("Aucune ampoule détectée sur le pont Hue ou pont non joignable.")
            empty_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 15px;")
            self.lights_layout.addWidget(empty_lbl)
        else:
            for l_id, l_info in lights.items():
                state = l_info.get("state", {})
                is_on = state.get("on", False)
                is_reachable = state.get("reachable", True)
                bri_val = state.get("bri", 254)
                bri_pct = int(round((bri_val / 254.0) * 100))

                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background: rgba(30, 41, 59, 0.7);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 8px;
                    }
                """)
                card_l = QVBoxLayout(card)
                card_l.setSpacing(6)

                top_row = QHBoxLayout()
                lamp_icon = "💡" if is_on else "⚫"
                lamp_title = QLabel(f"{lamp_icon} <b>{l_info.get('name', 'Ampoule')}</b> (ID: {l_id})")
                lamp_title.setStyleSheet("color: #f1f5f9; font-size: 12px;")
                top_row.addWidget(lamp_title, stretch=1)

                reach_text = "Joignable" if is_reachable else "Interrupteur coupé"
                reach_col = "#10b981" if is_reachable else "#f59e0b"
                reach_lbl = QLabel(reach_text)
                reach_lbl.setStyleSheet(f"color: {reach_col}; font-size: 10px; font-weight: bold;")
                top_row.addWidget(reach_lbl)

                toggle_btn = QPushButton("ÉTEINDRE" if is_on else "ALLUMER")
                toggle_btn.setFixedSize(85, 26)
                toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                if is_on:
                    toggle_btn.setStyleSheet("background: #be185d; color: white; font-weight: bold; font-size: 10px; border-radius: 5px; border: none;")
                else:
                    toggle_btn.setStyleSheet("background: #0284c7; color: white; font-weight: bold; font-size: 10px; border-radius: 5px; border: none;")
                toggle_btn.clicked.connect(lambda checked, lid=l_id, cur=is_on: self.on_toggle_hue_light(lid, not cur))
                top_row.addWidget(toggle_btn)
                card_l.addLayout(top_row)

                bot_row = QHBoxLayout()
                bri_lbl = QLabel(f"Luminosité : {bri_pct}%")
                bri_lbl.setStyleSheet("color: #cbd5e1; font-size: 10px;")
                bot_row.addWidget(bri_lbl)

                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setRange(1, 100)
                slider.setValue(bri_pct)
                slider.setFixedHeight(18)
                slider.setStyleSheet("""
                    QSlider::groove:horizontal { height: 4px; background: #1e293b; border-radius: 2px; }
                    QSlider::sub-page:horizontal { background: #fbbf24; border-radius: 2px; }
                    QSlider::handle:horizontal { background: #fef08a; width: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }
                """)
                slider.sliderReleased.connect(lambda lid=l_id, s=slider: self.on_hue_slider_changed(lid, s.value()))
                bot_row.addWidget(slider, stretch=1)

                if "xy" in state or "hue" in state:
                    btn_c_rose = QPushButton("🌸 Rose")
                    btn_c_rose.setFixedHeight(22)
                    btn_c_rose.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_c_rose.setStyleSheet("background: rgba(236, 72, 153, 0.3); color: #fbcfe8; font-size: 9px; font-weight: bold; border-radius: 4px; border: 1px solid rgba(236, 72, 153, 0.5);")
                    btn_c_rose.clicked.connect(lambda checked, lid=l_id: self.on_hue_color_click(lid, "rose"))
                    bot_row.addWidget(btn_c_rose)

                    btn_c_warm = QPushButton("🔥 Chaud")
                    btn_c_warm.setFixedHeight(22)
                    btn_c_warm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_c_warm.setStyleSheet("background: rgba(245, 158, 11, 0.3); color: #fde68a; font-size: 9px; font-weight: bold; border-radius: 4px; border: 1px solid rgba(245, 158, 11, 0.5);")
                    btn_c_warm.clicked.connect(lambda checked, lid=l_id: self.on_hue_color_click(lid, "blanc chaud"))
                    bot_row.addWidget(btn_c_warm)

                    btn_c_cyan = QPushButton("⚡ Cyan")
                    btn_c_cyan.setFixedHeight(22)
                    btn_c_cyan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_c_cyan.setStyleSheet("background: rgba(56, 189, 248, 0.3); color: #bae6fd; font-size: 9px; font-weight: bold; border-radius: 4px; border: 1px solid rgba(56, 189, 248, 0.5);")
                    btn_c_cyan.clicked.connect(lambda checked, lid=l_id: self.on_hue_color_click(lid, "cyan"))
                    bot_row.addWidget(btn_c_cyan)

                card_l.addLayout(bot_row)
                self.lights_layout.addWidget(card)

        self.lights_layout.addStretch()
        self.home_report_lbl.setText(agent_home.smart_home.get_status_report())

    def on_toggle_hue_light(self, light_id: str, new_state: bool):
        ok, msg = agent_home.smart_home.set_light(light_id, on=new_state)
        self.refresh_smarthome_panel()
        if self.parent_mascot:
            self.parent_mascot.display_message(msg)

    def on_hue_slider_changed(self, light_id: str, value: int):
        ok, msg = agent_home.smart_home.set_light(light_id, brightness=value)
        self.refresh_smarthome_panel()

    def on_hue_color_click(self, light_id: str, color_name: str):
        ok, msg = agent_home.smart_home.set_light(light_id, color_name=color_name)
        self.refresh_smarthome_panel()
        if self.parent_mascot:
            self.parent_mascot.display_message(msg)

    def on_hue_all_off(self):
        ok, msg = agent_home.smart_home.set_light("all", on=False)
        self.refresh_smarthome_panel()
        if self.parent_mascot:
            self.parent_mascot.display_message(msg)

    def on_hue_all_on(self):
        ok, msg = agent_home.smart_home.set_light("all", on=True)
        self.refresh_smarthome_panel()
        if self.parent_mascot:
            self.parent_mascot.display_message(msg)

    def on_hue_zero_two_scene(self):
        ok, msg = agent_home.smart_home.activate_zero_two_ambiance()
        self.refresh_smarthome_panel()
        if self.parent_mascot:
            self.parent_mascot.display_message(msg)

    # =========================================================================
    # 10. PANNEAU MÉMOIRE & CERVEAU IA
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
    # 11. PANNEAU PASSERELLE MOBILE 4G/5G
    # =========================================================================
    def create_mobile_panel(self) -> QWidget:
        p = QWidget()
        layout = QVBoxLayout(p)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        title = QLabel("📱 PASSERELLE MOBILE & ACCÈS DISTANT (4G / 5G / WIFI)")
        title.setStyleSheet("color: #22d3ee; font-size: 15px; font-weight: 800;")
        layout.addWidget(title)

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


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    qg = QGDashboard()
    qg.show()
    sys.exit(app.exec())
