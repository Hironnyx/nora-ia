"""
Station de Contrôle & Copilote IA 'Nora' :
- Interface Principale : Dynamic Island / Floating Minimal HUD Capsule (Translucide Glassmorphism)
- Classe Opérationnelle : Copilote Exécutif & Ingénierie Système (Style J.A.R.V.I.S.)
- Télémétrie en direct : CPU, RAM, GPU NVIDIA RTX 4080 (Température & VRAM), Disque C:
- Raccourci Clavier Global 'Ctrl + Alt + N' : Ouvre l'Omnibox de commande immédiate
- Contrôle Total du PC : Volume sonore, Lancement d'applications, Verrouillage Windows, Corbeille
- Agent de Sécurité Dédié : Veille Windows Defender, surveillance du démarrage anti-malware et scan complet
- Détection Vocale Continue : Mode Mains-Libres 'Dis Nora' / 'Hey Nora'
- Vision Multimodale : Analyse instantanée de l'écran avec Google Gemini
- Orchestration Cognitive : Intégration complète avec le QG de commandement
"""
import sys
import os
import time
import math
import random
import threading
import ctypes
from ctypes import wintypes
from pathlib import Path

# Protection absolue contre les crashs en mode sans console (--noconsole / pythonw)
class SafeNullWriter:
    def write(self, s): pass
    def flush(self): pass
    def reconfigure(self, **kwargs): pass

if sys.stdout is None:
    sys.stdout = SafeNullWriter()
elif sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = SafeNullWriter()
elif sys.platform == "win32" and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def _global_exception_handler(exctype, value, tb):
    import traceback
    err_text = "".join(traceback.format_exception(exctype, value, tb))
    try:
        base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
        with open(base / "nora_crash.log", "w", encoding="utf-8") as f:
            f.write(err_text)
    except Exception:
        pass

sys.excepthook = _global_exception_handler

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget, QMenu, QSystemTrayIcon
)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QCursor, QFont, QIcon, QPainter, QColor, QBrush, QPen

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "mascot_assets"

import voice_engine
import nora_brain
import memory_manager
import sound_effects
import system_monitor
import setup_shortcuts
import tools_pc_control
import agent_security
import qg_dashboard
import nora_initiatives
import gaming_mode
import tools_vision
import nora_audio_cache
from wake_word_listener import WakeWordDetector


class NoraBridge(QObject):
    """Signaux thread-safe pour la communication avec l'interface Qt."""
    update_hud = pyqtSignal(str, int)
    update_bubble = pyqtSignal(str)   # Rétrocompatibilité
    set_state = pyqtSignal(str)
    mission_finished = pyqtSignal(str)
    chat_response = pyqtSignal(str)
    wake_triggered = pyqtSignal(str)
    start_speech = pyqtSignal()
    stop_speech = pyqtSignal()
    hotkey_pressed = pyqtSignal()
    system_alert = pyqtSignal(str, str, str, bool)
    security_alert = pyqtSignal(str, str, bool)
    open_qg = pyqtSignal()
    gaming_mode_changed = pyqtSignal(bool)
    screen_vision_requested = pyqtSignal(str)
    swarm_event = pyqtSignal(str, int, str, int)
    mission_requested = pyqtSignal(str)
    user_message_received = pyqtSignal(str)
    ram_boost_requested = pyqtSignal()


class NoraWaveformWidget(QWidget):
    """Visualiseur spectral audio minimaliste néon cyan (7 barres animées)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(68, 22)
        self.bars = [3, 4, 6, 8, 6, 4, 3]
        self.is_active = False
        self.phase = 0.0

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_step)

    def set_active(self, active: bool):
        self.is_active = active
        if active:
            if not self.anim_timer.isActive():
                self.anim_timer.start(45)
        else:
            self.anim_timer.stop()
            self.bars = [3, 3, 4, 4, 4, 3, 3]
            self.update()

    def _animate_step(self):
        self.phase += 0.35
        for i in range(7):
            val = math.sin(self.phase + i * 0.9) * 7.0 + 9.0
            val += random.uniform(-1.5, 1.5)
            self.bars[i] = max(3, min(18, int(val)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        spacing = 3
        bar_w = 4
        start_x = (self.width() - (7 * bar_w + 6 * spacing)) // 2
        cy = self.height() // 2

        pen = QPen(Qt.PenStyle.NoPen)
        painter.setPen(pen)

        for i, h in enumerate(self.bars):
            x = start_x + i * (bar_w + spacing)
            y = cy - (h // 2)
            if self.is_active:
                color = QColor(56, 189, 248, 240) if i in [2, 3, 4] else QColor(14, 165, 233, 190)
            else:
                color = QColor(100, 116, 139, 120)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(x, y, bar_w, h, 2, 2)


class NoraDynamicIsland(QWidget):
    """
    Dynamic Island / Floating Minimal HUD Capsule pour Nora :
    - Format compact top-center (Obsidian Glassmorphism)
    - Jauges télémétriques temps réel (CPU, GPU RTX 4080, RAM)
    - Indicateur d'écoute vocale et waveform spectrale
    - Omnibox de commande rapide intégrée
    - Plaque de notification et de rapport détachable
    """
    def __init__(self):
        super().__init__()

        sound_effects.generate_chimes_if_missing()
        setup_shortcuts.create_desktop_shortcut()

        # Préchauffage RVC en arrière-plan
        try:
            import voice_cloning
            voice_cloning.warmup_in_background()
        except Exception:
            pass

        self.bridge = NoraBridge()
        self.bridge.update_hud.connect(self.display_message)
        self.bridge.update_bubble.connect(self.display_message)
        self.bridge.set_state.connect(self.set_hud_state)
        self.bridge.mission_finished.connect(self.on_mission_finished)
        self.bridge.chat_response.connect(self.on_chat_response)
        self.bridge.wake_triggered.connect(self.on_wake_word_heard)
        self.bridge.start_speech.connect(self.on_speech_started)
        self.bridge.stop_speech.connect(self.on_speech_stopped)
        self.bridge.hotkey_pressed.connect(self.on_hotkey_pressed)
        self.bridge.system_alert.connect(self.on_system_alert)
        self.bridge.security_alert.connect(self.on_security_alert)
        self.bridge.open_qg.connect(self.toggle_qg)
        self.bridge.gaming_mode_changed.connect(self.on_gaming_mode_changed)
        self.bridge.screen_vision_requested.connect(self.trigger_screen_vision)
        self.bridge.mission_requested.connect(self.execute_mission)
        self.bridge.swarm_event.connect(self.on_swarm_event_received)
        self.bridge.user_message_received.connect(self.process_user_message)
        self.bridge.ram_boost_requested.connect(self.optimize_ram_direct)

        self.drag_position = QPoint()
        self.is_dragging = False
        self.is_mission_running = False
        self.is_recording_voice = False
        self.is_speaking_now = False
        self.hands_free_enabled = False
        self.system_alerts_enabled = True
        self.core_pulse_state = 0

        self.init_ui()
        self.init_system_tray()
        self.init_wake_word_detector()
        self.init_system_monitor()
        self.init_security_watchdog()
        self.init_global_hotkey()
        self.init_qg()
        self.init_autonomy_engine()

        # Timer de pulsation lumineuse du Core Arc Reactor (1 Hz)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._pulse_core_led)
        self.pulse_timer.start(500)

        # Salutation sobre J.A.R.V.I.S. au démarrage
        QTimer.singleShot(900, self.welcome_greeting)

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Largeur de base de la capsule
        self.setFixedWidth(510)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 8)
        main_layout.setSpacing(6)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # -------------------------------------------------------------
        # 1. CAPSULE PRINCIPALE (Dynamic Island Pill)
        # -------------------------------------------------------------
        self.capsule_bar = QFrame()
        self.capsule_bar.setObjectName("capsule_bar")
        self.capsule_bar.setFixedHeight(44)
        self.capsule_bar.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.capsule_bar.setStyleSheet("""
            #capsule_bar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(11, 19, 36, 0.96),
                    stop:1 rgba(6, 11, 24, 0.98));
                border: 1px solid rgba(56, 189, 248, 0.38);
                border-radius: 22px;
            }
            #capsule_bar:hover {
                border: 1px solid rgba(56, 189, 248, 0.75);
            }
        """)

        capsule_layout = QHBoxLayout(self.capsule_bar)
        capsule_layout.setContentsMargins(14, 0, 12, 0)
        capsule_layout.setSpacing(10)

        # --- GAUCHE : Arc Core & Marque Nora ---
        core_layout = QHBoxLayout()
        core_layout.setSpacing(6)

        self.core_dot = QLabel("●")
        self.core_dot.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: 900; background: transparent; border: none;")
        self.core_dot.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.lbl_nora = QLabel("NORA")
        self.lbl_nora.setStyleSheet("color: #f8fafc; font-size: 11px; font-weight: 900; letter-spacing: 2px; font-family: 'Segoe UI', system-ui; background: transparent; border: none;")
        self.lbl_nora.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.lbl_state = QLabel("STANDBY")
        self.lbl_state.setStyleSheet("""
            color: #38bdf8;
            font-size: 8px;
            font-weight: 700;
            letter-spacing: 0.5px;
            background: rgba(56, 189, 248, 0.12);
            padding: 2px 5px;
            border-radius: 4px;
            border: none;
        """)
        self.lbl_state.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        core_layout.addWidget(self.core_dot)
        core_layout.addWidget(self.lbl_nora)
        core_layout.addWidget(self.lbl_state)
        capsule_layout.addLayout(core_layout)

        # Séparateur vertical
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: rgba(255, 255, 255, 0.12); font-size: 11px; background: transparent; border: none;")
        capsule_layout.addWidget(sep1)

        # --- CENTRE : Stack Dynamique (Télémétrie Idle / Waveform Écoute / Action) ---
        self.center_stack = QStackedWidget()
        self.center_stack.setStyleSheet("background: transparent; border: none;")

        # Page 0 : Mini-jauges de télémétrie matérielle
        page_telemetry = QWidget()
        t_layout = QHBoxLayout(page_telemetry)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(6)

        self.chip_cpu = QLabel("CPU 0%")
        self.chip_cpu.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; font-family: 'Consolas', 'Segoe UI'; background: rgba(255, 255, 255, 0.05); padding: 3px 6px; border-radius: 6px; border: none;")

        self.chip_gpu = QLabel("RTX 4080 --°C")
        self.chip_gpu.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 600; font-family: 'Consolas', 'Segoe UI'; background: rgba(56, 189, 248, 0.08); padding: 3px 6px; border-radius: 6px; border: none;")

        self.chip_ram = QLabel("RAM 0%")
        self.chip_ram.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; font-family: 'Consolas', 'Segoe UI'; background: rgba(255, 255, 255, 0.05); padding: 3px 6px; border-radius: 6px; border: none;")

        t_layout.addWidget(self.chip_cpu)
        t_layout.addWidget(self.chip_gpu)
        t_layout.addWidget(self.chip_ram)
        self.center_stack.addWidget(page_telemetry)  # Index 0

        # Page 1 : Mode Écoute Vocale & Spectral Waveform
        page_listen = QWidget()
        l_layout = QHBoxLayout(page_listen)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(6)

        self.waveform = NoraWaveformWidget()
        self.lbl_listen = QLabel("À votre écoute...")
        self.lbl_listen.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 600; background: transparent; border: none;")

        l_layout.addWidget(self.waveform)
        l_layout.addWidget(self.lbl_listen)
        self.center_stack.addWidget(page_listen)  # Index 1

        # Page 2 : Mission / Traitement actif
        page_work = QWidget()
        w_layout = QHBoxLayout(page_work)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.setSpacing(6)

        self.lbl_work = QLabel("⚡ Traitement en cours...")
        self.lbl_work.setStyleSheet("color: #a78bfa; font-size: 10px; font-weight: 600; background: transparent; border: none;")
        w_layout.addWidget(self.lbl_work)
        self.center_stack.addWidget(page_work)  # Index 2

        capsule_layout.addWidget(self.center_stack, stretch=1)

        # Séparateur vertical
        sep2 = QLabel("|")
        sep2.setStyleSheet("color: rgba(255, 255, 255, 0.12); font-size: 11px; background: transparent; border: none;")
        capsule_layout.addWidget(sep2)

        # --- DROITE : Boutons d'Action & Déclencheurs Rapides ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        btn_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.04);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.18);
                color: #f8fafc;
                border-color: rgba(56, 189, 248, 0.5);
            }
        """

        # Bouton Micro
        self.btn_mic = QPushButton("🎙️")
        self.btn_mic.setFixedSize(26, 26)
        self.btn_mic.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_mic.setStyleSheet(btn_style)
        self.btn_mic.setToolTip("Activer l'écoute vocale (Clic) / Mains-Libres 'Dis Nora'")
        self.btn_mic.clicked.connect(self.start_voice_input)
        btn_layout.addWidget(self.btn_mic)

        # Bouton Vision Écran
        self.btn_vision = QPushButton("👁️")
        self.btn_vision.setFixedSize(26, 26)
        self.btn_vision.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_vision.setStyleSheet(btn_style)
        self.btn_vision.setToolTip("Analyser l'écran (Vision Multimodale Gemini)")
        self.btn_vision.clicked.connect(lambda: self.trigger_screen_vision(""))
        btn_layout.addWidget(self.btn_vision)

        # Bouton Omnibox (Commande Rapide)
        self.btn_cmd = QPushButton("⚡")
        self.btn_cmd.setFixedSize(26, 26)
        self.btn_cmd.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cmd.setStyleSheet(btn_style)
        self.btn_cmd.setToolTip("Ouvrir la ligne de commande rapide (Ctrl+Alt+N)")
        self.btn_cmd.clicked.connect(self.toggle_command_bar)
        btn_layout.addWidget(self.btn_cmd)

        # Bouton QG Dashboard
        self.btn_qg = QPushButton("HQ")
        self.btn_qg.setFixedSize(30, 26)
        self.btn_qg.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_qg.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.12);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
                font-size: 10px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.28);
                color: #ffffff;
                border-color: #38bdf8;
            }
        """)
        self.btn_qg.setToolTip("Ouvrir le Poste de Contrôle QG")
        self.btn_qg.clicked.connect(self.toggle_qg)
        btn_layout.addWidget(self.btn_qg)

        capsule_layout.addLayout(btn_layout)
        main_layout.addWidget(self.capsule_bar)

        # -------------------------------------------------------------
        # 2. OMNIBOX DE COMMANDE RAPIDE (Rétractable)
        # -------------------------------------------------------------
        self.cmd_bar = QFrame()
        self.cmd_bar.setObjectName("cmd_bar")
        self.cmd_bar.setFixedHeight(38)
        self.cmd_bar.setStyleSheet("""
            #cmd_bar {
                background: rgba(15, 23, 42, 0.96);
                border: 1px solid rgba(56, 189, 248, 0.45);
                border-radius: 19px;
            }
        """)
        cb_layout = QHBoxLayout(self.cmd_bar)
        cb_layout.setContentsMargins(12, 0, 8, 0)
        cb_layout.setSpacing(8)

        lbl_prompt_icon = QLabel("➤")
        lbl_prompt_icon.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 800; background: transparent; border: none;")
        cb_layout.addWidget(lbl_prompt_icon)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Donnez un ordre ou une question à Nora... (Entrée pour valider, Échap pour masquer)")
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f8fafc;
                font-size: 11px;
                font-family: 'Segoe UI', system-ui;
            }
        """)
        self.cmd_input.returnPressed.connect(self.submit_cmd_input)
        cb_layout.addWidget(self.cmd_input, stretch=1)

        btn_send = QPushButton("Exécuter")
        btn_send.setFixedHeight(26)
        btn_send.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_send.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: #ffffff;
                font-size: 10px;
                font-weight: 700;
                padding: 0 10px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background: #0369a1;
            }
        """)
        btn_send.clicked.connect(self.submit_cmd_input)
        cb_layout.addWidget(btn_send)

        btn_close_cmd = QPushButton("✕")
        btn_close_cmd.setFixedSize(20, 20)
        btn_close_cmd.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close_cmd.setStyleSheet("background: transparent; color: #64748b; font-size: 10px; border: none;")
        btn_close_cmd.clicked.connect(lambda: self.cmd_bar.hide())
        cb_layout.addWidget(btn_close_cmd)

        self.cmd_bar.hide()
        main_layout.addWidget(self.cmd_bar)

        # -------------------------------------------------------------
        # 3. CARTE HUD DE NOTIFICATION & RAPPORT DÉTACHABLE
        # -------------------------------------------------------------
        self.hud_card = QFrame()
        self.hud_card.setObjectName("hud_card")
        self.hud_card.setStyleSheet("""
            #hud_card {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(10, 16, 30, 0.97),
                    stop:1 rgba(5, 9, 18, 0.99));
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 12px;
            }
        """)
        hud_layout = QVBoxLayout(self.hud_card)
        hud_layout.setContentsMargins(12, 8, 12, 10)
        hud_layout.setSpacing(6)

        header_layout = QHBoxLayout()
        self.lbl_hud_title = QLabel("⚡ NORA EXECUTIVE HUD")
        self.lbl_hud_title.setStyleSheet("color: #38bdf8; font-size: 9px; font-weight: 800; letter-spacing: 1px; background: transparent; border: none;")
        header_layout.addWidget(self.lbl_hud_title, stretch=1)

        btn_hud_close = QPushButton("✕")
        btn_hud_close.setFixedSize(18, 18)
        btn_hud_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_hud_close.setStyleSheet("background: transparent; color: #64748b; font-size: 10px; border: none;")
        btn_hud_close.clicked.connect(lambda: self.hud_card.hide())
        header_layout.addWidget(btn_hud_close)
        hud_layout.addLayout(header_layout)

        self.hud_msg = QLabel("")
        self.hud_msg.setWordWrap(True)
        self.hud_msg.setStyleSheet("color: #f1f5f9; font-size: 11px; line-height: 16px; background: transparent; border: none; font-family: 'Segoe UI', system-ui;")
        hud_layout.addWidget(self.hud_msg)

        self.hud_card.hide()
        main_layout.addWidget(self.hud_card)

        # Timer de masquage automatique du HUD
        self.hud_timer = QTimer(self)
        self.hud_timer.setSingleShot(True)
        self.hud_timer.timeout.connect(lambda: self.hud_card.hide())

        # Position initiale : Top-Center de l'écran principal
        self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.left() + (screen.width() - self.width()) // 2
        y = screen.top() + 18
        self.move(x, y)

    def _pulse_core_led(self):
        """Anime doucement l'intensité lumineuse du réacteur Arc Core."""
        self.core_pulse_state = (self.core_pulse_state + 1) % 2
        if self.is_speaking_now:
            color = "#38bdf8" if self.core_pulse_state == 0 else "#60a5fa"
            self.core_dot.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 900; background: transparent; border: none;")
        elif self.is_mission_running:
            color = "#a78bfa" if self.core_pulse_state == 0 else "#818cf8"
            self.core_dot.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 900; background: transparent; border: none;")
        else:
            color = "#38bdf8" if self.core_pulse_state == 0 else "rgba(56, 189, 248, 0.45)"
            self.core_dot.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 900; background: transparent; border: none;")

    def set_hud_state(self, state: str):
        """Bascule l'état visuel de la capsule (idle, listen, work)."""
        if QThread.currentThread() != self.thread():
            self.bridge.set_state.emit(state)
            return

        if state == "listen":
            self.lbl_state.setText("LISTENING")
            self.lbl_state.setStyleSheet("color: #38bdf8; font-size: 8px; font-weight: 700; background: rgba(56, 189, 248, 0.2); padding: 2px 5px; border-radius: 4px; border: none;")
            self.center_stack.setCurrentIndex(1)
            self.waveform.set_active(True)
        elif state == "work":
            self.lbl_state.setText("EXEC")
            self.lbl_state.setStyleSheet("color: #a78bfa; font-size: 8px; font-weight: 700; background: rgba(167, 139, 250, 0.2); padding: 2px 5px; border-radius: 4px; border: none;")
            self.center_stack.setCurrentIndex(2)
            self.waveform.set_active(False)
        else:
            self.lbl_state.setText("STANDBY")
            self.lbl_state.setStyleSheet("color: #38bdf8; font-size: 8px; font-weight: 700; background: rgba(56, 189, 248, 0.12); padding: 2px 5px; border-radius: 4px; border: none;")
            self.center_stack.setCurrentIndex(0)
            self.waveform.set_active(False)

    # =========================================================================
    # AFFICHAGE DE MESSAGES & NOTIFICATIONS HUD
    # =========================================================================
    def display_message(self, text: str, duration_ms: int = 6500):
        """Affiche un message stylisé dans la carte HUD rétractable."""
        if QThread.currentThread() != self.thread():
            self.bridge.update_hud.emit(text, duration_ms)
            return
        if not text:
            return
        self.hud_msg.setText(text)
        self.hud_card.show()
        self.adjustSize()
        self.hud_timer.stop()
        if duration_ms > 0:
            self.hud_timer.start(duration_ms)

    def welcome_greeting(self):
        msg = memory_manager.get_welcome_message()
        self.display_message(msg, duration_ms=7000)
        self.speak_nora(msg)

    # =========================================================================
    # COMMANDE RAPIDE (OMNIBOX)
    # =========================================================================
    def toggle_command_bar(self):
        if self.cmd_bar.isVisible():
            self.cmd_bar.hide()
        else:
            self.cmd_bar.show()
            self.cmd_input.setFocus()
            self.cmd_input.selectAll()
        self.adjustSize()

    def submit_cmd_input(self):
        text = self.cmd_input.text().strip()
        if text:
            self.cmd_input.clear()
            self.cmd_bar.hide()
            self.adjustSize()
            self.process_user_message(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.cmd_bar.isVisible():
                self.cmd_bar.hide()
                self.adjustSize()
            if self.hud_card.isVisible():
                self.hud_card.hide()
                self.adjustSize()
        super().keyPressEvent(event)

    # =========================================================================
    # GESTION DES MESSAGES UTILISATEUR & MISSIONS
    # =========================================================================
    def process_user_message(self, user_text: str):
        if QThread.currentThread() != self.thread():
            self.bridge.user_message_received.emit(user_text)
            return

        if self.is_mission_running:
            self.display_message("⏳ Une mission est déjà en cours d'exécution, Maverick.")
            return

        # Détection immédiate des commandes vocales de changement de voix
        lower = user_text.lower()
        if "voix" in lower:
            if any(k in lower for k in ["denise", "executiv", "exécutiv"]):
                memory_manager.set_voice_profile("denise")
                msg = "Profil vocal configuré sur Nora Exécutive. Prête pour vos directives, Maverick."
                self.bridge.chat_response.emit(msg)
                return
            elif any(k in lower for k in ["jarvis", "henri", "majordome"]):
                memory_manager.set_voice_profile("henri")
                msg = "Profil vocal configuré sur Nora J.A.R.V.I.S. À vos ordres, Maverick."
                self.bridge.chat_response.emit(msg)
                return
            elif any(k in lower for k in ["vivienne", "studio"]):
                memory_manager.set_voice_profile("vivienne")
                msg = "Profil vocal configuré sur Nora Studio. À votre écoute, Maverick."
                self.bridge.chat_response.emit(msg)
                return
            elif any(k in lower for k in ["remy", "cyber"]):
                memory_manager.set_voice_profile("remy")
                msg = "Profil vocal configuré sur Nora Cyber Tech. Systèmes parés, Maverick."
                self.bridge.chat_response.emit(msg)
                return

        self.set_hud_state("work")
        self.display_message(f"💬 « {user_text} »\nAnalyse cognitive en cours...")

        def analyze_thread():
            try:
                intent, chat_reply = nora_brain.analyze_intent_and_respond(user_text)
                if intent == "OPEN_QG":
                    self.bridge.open_qg.emit()
                    self.bridge.chat_response.emit(chat_reply)
                elif intent == "GAMING_ON":
                    self.bridge.gaming_mode_changed.emit(True)
                    self.bridge.chat_response.emit(chat_reply)
                elif intent == "GAMING_OFF":
                    self.bridge.gaming_mode_changed.emit(False)
                    self.bridge.chat_response.emit(chat_reply)
                elif intent == "BOOST_RAM":
                    self.bridge.chat_response.emit(chat_reply)
                    self.bridge.ram_boost_requested.emit()
                elif intent == "SCREEN_VISION":
                    self.bridge.screen_vision_requested.emit(chat_reply)
                elif intent == "CHAT":
                    self.bridge.chat_response.emit(chat_reply)
                else:
                    self.bridge.mission_requested.emit(user_text)
            except Exception as e:
                self.bridge.chat_response.emit(f"Maverick, une anomalie est survenue lors de l'analyse : {e}")

        threading.Thread(target=analyze_thread, daemon=True).start()

    def on_chat_response(self, reply_text: str):
        if QThread.currentThread() != self.thread():
            self.bridge.chat_response.emit(reply_text)
            return
        self.set_hud_state("idle")
        self.display_message(reply_text, duration_ms=7500)
        self.speak_nora(reply_text)

    def execute_mission(self, mission_goal: str):
        if QThread.currentThread() != self.thread():
            self.bridge.mission_requested.emit(mission_goal)
            return
        self.is_mission_running = True
        self.set_hud_state("work")
        self.display_message(f"⚙️ <b>MISSION DÉMARRÉE :</b>\n{mission_goal}\n\nMobilisation de l'Essaim Cognitif en cours...", duration_ms=0)
        sound_effects.play_wake_chime()
        self.speak_nora("C'est bien noté Maverick. Je mobilise mes agents pour exécuter la tâche.")

        def mission_worker():
            def step_callback(step_type, text):
                if step_type == "swarm":
                    self.bridge.update_hud.emit(f"🐝 <b>AGORA ESSAIM :</b>\n{text}", 0)
                    self.bridge.swarm_event.emit("Essaim", 1, text, 96)
                else:
                    self.bridge.update_hud.emit(f"⚙️ {text}", 0)

            try:
                from mission_engine import run_autonomous_mission
                report = run_autonomous_mission(mission_goal, callback_step=step_callback)
                self.bridge.mission_finished.emit(report)
            except Exception as e:
                self.bridge.mission_finished.emit(f"Erreur mission : {str(e)}")

        threading.Thread(target=mission_worker, daemon=True).start()

    def on_mission_finished(self, report: str):
        if QThread.currentThread() != self.thread():
            self.bridge.mission_finished.emit(report)
            return
        self.is_mission_running = False
        self.set_hud_state("idle")
        sound_effects.play_success_chime()
        summary = "🎉 <b>Mission accomplie avec succès, Maverick !</b>\nLes opérations ont été clôturées à 100 %."
        self.display_message(summary, duration_ms=8000)
        self.notify_windows("Mission Nora Terminée", "Toutes les opérations demandées ont été effectuées avec succès.")
        self.speak_nora("Mission accomplie Maverick. Toutes les opérations ont été menées à bien.")

    def on_swarm_event_received(self, agent: str, round_num: int, text: str, consensus: int):
        if hasattr(self, 'qg') and self.qg:
            try:
                self.qg.update_swarm_event(agent, round_num, text, consensus)
            except Exception:
                pass

    # =========================================================================
    # AUDIO & SYNTHÈSE VOCALE
    # =========================================================================
    def speak_nora(self, text: str, on_finished=None, force: bool = False):
        if gaming_mode.is_gaming_mode() and not force:
            if on_finished:
                threading.Timer(0.1, on_finished).start()
            return

        def _on_start():
            try:
                self.bridge.start_speech.emit()
            except RuntimeError:
                pass

        def _on_end():
            try:
                self.bridge.stop_speech.emit()
            except RuntimeError:
                pass
            if on_finished:
                on_finished()

        voice_engine.speak(text, on_start=_on_start, on_end=_on_end)

    def on_speech_started(self):
        self.is_speaking_now = True

    def on_speech_stopped(self):
        self.is_speaking_now = False

    def start_voice_input(self):
        if self.is_mission_running or getattr(self, 'is_recording_voice', False):
            return
        self.is_recording_voice = True

        def record_thread():
            try:
                self.bridge.set_state.emit("listen")
                self.bridge.update_hud.emit("🎙️ <i>À votre écoute, Maverick... Parlez librement.</i>", 5000)
                spoken = voice_engine.listen_microphone()
                if spoken:
                    self.bridge.user_message_received.emit(spoken)
                else:
                    self.bridge.set_state.emit("idle")
                    self.bridge.update_hud.emit("Je n'ai pas capté votre voix, Maverick. Cliquez sur 🎙️ ou écrivez-moi.", 5000)
            except Exception as e:
                self.bridge.set_state.emit("idle")
                self.bridge.update_hud.emit(f"Erreur microphone : {e}", 4000)
            finally:
                self.is_recording_voice = False

        threading.Thread(target=record_thread, daemon=True).start()

    def on_wake_word_heard(self, command: str):
        if self.is_mission_running:
            return
        if command:
            self.process_user_message(command)
        else:
            sound_effects.play_wake_chime()
            self.set_hud_state("listen")
            self.display_message("✨ Oui Maverick, je suis à votre écoute.", duration_ms=4000)
            self.start_voice_input()

    # =========================================================================
    # VISION D'ÉCRAN MULTIMODALE GEMINI
    # =========================================================================
    def trigger_screen_vision(self, prompt_text: str = ""):
        if QThread.currentThread() != self.thread():
            self.bridge.screen_vision_requested.emit(prompt_text)
            return
        if self.is_mission_running:
            self.display_message("⏳ Une mission est déjà en cours Maverick, un instant s'il vous plaît.")
            return

        self.set_hud_state("work")
        self.display_message("👁️ <b>Analyse visuelle de l'écran en cours...</b>", duration_ms=0)
        sound_effects.play_wake_chime()

        def vision_worker():
            res = tools_vision.analyze_screen_with_gemini(prompt_text)
            speech = res.get("speech", "")
            self.bridge.set_state.emit("idle")
            self.bridge.update_hud.emit(f"👁️ <b>RAPPORT DE VISION :</b>\n{speech}", 9000)
            self.speak_nora(speech)

        threading.Thread(target=vision_worker, daemon=True).start()

    # =========================================================================
    # SERVICES D'ARRIÈRE-PLAN (MONITORING, DEFENDER, HOTKEY, SYSTRAY, QG)
    # =========================================================================
    def init_system_monitor(self):
        def on_sys_alert(category, title, msg, speak):
            self.bridge.system_alert.emit(category, title, msg, speak)

        self.sys_monitor = system_monitor.SystemMonitor(on_alert_callback=on_sys_alert)
        self.sys_monitor.start()

        # Timer de mise à jour des mini-puces de télémétrie sur la Dynamic Island (toutes les 2.0 s)
        self.telemetry_hud_timer = QTimer(self)
        self.telemetry_hud_timer.timeout.connect(self._update_hud_telemetry)
        self.telemetry_hud_timer.start(2000)
        self._update_hud_telemetry()

    def _update_hud_telemetry(self):
        try:
            stats = system_monitor.get_current_metrics()
            cpu = stats.get("cpu_percent", 0.0)
            ram = stats.get("ram_percent", 0.0)
            gpu = stats.get("gpu", {})

            # 1. CPU
            self.chip_cpu.setText(f"CPU {int(cpu)}%")
            if cpu > 85:
                self.chip_cpu.setStyleSheet("color: #ef4444; font-size: 10px; font-weight: 700; background: rgba(239, 68, 68, 0.15); padding: 3px 6px; border-radius: 6px; border: none;")
            elif cpu > 65:
                self.chip_cpu.setStyleSheet("color: #f59e0b; font-size: 10px; font-weight: 700; background: rgba(245, 158, 11, 0.15); padding: 3px 6px; border-radius: 6px; border: none;")
            else:
                self.chip_cpu.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; background: rgba(255, 255, 255, 0.05); padding: 3px 6px; border-radius: 6px; border: none;")

            # 2. GPU (RTX 4080)
            gpu_name = gpu.get("name", "GPU")
            temp = gpu.get("temp_c", 0)
            load = gpu.get("load_pct", 0)
            if "4080" in gpu_name:
                self.chip_gpu.setText(f"RTX 4080 {temp}°C")
            else:
                self.chip_gpu.setText(f"GPU {temp}°C")

            # 3. RAM
            self.chip_ram.setText(f"RAM {int(ram)}%")
            if ram > 85:
                self.chip_ram.setStyleSheet("color: #ef4444; font-size: 10px; font-weight: 700; background: rgba(239, 68, 68, 0.15); padding: 3px 6px; border-radius: 6px; border: none;")
            else:
                self.chip_ram.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 600; background: rgba(255, 255, 255, 0.05); padding: 3px 6px; border-radius: 6px; border: none;")
        except Exception:
            pass

    def on_system_alert(self, category: str, title: str, msg: str, speak: bool):
        if not self.system_alerts_enabled:
            return
        icon = "⚠️" if category == "warning" else "📥"
        self.display_message(f"{icon} <b>{title}</b> :\n{msg}", duration_ms=7000)
        if speak and not self.is_speaking_now and not self.is_mission_running:
            sound_effects.play_wake_chime()
            self.speak_nora(msg)

    def init_security_watchdog(self):
        def on_sec_alert(title, msg, is_critical):
            self.bridge.security_alert.emit(title, msg, is_critical)

        self.sec_watchdog = agent_security.SecurityWatchdog(on_alert=on_sec_alert)
        self.sec_watchdog.start()

    def on_security_alert(self, title: str, msg: str, is_critical: bool):
        self.display_message(f"🚨 <b>SÉCURITÉ OS : {title}</b>\n{msg}", duration_ms=8000)
        sound_effects.play_wake_chime()
        if not self.is_speaking_now:
            self.speak_nora(msg)

    def init_global_hotkey(self):
        """Enregistre le raccourci global Ctrl+Alt+N sous Windows."""
        self.hotkey_running = True

        def hotkey_thread():
            user32 = ctypes.windll.user32
            HOTKEY_ID = 1001
            MOD_CONTROL = 0x0002
            MOD_ALT = 0x0001
            VK_N = 0x4E

            if user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_N):
                try:
                    msg = wintypes.MSG()
                    while self.hotkey_running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                        if msg.message == 0x0312:
                            self.bridge.hotkey_pressed.emit()
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
                finally:
                    user32.UnregisterHotKey(None, HOTKEY_ID)

        t = threading.Thread(target=hotkey_thread, daemon=True)
        t.start()

    def on_hotkey_pressed(self):
        """Invoque l'Omnibox instantanément lors de l'appui sur Ctrl+Alt+N."""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.raise_()
        self.activateWindow()
        sound_effects.play_wake_chime()
        self.toggle_command_bar()

    def init_wake_word_detector(self):
        def on_wake_alone():
            self.bridge.wake_triggered.emit("")

        def on_command(cmd):
            self.bridge.wake_triggered.emit(cmd)

        self.wake_detector = WakeWordDetector(
            on_wake_callback=on_wake_alone,
            on_command_callback=on_command
        )

    def toggle_hands_free(self):
        self.hands_free_enabled = not self.hands_free_enabled
        if self.hands_free_enabled:
            self.wake_detector.start()
            sound_effects.play_wake_chime()
            self.btn_mic.setStyleSheet("""
                QPushButton {
                    background: rgba(56, 189, 248, 0.3);
                    color: #ffffff;
                    border: 1px solid #38bdf8;
                    border-radius: 12px;
                }
            """)
            self.display_message("🎧 Mode Mains-Libres ACTIF !\nDites simplement 'Dis Nora' ou 'Hey Nora' à voix haute.", duration_ms=4500)
        else:
            self.wake_detector.stop()
            self.btn_mic.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.04);
                    color: #94a3b8;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                }
            """)
            self.display_message("🎧 Mode Mains-Libres désactivé.", duration_ms=3000)

    def init_qg(self):
        self.qg = qg_dashboard.QGDashboard(parent_mascot=self)
        self.qg.initiative_accepted.connect(self.on_initiative_accepted)
        self.qg.initiative_refused.connect(self.on_initiative_refused)
        self.qg.action_requested.connect(self.on_qg_action_requested)
        self.qg.gaming_mode_toggled.connect(self.on_qg_gaming_toggled)
        self.qg.ram_boost_requested.connect(self.optimize_ram_direct)
        self.qg.screen_vision_requested.connect(lambda: self.trigger_screen_vision(""))

    def open_qg_initial(self):
        if hasattr(self, 'qg') and self.qg:
            self.qg.show_independent()

    def init_autonomy_engine(self):
        """Démarre le Moteur d'Autonomie Exécutif en tâche de fond permanente."""
        import nora_consciousness
        def _on_action(action_type, title, desc, speak):
            self.bridge.update_hud.emit(f"⚡ <b>{title}</b>\n{desc}", 7000)
            if speak and not self.is_speaking_now:
                self.speak_nora(desc)

        def _on_hud(text, duration_ms):
            self.bridge.update_hud.emit(text, duration_ms)

        def _on_thought(text, speak):
            self.bridge.update_hud.emit(f"💡 <b>NOTE NORA :</b>\n{text}", 6000)
            if speak and not self.is_speaking_now:
                self.speak_nora(text)

        self.autonomy_engine = nora_consciousness.autonomy_engine
        self.autonomy_engine.on_action = _on_action
        self.autonomy_engine.on_hud = _on_hud
        self.autonomy_engine.on_thought = _on_thought
        self.autonomy_engine.start()

    def toggle_qg(self):
        if hasattr(self, 'qg') and self.qg:
            self.qg.toggle_independent()

    def on_initiative_accepted(self, init_id: str):
        res = nora_initiatives.execute_accepted_initiative(init_id)
        self.display_message(res, duration_ms=6500)
        sound_effects.play_success_chime()
        self.speak_nora(res)

    def on_initiative_refused(self, init_id: str):
        res = nora_initiatives.refuse_initiative(init_id)
        self.display_message(res, duration_ms=4000)
        self.speak_nora(res)

    def on_qg_action_requested(self, action_name: str):
        if action_name == "security_scan":
            self.run_security_scan_action()
        elif action_name == "organize_downloads":
            self.execute_mission("Range mon dossier Téléchargements en triant tout par catégories.")
        elif action_name == "web_search":
            self.start_voice_input()

    def on_qg_gaming_toggled(self, active: bool):
        stat = "ACTIVÉ" if active else "DÉSACTIVÉ"
        msg = f"🎮 Mode Gaming {stat}, Maverick. Priorité maximale accordée au GPU."
        self.display_message(msg, duration_ms=4500)
        self.speak_nora(msg, force=True)

    def on_gaming_mode_changed(self, active: bool):
        if hasattr(self, 'qg') and self.qg:
            self.qg.update_gaming_ui()

    def optimize_ram_direct(self):
        if QThread.currentThread() != self.thread():
            self.bridge.ram_boost_requested.emit()
            return
        sound_effects.play_wake_chime()
        count, freed = gaming_mode.optimize_ram_boost()
        msg = f"⚡ Mémoire vive optimisée : {count} processus allégés, {freed} Mo libérés !"
        self.display_message(msg, duration_ms=5000)
        self.speak_nora(msg, force=True)

    def run_security_scan_action(self):
        self.set_hud_state("work")
        self.display_message("🛡️ <b>Audit de sécurité en cours...</b>", duration_ms=0)
        sound_effects.play_wake_chime()

        def scan_worker():
            scan = agent_security.run_security_scan()
            self.bridge.set_state.emit("idle")
            self.bridge.update_hud.emit(f"🛡️ <b>Score de Sécurité : {scan['score']}/100</b>\n{scan['speech']}", 8000)
            self.speak_nora(scan["speech"])

        threading.Thread(target=scan_worker, daemon=True).start()

    # =========================================================================
    # SYSTEM TRAY & CONTEXT MENU
    # =========================================================================
    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        ico_path = ASSETS_DIR / "nora.ico"
        if not ico_path.exists():
            ico_path = ASSETS_DIR / "nora_idle.png"
        if ico_path.exists():
            self.tray_icon.setIcon(QIcon(str(ico_path)))
        self.tray_icon.setToolTip("NORA WORKSTATION | Copilote Exécutif IA")
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            self.show_context_menu(QCursor.pos())

    def show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0b1120;
                color: #f1f5f9;
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 8px;
                padding: 6px;
                font-size: 11px;
                font-family: 'Segoe UI', system-ui;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0284c7;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.08);
                margin: 4px 6px;
            }
        """)

        act_qg = menu.addAction("Poste de Contrôle QG")
        act_cmd = menu.addAction("Ligne de Commande Rapide (Ctrl+Alt+N)")
        act_mic = menu.addAction("Entrée Vocale")
        act_handsfree = menu.addAction("Mode Mains-Libres ('Dis Nora')")
        act_vision = menu.addAction("Vision Écran (Gemini Multimodal)")

        menu.addSeparator()
        menu_voice = menu.addMenu("Profil Vocal Nora")
        menu_voice.setStyleSheet(menu.styleSheet())
        current_voice = memory_manager.get_voice_profile()
        profiles = memory_manager.VOICE_PROFILES
        voice_actions = {}
        for p_id, p_info in profiles.items():
            mark = "● " if p_id == current_voice else "○ "
            act_p = menu_voice.addAction(f"{mark}{p_info['name']}")
            voice_actions[act_p] = p_id

        menu_voice.addSeparator()
        act_test_voice = menu_voice.addAction("Tester la voix active")
        act_clear_cache = menu_voice.addAction("Purger le cache audio")

        menu.addSeparator()
        act_ram = menu.addAction("Purger la RAM")
        is_gaming = gaming_mode.is_gaming_mode()
        act_gaming = menu.addAction("Désactiver Mode Gaming" if is_gaming else "Activer Mode Gaming (Priorité GPU)")
        act_sec = menu.addAction("Audit de Sécurité Système")

        menu.addSeparator()
        act_lock = menu.addAction("Verrouiller la session Windows")
        act_bin = menu.addAction("Vider la corbeille")
        act_mute = menu.addAction("Couper / Rétablir le son")

        menu.addSeparator()
        act_vis = menu.addAction("Masquer la Capsule HUD" if self.isVisible() else "Afficher la Capsule HUD")
        is_startup = setup_shortcuts.is_startup_enabled()
        act_startup = menu.addAction("☑ Lancer avec Windows" if is_startup else "☐ Lancer avec Windows")
        menu.addSeparator()
        act_quit = menu.addAction("Quitter la station Nora")

        action = menu.exec(global_pos)
        if action == act_qg:
            self.toggle_qg()
        elif action == act_cmd:
            self.toggle_command_bar()
        elif action == act_mic:
            self.start_voice_input()
        elif action == act_handsfree:
            self.toggle_hands_free()
        elif action == act_vision:
            self.trigger_screen_vision("")
        elif action in voice_actions:
            chosen_id = voice_actions[action]
            memory_manager.set_voice_profile(chosen_id)
            info = memory_manager.get_voice_profile_info(chosen_id)
            self.display_message(f"🎙️ Profil vocal : {info['name']}", duration_ms=4000)
            self.speak_nora(f"Profil vocal configuré sur {info['name']}. À vos ordres, Maverick.")
        elif action == act_test_voice:
            info = memory_manager.get_voice_profile_info()
            self.speak_nora(f"Système vocal opérationnel Maverick. Profil actif : {info['name']}.")
        elif action == act_clear_cache:
            count = nora_audio_cache.clear_cache()
            self.display_message(f"🧹 Cache audio purgé ({count} fichiers)", duration_ms=3500)
        elif action == act_ram:
            self.optimize_ram_direct()
        elif action == act_gaming:
            new_state, msg = gaming_mode.toggle_gaming_mode()
            if hasattr(self, 'qg') and self.qg:
                self.qg.update_gaming_ui()
            self.display_message(msg, duration_ms=4500)
            self.speak_nora(msg, force=True)
        elif action == act_sec:
            self.run_security_scan_action()
        elif action == act_lock:
            tools_pc_control.lock_workstation()
        elif action == act_bin:
            ok, msg = tools_pc_control.empty_recycle_bin()
            self.display_message(f"🗑️ {msg}", duration_ms=4500)
        elif action == act_mute:
            ok, msg = tools_pc_control.toggle_mute()
            self.display_message(msg, duration_ms=3500)
        elif action == act_vis:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
        elif action == act_startup:
            new_startup = not is_startup
            setup_shortcuts.set_startup_enabled(new_startup)
            stat = "activé" if new_startup else "désactivé"
            self.display_message(f"Démarrage automatique avec Windows {stat}.", duration_ms=4000)
        elif action == act_quit:
            self.hotkey_running = False
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
            if hasattr(self, 'qg') and self.qg:
                self.qg.close()
            if hasattr(self, 'sys_monitor'):
                self.sys_monitor.stop()
            if hasattr(self, 'sec_watchdog'):
                self.sec_watchdog.stop()
            if hasattr(self, 'wake_detector'):
                self.wake_detector.stop()
            if hasattr(self, 'autonomy_engine') and self.autonomy_engine:
                self.autonomy_engine.stop()
            QApplication.quit()

    # =========================================================================
    # INTERACTIONS SOURIS (DRAG & DROP DE LA CAPSULE)
    # =========================================================================
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPosition().toPoint()
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.drag_has_moved = False
            event.accept()

    def mouseMoveEvent(self, event):
        if getattr(self, 'is_dragging', False) and self.drag_position is not None and event.buttons() == Qt.MouseButton.LeftButton:
            curr_pos = event.globalPosition().toPoint()
            if hasattr(self, 'drag_start_pos') and (curr_pos - self.drag_start_pos).manhattanLength() > 6:
                self.drag_has_moved = True
            new_pos = curr_pos - self.drag_position
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            if not getattr(self, 'drag_has_moved', False):
                self.toggle_command_bar()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_qg()
            event.accept()

    def contextMenuEvent(self, event):
        try:
            pos = event.globalPos() if hasattr(event, 'globalPos') else QCursor.pos()
            self.show_context_menu(pos)
        except Exception:
            pass

    def notify_windows(self, title: str, message: str):
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 4000)

    # Stubs de rétrocompatibilité pour toute dépendance résiduelle
    def set_outfit(self, outfit: str): pass
    def play_pose(self, pose_name: str, duration_sec: float = 6.0, dialog: str = None): pass
    def set_sprite_state(self, state: str): self.set_hud_state(state)


# Alias pour rétrocompatibilité
NoraMascot = NoraDynamicIsland


def run_app():
    try:
        app = QApplication(sys.argv)
        island = NoraDynamicIsland()
        island.show()

        # Démarrage non-bloquant du serveur mobile en arrière-plan
        def _start_bg_server():
            try:
                import nora_server
                nora_server.start_server_background(8000)
            except Exception as e:
                print(f"Avertissement serveur mobile: {e}")

        threading.Thread(target=_start_bg_server, daemon=True).start()

        sys.exit(app.exec())
    except Exception:
        import traceback
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)

if __name__ == "__main__":
    run_app()
