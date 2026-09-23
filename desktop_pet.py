"""
Mascotte Animée de Bureau 'Nora' :
- Style Visuel : Zero Two (Darling in the Franxx) - Longs cheveux roses, cornes écarlates, fard rouge, uniforme Franxx
- Option A : Animations fluides (Synchronisation labiale bouche ouverte/fermée pendant la parole + clignements d'yeux naturels)
- Le QG de Nora : Mini-Dashboard visuel rétractable aux couleurs de Zero Two
- Moteur d'Auto-Amélioration & Prise d'Initiatives (accord préalable obligatoire)
- Navigation Web Autonome en direct avec Playwright
- Contrôle Total du PC : Volume sonore, Lancement d'applications, Verrouillage Windows, Corbeille
- Agent de Sécurité Dédié : Veille Windows Defender, surveillance du démarrage anti-malware et scan complet
- Surveillance Système en temps réel : Alertes RAM, Disque, Batterie et Nouveaux Téléchargements
- Raccourci Clavier Global 'Ctrl + Alt + N' : Ouvre et réveille Nora instantanément où que vous soyez sur Windows
- Démarrage automatique configurable avec Windows (shell:startup)
- Mode Mains-Libres 'Dis Nora' / 'Hey Nora' (Détection vocale continue sur le micro actif)
"""
import sys
import os
import io

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
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"Erreur de démarrage Nora:\n\n{err_text[:500]}", "Nora Copilote - Diagnostic", 0x10)
    except Exception:
        pass

sys.excepthook = _global_exception_handler

import math
import time
import random
import threading
import ctypes
from ctypes import wintypes
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMenu, QSystemTrayIcon
)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QCursor, QFont, QIcon, QTransform

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "mascot_assets"

import voice_engine
import mascot_assets
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
import nora_autonomous_life
from wake_word_listener import WakeWordDetector



class NoraBridge(QObject):
    """Signaux pour la communication sécurisée entre les threads et l'interface PyQt6."""
    update_bubble = pyqtSignal(str)
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
    outfit_changed = pyqtSignal(str)
    gaming_mode_changed = pyqtSignal(bool)
    screen_vision_requested = pyqtSignal(str)
    swarm_event = pyqtSignal(str, int, str, int)

class NoraMascot(QWidget):
    def __init__(self):
        super().__init__()

        # Vérifier et générer les assets Zero Two, l'icône .ico et le raccourci Bureau
        mascot_assets.generate_all_zero_two_assets()
        sound_effects.generate_chimes_if_missing()
        setup_shortcuts.create_desktop_shortcut()

        # Charger la tenue sauvegardée
        self.current_outfit = memory_manager.get_current_outfit()
        mascot_assets.set_active_outfit(self.current_outfit)

        # Préchauffage du clonage vocal Zero Two RVC sur RTX 4080
        try:
            import voice_cloning
            voice_cloning.warmup_in_background()
        except Exception:
            pass

        self.bridge = NoraBridge()
        self.bridge.update_bubble.connect(self.display_message)
        self.bridge.set_state.connect(self.set_sprite_state)
        self.bridge.mission_finished.connect(self.on_mission_finished)
        self.bridge.chat_response.connect(self.on_chat_response)
        self.bridge.wake_triggered.connect(self.on_wake_word_heard)
        self.bridge.start_speech.connect(self.on_speech_started)
        self.bridge.stop_speech.connect(self.on_speech_stopped)
        self.bridge.hotkey_pressed.connect(self.on_hotkey_pressed)
        self.bridge.system_alert.connect(self.on_system_alert)
        self.bridge.security_alert.connect(self.on_security_alert)
        self.bridge.open_qg.connect(self.toggle_qg)
        self.bridge.outfit_changed.connect(self.set_outfit)
        self.bridge.swarm_event.connect(self.on_swarm_event_received)
        self.bridge.gaming_mode_changed.connect(self.on_gaming_mode_changed)
        self.bridge.screen_vision_requested.connect(self.trigger_screen_vision)

        self.drag_position = QPoint()
        self.is_dragging = False
        self._pixmap_cache = {}
        self.preload_all_sprites()
        self.current_state = "idle"
        self.is_mission_running = False
        self.hands_free_enabled = False
        self.system_alerts_enabled = True

        # Moteur de Vie Autonome & Corps Animé (Direction, Tangage, Respiration)
        self.life_engine = nora_autonomous_life.life_engine
        self.facing_direction = 1  # 1 = face droite, -1 = face gauche
        self.is_walking = False
        self.walk_target_x = 0
        self.walk_speed = 2
        self.walk_step_counter = 0

        self.init_ui()
        self.init_system_tray()
        self.init_animations()
        self.init_wake_word_detector()
        self.init_system_monitor()
        self.init_security_watchdog()
        self.init_global_hotkey()
        self.init_qg()
        self.init_autonomous_life()

        # Salutation personnalisée au démarrage avec synchronisation labiale
        QTimer.singleShot(800, self.welcome_greeting)
        # Ouverture automatique de l'espace de contrôle QG au démarrage (100% indépendant)
        QTimer.singleShot(1200, self.open_qg_initial)

    def open_qg_initial(self):
        """Ouvre le QG au lancement comme un espace de contrôle indépendant et fixe."""
        if hasattr(self, 'qg'):
            self.qg.show_independent()

    def preload_all_sprites(self):
        """Précharge et redimensionne tous les sprites plein corps en RAM avec miroir gauche/droite pour un affichage 0 ms."""
        outfits = ["franxx", "school", "hoodie", "cyberpunk", "commander"]
        states = [
            "idle", "idle_standing", "idle_arms_crossed", "idle_wave", "idle_thinking",
            "idle_sitting", "idle_work_hologram", "idle_gaming", "alert_shield",
            "blink", "talk_open", "talk_closed", "listen", "work"
        ]
        # Ajout des frames de marche et de course articulées
        for i in range(1, 9):
            states.append(f"walk_{i}")
        for i in range(1, 5):
            states.append(f"run_{i}")

        for o in outfits:
            for s in states:
                # 1. Vérifier dans le sous-dossier de la tenue (mascot_assets/<outfit>/<s>.png)
                p = ASSETS_DIR / o / f"{s}.png"
                if not p.exists():
                    p = ASSETS_DIR / f"nora_{o}_{s}.png"
                if not p.exists():
                    p = ASSETS_DIR / f"nora_{s}.png"
                if not p.exists() and s.startswith("walk_"):
                    p = ASSETS_DIR / o / "idle_standing.png"
                if not p.exists():
                    p = ASSETS_DIR / "nora_idle.png"

                if p.exists():
                    pix = QPixmap(str(p))
                    if not pix.isNull():
                        pix_norm = pix.scaled(
                            250, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                        )
                        # Normal (droite)
                        self._pixmap_cache[(o, s, 1)] = pix_norm
                        # Miroir (gauche)
                        mirrored = pix_norm.transformed(QTransform().scale(-1, 1), Qt.TransformationMode.SmoothTransformation)
                        self._pixmap_cache[(o, s, -1)] = mirrored
                        # Compatibilité
                        self._pixmap_cache[(o, s)] = pix_norm

    def get_cached_pixmap(self, outfit: str, state: str, direction: int = 1):
        """Récupère instantanément le sprite mis en cache mémoire selon l'orientation du corps."""
        dir_key = -1 if direction == -1 else 1
        pix = self._pixmap_cache.get((outfit, state, dir_key))
        if pix:
            return pix
        pix = self._pixmap_cache.get((outfit, state))
        if pix:
            return pix
        # Fallbacks intelligents
        return (
            self._pixmap_cache.get((outfit, "idle_standing", dir_key)) or
            self._pixmap_cache.get((outfit, "idle", dir_key)) or
            self._pixmap_cache.get(("franxx", state, dir_key)) or
            self._pixmap_cache.get(("franxx", "idle_standing", dir_key)) or
            self._pixmap_cache.get(("franxx", "idle"))
        )

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(260)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Bulle de dialogue style Manga / Comic (Apparaît uniquement quand Nora s'exprime)
        self.bubble_container = QWidget()
        bubble_layout = QVBoxLayout(self.bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(0)
        bubble_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bubble_label = QLabel("")
        self.bubble_label.setWordWrap(True)
        self.bubble_label.setMaximumWidth(225)
        self.bubble_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bubble_label.setStyleSheet("""
            background-color: rgba(15, 23, 42, 0.95);
            color: #ffffff;
            border: 2px solid #fb7185;
            border-radius: 14px;
            padding: 8px 12px;
            font-size: 11.5px;
            font-weight: 600;
        """)
        bubble_layout.addWidget(self.bubble_label)

        # Flèche manga de la bulle vers la tête de Nora
        self.bubble_tail = QLabel("▼")
        self.bubble_tail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bubble_tail.setStyleSheet("color: #fb7185; font-size: 10px; margin-top: -3px; border: none; background: transparent;")
        bubble_layout.addWidget(self.bubble_tail)

        main_layout.addWidget(self.bubble_container)
        self.bubble_container.hide()  # Cachée par défaut pour un personnage 100% épuré

        # Timer pour masquer la bulle automatiquement
        self.bubble_hide_timer = QTimer(self)
        self.bubble_hide_timer.setSingleShot(True)
        self.bubble_hide_timer.timeout.connect(self.hide_speech_bubble)

        # 2. Sprite animé de Nora (Zero Two)
        self.avatar_label = QLabel()
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.set_sprite_state("idle")
        main_layout.addWidget(self.avatar_label)

        self.setLayout(main_layout)

        # Position initiale : bord inférieur droit de l'écran principal
        screen = QApplication.primaryScreen().availableGeometry()
        pos_x = max(100, screen.right() - 280)
        pos_y = max(100, screen.bottom() - 320)
        self.move(pos_x, pos_y)

    # =================================================================
    # INTÉGRATION WINDOWS SYSTEM TRAY & NOTIFICATIONS
    # =================================================================
    def init_system_tray(self):
        """Place l'icône de Zero Two dans la zone de notification près de l'horloge Windows."""
        self.tray_icon = QSystemTrayIcon(self)
        ico_path = ASSETS_DIR / "nora.ico"
        if not ico_path.exists():
            ico_path = ASSETS_DIR / "nora_idle.png"
        self.tray_icon.setIcon(QIcon(str(ico_path)))
        self.tray_icon.setToolTip("🌸 Nora - Votre Copilote Zero Two")

        # Clic sur l'icône de la barre des tâches pour afficher/masquer
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # Clic gauche
            self.toggle_mascot_visibility()
        elif reason == QSystemTrayIcon.ActivationReason.Context:  # Clic droit
            self.show_context_menu(QCursor.pos())

    def toggle_mascot_visibility(self):
        """Bascule la visibilité de Nora et de son QG en 1 clic."""
        if self.isVisible():
            self.hide()
            if hasattr(self, 'qg') and self.qg.isVisible():
                self.qg.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def notify_windows(self, title: str, message: str, is_warning: bool = False):
        """Affiche une notification native Windows (Toast/Bulle près de l'horloge)."""
        if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
            msg_icon = QSystemTrayIcon.MessageIcon.Warning if is_warning else QSystemTrayIcon.MessageIcon.Information
            self.tray_icon.showMessage(f"🌸 {title}", message, msg_icon, 4500)

    # =================================================================
    # ANIMATIONS OPTION A : CLIGNEMENT NATUREL + LIP-SYNC
    # =================================================================
    def init_animations(self):
        # 1. Flottement doux vertical (30 FPS sinusoïdal organique)
        self.float_start_time = time.time()
        self.float_timer = QTimer(self)
        self.float_timer.timeout.connect(self.float_animation_step)
        self.float_timer.start(33)

        # 2. Clignements d'yeux naturels aléatoires (Option A)
        self.blink_timer = QTimer(self)
        self.blink_timer.setSingleShot(True)
        self.blink_timer.timeout.connect(self.trigger_blink)
        self.schedule_next_blink()

        # 3. Synchronisation labiale fluide (Option A)
        self.is_speaking_now = False
        self.lip_phase = 0
        self.lip_timer = QTimer(self)
        self.lip_timer.timeout.connect(self.lip_sync_step)

    def float_animation_step(self):
        """Mouvement corporel vivant : respiration sinusoïdale organique et micro-mouvements."""
        if getattr(self, 'is_walking', False):
            return  # La marche gère son propre cycle corporel dynamique
        if self.current_state in ["idle", "talk_open", "talk_closed", "listen", "work"]:
            elapsed = time.time() - self.float_start_time
            sin_breathe = math.sin(elapsed * 2.1)
            offset = int(sin_breathe * 3.5)
            # Respiration corporelle : étirement doux (squash & stretch de 2.5%)
            breathe_h = int(220 * (1.0 + 0.025 * sin_breathe))
            base_pix = self.get_cached_pixmap(self.current_outfit, self.current_state, getattr(self, 'facing_direction', 1))
            if base_pix:
                scaled_pix = base_pix.scaled(220, breathe_h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.avatar_label.setPixmap(scaled_pix)
            self.avatar_label.setContentsMargins(0, 4 + offset, 0, 4 - offset)

    def schedule_next_blink(self):
        """Planifie le prochain clignement naturel des yeux entre 3 et 5.5 secondes."""
        delay = random.randint(3000, 5500)
        self.blink_timer.start(delay)

    def trigger_blink(self):
        """Cligne des yeux si elle est au repos et ne parle pas."""
        if self.current_state == "idle" and not self.is_speaking_now:
            self.set_sprite_state("blink")
            QTimer.singleShot(150, self.finish_blink)
        else:
            self.schedule_next_blink()

    def finish_blink(self):
        """Retour aux yeux ouverts après le clignement."""
        if self.current_state == "blink" and not self.is_speaking_now:
            self.set_sprite_state("idle")
        self.schedule_next_blink()

    def on_speech_started(self):
        """Déclenché au tout début de la voix de synthèse."""
        self.is_speaking_now = True
        self.lip_phase = 0
        self.set_sprite_state("talk_open")
        self.lip_timer.start(135)
        # Maintenir la bulle manga visible tant que Nora parle
        if hasattr(self, 'bubble_hide_timer'):
            self.bubble_hide_timer.stop()
        if hasattr(self, 'bubble_container'):
            self.bubble_container.show()

    def lip_sync_step(self):
        """Alterne la bouche ouverte et entrouverte pendant l'articulation."""
        if not self.is_speaking_now:
            self.lip_timer.stop()
            return
        self.lip_phase = 1 - self.lip_phase
        next_state = "talk_open" if self.lip_phase == 0 else "talk_closed"
        self.set_sprite_state(next_state)

    def on_speech_stopped(self):
        """Déclenché dès que Nora a fini de prononcer sa phrase."""
        self.is_speaking_now = False
        self.lip_timer.stop()
        if not self.is_mission_running:
            self.set_sprite_state("idle")
        # Masquer automatiquement la bulle de dialogue 3.5s après la parole
        if hasattr(self, 'bubble_hide_timer'):
            self.bubble_hide_timer.start(3500)

    def hide_speech_bubble(self):
        """Masque la bulle de dialogue manga pour laisser le personnage pur et épuré."""
        if hasattr(self, 'bubble_container') and self.bubble_container.isVisible():
            self.bubble_container.hide()

    def display_message(self, text: str, duration_ms: int = 6500):
        """Affiche un message dans la bulle manga au-dessus de Nora et planifie sa disparition."""
        if not text:
            self.hide_speech_bubble()
            return
        self.bubble_label.setText(text)
        self.bubble_label.adjustSize()
        if hasattr(self, 'bubble_container'):
            self.bubble_container.show()
        if hasattr(self, 'bubble_hide_timer'):
            self.bubble_hide_timer.stop()
            if duration_ms > 0:
                self.bubble_hide_timer.start(duration_ms)

    def speak_nora(self, text: str, on_finished=None, force: bool = False):
        """Fait parler Nora avec synchronisation labiale et animation."""
        # En mode Gaming, Nora reste silencieuse pour respecter l'audio du jeu (Ne Pas Déranger)
        if gaming_mode.is_gaming_mode() and not force:
            if on_finished:
                QTimer.singleShot(100, on_finished)
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

    def set_outfit(self, outfit: str):
        """Change la tenue de Zero Two en temps réel et met à jour les sprites."""
        if outfit not in ["franxx", "school", "hoodie", "cyberpunk", "commander"]:
            outfit = "franxx"
        self.current_outfit = outfit
        memory_manager.set_current_outfit(outfit)
        mascot_assets.set_active_outfit(outfit)
        self.set_sprite_state(self.current_state)
        if hasattr(self, 'qg') and self.qg:
            self.qg.update_outfit_buttons(outfit)

    def on_gaming_mode_changed(self, active: bool):
        """Synchronise l'interface quand le mode gaming change d'état."""
        if hasattr(self, 'qg') and self.qg:
            self.qg.update_gaming_ui()

    def set_sprite_state(self, state: str):
        """Met à jour le sprite affiché instantanément depuis le cache RAM avec orientation."""
        self.current_state = state
        pix = self.get_cached_pixmap(self.current_outfit, state, getattr(self, 'facing_direction', 1))
        if pix:
            self.avatar_label.setPixmap(pix)

    def welcome_greeting(self):
        msg = memory_manager.get_welcome_message()
        self.display_message(msg)
        self.speak_nora(msg)

    # =================================================================
    # MOTEUR DE VIE AUTONOME & DÉPLACEMENT LIBRE (ROAMING)
    # =================================================================
    def init_autonomous_life(self):
        """Initialise la boucle de déplacement autonome (balade) et le cycle de vie."""
        # 1. Timer de marche fluide (30 FPS)
        self.walk_timer = QTimer(self)
        self.walk_timer.timeout.connect(self.walk_step)
        self.walk_timer.start(35)

        # 2. Timer de décisions de vie autonome (toutes les 4 secondes)
        self.life_timer = QTimer(self)
        self.life_timer.timeout.connect(self.check_autonomous_life)
        self.life_timer.start(4000)

        # 3. Première balade visible 4.5 secondes après le lancement
        QTimer.singleShot(4500, self.initial_autonomous_walk)

    def initial_autonomous_walk(self):
        """Déclenche une première balade visible peu après le démarrage."""
        if getattr(self, 'is_walking', False) or getattr(self, 'is_dragging', False):
            return
        screen = QApplication.primaryScreen().availableGeometry()
        min_x = screen.left() + 20
        max_x = max(min_x + 100, screen.right() - self.width() - 20)
        current_x = self.x()
        if current_x > (min_x + max_x) / 2:
            target_x = max(min_x, current_x - 280)
        else:
            target_x = min(max_x, current_x + 280)
        self.start_walking_to(target_x, speed=3, announcement="Je commence ma petite balade sur votre écran, Maverick !")

    def start_walking_to(self, target_x: int, speed: int = 3, announcement: str = None):
        """Lance une balade autonome vers une coordonnée horizontale."""
        if getattr(self, 'is_dragging', False) or self.is_mission_running:
            return
        self.walk_target_x = target_x
        self.walk_speed = max(1, speed)
        self.is_walking = True
        if announcement:
            self.display_message(announcement)

    def walk_step(self):
        """Effectue un pas fluide vers la destination de balade avec corps articulé animé."""
        if not getattr(self, 'is_walking', False) or getattr(self, 'is_dragging', False) or self.is_mission_running:
            return

        current_pos = self.pos()
        dx = self.walk_target_x - current_pos.x()

        # Destination atteinte
        if abs(dx) <= abs(self.walk_speed) + 2:
            self.move(self.walk_target_x, current_pos.y())
            self.is_walking = False
            self.set_sprite_state("idle")
            return

        # Mise à jour de l'orientation du corps selon la direction de marche
        if dx > 1:
            self.facing_direction = 1
        elif dx < -1:
            self.facing_direction = -1

        # Translation
        step = self.walk_speed if dx > 0 else -self.walk_speed
        new_x = current_pos.x() + step
        self.move(new_x, current_pos.y())

        # Cycle de marche complet articulé (8 frames plein corps, jambes & bras)
        self.walk_step_counter += 1
        cycle = self.walk_step_counter * 0.35
        # Rebond vertical des pieds/jambes
        stride_bob = int(abs(math.sin(cycle)) * 6) - 2
        # Balancement angulaire du torse (±3.5 degrés)
        stride_tilt = math.sin(cycle) * (3.5 if self.facing_direction == 1 else -3.5)

        # Sélection de la frame de marche articulée (walk_1 à walk_8)
        walk_frame = ((self.walk_step_counter // 2) % 8) + 1
        state_name = f"walk_{walk_frame}"
        base_pix = self.get_cached_pixmap(self.current_outfit, state_name, self.facing_direction)
        if not base_pix:
            base_pix = self.get_cached_pixmap(self.current_outfit, "idle", self.facing_direction)

        if base_pix:
            transform = QTransform().rotate(stride_tilt)
            t_pix = base_pix.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            self.avatar_label.setPixmap(t_pix)

        self.avatar_label.setContentsMargins(0, 4 + stride_bob, 0, 4 - stride_bob)

    def check_autonomous_life(self):
        """Interroge le moteur de vie autonome pour déclencher balades, pensées ou pauses."""
        if getattr(self, 'is_walking', False) or getattr(self, 'is_dragging', False) or self.is_mission_running or getattr(self, 'is_speaking_now', False):
            return

        # En mode Gaming, Nora respecte l'immersion et ne se balade pas
        if gaming_mode.is_gaming_mode():
            return

        screen = QApplication.primaryScreen().availableGeometry()
        min_x = screen.left() + 20
        max_x = max(min_x + 100, screen.right() - self.width() - 20)

        action = self.life_engine.decide_next_action(self.x(), min_x, max_x)
        action_type = action.get("type")

        if action_type == "WALK":
            self.start_walking_to(action["target_x"], action.get("speed", 2), action.get("bubble"))
        elif action_type in ["THOUGHT", "WATER", "MAINTENANCE"]:
            if action.get("bubble"):
                self.display_message(action["bubble"])
            if action.get("speech"):
                self.speak_nora(action["bubble"])
        elif action_type == "SLEEP":
            self.display_message(action["bubble"])
            self.set_sprite_state("blink")
        elif action_type == "WAKE_UP":
            self.display_message(action["bubble"])
            self.set_sprite_state("idle")
            if action.get("speech"):
                self.speak_nora(action["bubble"])

    def toggle_roaming_mode(self):
        """Active ou désactive la balade libre de Nora."""
        active = self.life_engine.toggle_roaming()
        if not active:
            self.is_walking = False
            self.set_sprite_state("idle")
            self.display_message("Mode balade désactivé. Je reste ici, Maverick.")
        else:
            self.display_message("Mode balade activé ! Je me dégourdis les jambes, Maverick.")

    def force_nap_mode(self):
        """Met Nora en sieste paisible."""
        self.is_walking = False
        self.life_engine.is_sleeping = True
        self.set_sprite_state("blink")
        self.display_message("Je fais une petite sieste discrète, Maverick. Zzz... 🌙")

    def read_learning_note(self):
        """Fait lire à haute voix ou afficher une note du carnet."""
        thought = self.life_engine.generate_spontaneous_thought("day")
        self.display_message(thought["text"])

    # =================================================================
    # VISION D'ÉCRAN MULTIMODALE & LE QG DE NORA
    # =================================================================
    def trigger_screen_vision(self, prompt_text: str = ""):
        """Capture l'écran et l'analyse via Gemini 3.6 Flash avec la personnalité de Zero Two."""
        if self.is_mission_running:
            self.display_message("⏳ Je suis déjà occupée sur une mission Maverick, un instant s'il vous plaît.")
            return

        self.set_sprite_state("work")
        self.display_message("👁️ J'analyse votre écran, Maverick... Laissez-moi regarder.")
        sound_effects.play_wake_chime()

        def vision_worker():
            res = tools_vision.analyze_screen_with_gemini(prompt_text)
            speech = res.get("speech", "")
            self.bridge.update_bubble.emit(f"👁️ {speech}")
            self.speak_nora(speech, on_finished=lambda: self.bridge.set_state.emit("idle"))

        threading.Thread(target=vision_worker, daemon=True).start()

    def init_qg(self):
        self.qg = qg_dashboard.QGDashboard(parent_mascot=self)
        self.qg.initiative_accepted.connect(self.on_initiative_accepted)
        self.qg.initiative_refused.connect(self.on_initiative_refused)
        self.qg.action_requested.connect(self.on_qg_action_requested)
        self.qg.outfit_changed.connect(self.set_outfit)
        self.qg.gaming_mode_toggled.connect(self.on_qg_gaming_toggled)
        self.qg.ram_boost_requested.connect(self.on_qg_ram_boost)
        self.qg.screen_vision_requested.connect(lambda: self.trigger_screen_vision(""))
        self.qg.voice_cloning_toggled.connect(self.on_qg_voice_cloning_toggled)

    def on_qg_gaming_toggled(self, active: bool):
        if active:
            msg = "🎮 Mode Gaming ACTIVÉ ! Silence radio et performances maximales, Maverick."
            self.display_message(msg)
            self.speak_nora(msg, force=True)
        else:
            msg = "✨ Mode Gaming DÉSACTIVÉ ! Je reprends les alertes normales, Maverick."
            self.display_message(msg)
            self.speak_nora(msg, force=True)

    def on_qg_voice_cloning_toggled(self, active: bool):
        stat = "activée" if active else "désactivée"
        self.display_message(f"🎙️ Voix de Nora {stat} (RTX 4080) !")
        self.speak_nora(f"Ma voix Nora est maintenant {stat}, Maverick.", force=True)

    def on_qg_ram_boost(self):
        sound_effects.play_wake_chime()

    def toggle_qg(self):
        if hasattr(self, 'qg'):
            self.qg.toggle_independent()

    def on_initiative_accepted(self, init_id: str):
        self.set_sprite_state("work")
        res = nora_initiatives.execute_accepted_initiative(init_id)
        self.display_message(res)
        sound_effects.play_success_chime()
        self.speak_nora(res, on_finished=lambda: self.set_sprite_state("idle"))

    def on_initiative_refused(self, init_id: str):
        res = nora_initiatives.refuse_initiative(init_id)
        self.display_message(res)
        self.speak_nora(res)

    def on_qg_action_requested(self, action_name: str):
        if action_name == "security_scan":
            self.run_security_scan_action()
        elif action_name == "organize_downloads":
            self.execute_mission("Range mon dossier Téléchargements en triant tout par catégories.")
        elif action_name == "web_search":
            self.start_voice_input()
        elif action_name == "smart_home_panel":
            self.show_smart_home_menu()

    def show_smart_home_menu(self):
        """Ouvre un menu interactif pour piloter la maison et le pont Philips Hue."""
        import agent_home
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0f172a;
                color: #f1f5f9;
                border: 2px solid #818cf8;
                border-radius: 10px;
                padding: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: 600;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #4338ca;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #334155;
                margin: 4px 8px;
            }
        """)

        is_paired = agent_home.smart_home.is_hue_paired()
        hue_title = "🏠 Pont Philips Hue : Connecté 💖" if is_paired else "🏠 Pont Hue : Détecté (192.168.1.29) 🟡"
        act_title = menu.addAction(hue_title)
        act_title.setEnabled(False)
        menu.addSeparator()

        act_salon = menu.addAction("💡 Basculer Lumières Salon")
        act_chambre = menu.addAction("💡 Basculer Lumières Chambre")
        act_zero_two = menu.addAction("🌸 Ambiance Zero Two (Rose Pastel)")
        menu.addSeparator()
        act_volets = menu.addAction("🪟 Fermer / Ouvrir Volets")
        act_night = menu.addAction("🌙 Mode Nuit (Tout Éteindre)")
        menu.addSeparator()
        act_status = menu.addAction("📊 État de la Maison")
        act_pair = menu.addAction("🔗 Associer le Pont Philips Hue...")

        action = menu.exec(QCursor.pos())
        if action == act_salon:
            lights = agent_home.smart_home.state.get("lights", {}).get("salon", {})
            new_on = not lights.get("on", False)
            ok, msg = agent_home.smart_home.set_light("salon", on=new_on)
            self.display_message(msg)
            self.speak_nora(msg)
        elif action == act_chambre:
            lights = agent_home.smart_home.state.get("lights", {}).get("chambre", {})
            new_on = not lights.get("on", False)
            ok, msg = agent_home.smart_home.set_light("chambre", on=new_on)
            self.display_message(msg)
            self.speak_nora(msg)
        elif action == act_zero_two:
            ok, msg = agent_home.smart_home.activate_zero_two_ambiance()
            self.display_message(msg)
            self.speak_nora(msg)
        elif action == act_volets:
            cov = agent_home.smart_home.state.get("covers", {}).get("salon", "ouvert")
            new_state = (cov != "ouvert")
            ok, msg = agent_home.smart_home.set_cover("all", open_state=new_state)
            self.display_message(msg)
            self.speak_nora(msg)
        elif action == act_night:
            ok, msg = agent_home.smart_home.activate_night_mode()
            self.display_message(msg)
            self.speak_nora(msg)
        elif action == act_status:
            rep = agent_home.smart_home.get_status_report()
            self.display_message(rep)
            self.speak_nora("Voici l'état des équipements de la maison, Maverick.")
        elif action == act_pair:
            self.display_message("Appuyez sur le gros bouton rond au centre de votre pont Philips Hue (192.168.1.29)...")
            self.speak_nora("Appuyez sur le gros bouton rond au centre de votre pont Hue, Maverick. Je patiente...")
            ok, msg = agent_home.smart_home.pair_hue_bridge()
            self.display_message(msg)
            self.speak_nora(msg)

    # =================================================================
    # SURVEILLANCE SYSTÈME & ALERTES EN DIRECT
    # =================================================================
    def init_system_monitor(self):
        """Démarre le module de surveillance matérielle et des téléchargements."""
        def on_sys_alert(category, title, msg, speak):
            self.bridge.system_alert.emit(category, title, msg, speak)

        self.sys_monitor = system_monitor.SystemMonitor(on_alert_callback=on_sys_alert)
        self.sys_monitor.start()

    def on_system_alert(self, category: str, title: str, msg: str, speak: bool):
        """Réceptionne une alerte matérielle ou un nouveau téléchargement."""
        if not self.system_alerts_enabled:
            return

        icon = "⚠️" if category == "warning" else "📥"
        self.display_message(f"{icon} {title} :\n{msg}")

        if speak and not self.is_speaking_now and not self.is_mission_running:
            sound_effects.play_wake_chime()
            self.speak_nora(msg)

    def show_system_health_report(self):
        """Énonce et affiche un bilan complet de l'ordinateur."""
        report = system_monitor.get_system_health_report()
        self.display_message(f"📊 Bilan Santé du PC :\n{report}")
        self.speak_nora(report)

    # =================================================================
    # AGENT DE SÉCURITÉ DU PC (LE GARDIEN)
    # =================================================================
    def init_security_watchdog(self):
        """Démarre le gardien de sécurité pour surveiller Defender et le démarrage."""
        def on_sec_alert(title, msg, is_critical):
            self.bridge.security_alert.emit(title, msg, is_critical)

        self.sec_watchdog = agent_security.SecurityWatchdog(on_alert=on_sec_alert)
        self.sec_watchdog.start()

    def on_security_alert(self, title: str, msg: str, is_critical: bool):
        """Déclenché si Defender est désactivé ou si un nouveau programme s'ajoute au démarrage."""
        self.display_message(f"🚨 {title} :\n{msg}")
        sound_effects.play_wake_chime()
        if not self.is_speaking_now:
            self.speak_nora(msg)

    def run_security_scan_action(self):
        """Lance un scan de sécurité complet sur demande."""
        self.set_sprite_state("work")
        self.display_message("🛡️ L'Agent de Sécurité analyse le système...")
        sound_effects.play_wake_chime()

        def scan_worker():
            scan = agent_security.run_security_scan()
            self.bridge.update_bubble.emit(f"🛡️ Score de Sécurité : {scan['score']}/100\n{scan['speech']}")
            self.speak_nora(scan["speech"], on_finished=lambda: self.bridge.set_state.emit("idle"))

        threading.Thread(target=scan_worker, daemon=True).start()

    # =================================================================
    # RACCOURCI CLAVIER GLOBAL (CTRL + ALT + N)
    # =================================================================
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
        """Invoque Nora instantanément lors de l'appui sur Ctrl+Alt+N."""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.raise_()
        self.activateWindow()

        sound_effects.play_wake_chime()
        self.set_sprite_state("listen")
        self.display_message("✨ Oui Maverick, je vous écoute.")
        self.start_voice_input()

    # =================================================================
    # MAINS-LIBRES : "DIS NORA"
    # =================================================================
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
        """Active ou désactive l'écoute continue 'Dis Nora'."""
        self.hands_free_enabled = not self.hands_free_enabled
        if hasattr(self, 'qg') and self.qg:
            self.qg.update_handsfree_button()

        if self.hands_free_enabled:
            self.wake_detector.start()
            sound_effects.play_wake_chime()
            self.display_message("🎧 Mode Mains-Libres ACTIF !\nDis simplement 'Dis Nora' ou 'Hey Nora' à voix haute.")
        else:
            self.wake_detector.stop()
            self.display_message("🎧 Mode Mains-Libres désactivé.")

    def on_wake_word_heard(self, command: str):
        """Déclenché automatiquement lorsque 'Dis Nora' est prononcé dans la pièce."""
        if self.is_mission_running:
            return

        if command:
            self.process_user_message(command)
        else:
            self.set_sprite_state("listen")
            self.display_message("✨ Oui Maverick, je vous écoute.")
            self.start_voice_input()

    # =================================================================
    # GESTION DES ENTRÉES : DISCUSSION VS MISSION
    # =================================================================
    def submit_text_input(self):
        if hasattr(self, 'input_field'):
            text = self.input_field.text().strip()
            if text:
                self.input_field.clear()
                self.process_user_message(text)

    def start_voice_input(self):
        if self.is_mission_running:
            return

        def record_thread():
            self.bridge.set_state.emit("listen")
            self.bridge.update_bubble.emit("🎙️ Je vous écoute Maverick... Vous pouvez parler.")
            spoken = voice_engine.listen_microphone()
            if spoken:
                self.process_user_message(spoken)
            else:
                self.bridge.set_state.emit("idle")
                self.bridge.update_bubble.emit("Je n'ai pas bien compris Maverick. Cliquez sur 🎙️ ou écrivez-moi.")

        threading.Thread(target=record_thread, daemon=True).start()

    def process_user_message(self, user_text: str):
        if self.is_mission_running:
            self.display_message("⏳ Je suis déjà occupée sur une mission Maverick, un instant s'il vous plaît.")
            return

        def analyze_thread():
            intent, chat_reply = nora_brain.analyze_intent_and_respond(user_text)
            if intent == "OPEN_QG":
                self.bridge.open_qg.emit()
                self.bridge.chat_response.emit(chat_reply)
            elif intent.startswith("OUTFIT:"):
                outfit_key = intent.split(":")[1]
                self.bridge.outfit_changed.emit(outfit_key)
                self.bridge.chat_response.emit(chat_reply)
            elif intent == "GAMING_ON":
                self.bridge.gaming_mode_changed.emit(True)
                self.bridge.chat_response.emit(chat_reply)
            elif intent == "GAMING_OFF":
                self.bridge.gaming_mode_changed.emit(False)
                self.bridge.chat_response.emit(chat_reply)
            elif intent == "BOOST_RAM":
                self.bridge.chat_response.emit(chat_reply)
            elif intent == "SCREEN_VISION":
                self.bridge.screen_vision_requested.emit(chat_reply)
            elif intent == "CHAT":
                self.bridge.chat_response.emit(chat_reply)
            else:
                self.execute_mission(user_text)

        threading.Thread(target=analyze_thread, daemon=True).start()

    def on_chat_response(self, reply_text: str):
        self.display_message(reply_text)
        self.speak_nora(reply_text)

    def execute_mission(self, mission_goal: str):
        self.is_mission_running = True
        self.bridge.set_state.emit("work")
        self.bridge.update_bubble.emit(f"⚙️ Mission : '{mission_goal[:35]}...'\nJe mobilise mes agents, Maverick.")
        
        sound_effects.play_wake_chime()
        self.speak_nora("C'est bien noté Maverick. Je lance mes agents pour s'en occuper.")

        def mission_worker():
            def step_callback(step_type, text):
                if step_type == "swarm":
                    self.bridge.update_bubble.emit(text)
                    self.bridge.swarm_event.emit("Essaim", 1, text, 96)
                else:
                    self.bridge.update_bubble.emit(f"⚙️ {text}")

            try:
                from mission_engine import run_autonomous_mission
                report = run_autonomous_mission(mission_goal, callback_step=step_callback)
                self.bridge.mission_finished.emit(report)
            except Exception as e:
                self.bridge.mission_finished.emit(f"Erreur : {str(e)}")

        threading.Thread(target=mission_worker, daemon=True).start()

    def on_swarm_event_received(self, agent: str, round_num: int, text: str, consensus: int):
        if hasattr(self, 'qg') and self.qg:
            self.qg.update_swarm_event(agent, round_num, text, consensus)

    def on_mission_finished(self, report: str):
        self.is_mission_running = False
        sound_effects.play_success_chime()

        summary_preview = "🎉 Mission accomplie à 100 % ! Tout a été terminé avec succès, Maverick."
        self.display_message(summary_preview)
        self.notify_windows("Mission Accomplie !", "Toutes les actions demandées ont été effectuées avec succès !")
        self.speak_nora("Mission accomplie Maverick ! Toutes les actions demandées ont été effectuées.")

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
                self.is_walking = False  # Pause la balade libre si Maverick déplace Nora
            new_pos = curr_pos - self.drag_position
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.walk_target_x = self.x()
            if not getattr(self, 'drag_has_moved', False):
                # Un clic direct sur Nora ouvre / ferme son QG de commande classique et esthétique
                self.toggle_qg()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_qg()
            event.accept()

    def contextMenuEvent(self, event):
        try:
            pos = event.globalPos() if hasattr(event, 'globalPos') else QCursor.pos()
            self.show_context_menu(pos)
        except Exception as e:
            print(f"[ContextMenu Error] {e}")

    def show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #475569;
                padding: 6px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #e11d48;
            }
        """)

        action_qg = menu.addAction("📊 Ouvrir / Rétracter le QG")
        action_voice = menu.addAction("🎙️ Parler au micro (Ctrl+Alt+N)")
        action_handsfree = menu.addAction("🎧 Activer / Désactiver Mains-Libres")
        action_vision = menu.addAction("👁️ Regarder mon Écran (Vision IA)")
        
        # Vie Autonome & Balade Libre
        menu.addSeparator()
        is_roaming = self.life_engine.roaming_enabled
        roam_label = "🚶 Désactiver la Balade Libre" if is_roaming else "🚶 Activer la Balade Libre"
        action_roam = menu.addAction(roam_label)
        action_walk_now = menu.addAction("🚶 Se balader maintenant")
        action_nap = menu.addAction("😴 Faire une sieste")
        action_read = menu.addAction("📖 Lire une note du carnet")
        menu.addSeparator()

        # Garde-Robe Zero Two
        outfit_menu = menu.addMenu("👗 Garde-Robe Zero Two")
        outfit_menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #475569;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #e11d48;
            }
        """)
        curr_outfit = memory_manager.get_current_outfit()
        act_franxx = outfit_menu.addAction("🚀 Pilote Franxx" + (" ✓" if curr_outfit == "franxx" else ""))
        act_school = outfit_menu.addAction("🎓 Écolière Sailor" + (" ✓" if curr_outfit == "school" else ""))
        act_hoodie = outfit_menu.addAction("🧸 Hoodie Doux" + (" ✓" if curr_outfit == "hoodie" else ""))
        act_cyberpunk = outfit_menu.addAction("⚡ Cyberpunk Techwear" + (" ✓" if curr_outfit == "cyberpunk" else ""))
        act_commander = outfit_menu.addAction("👑 Commandant Écarlate" + (" ✓" if curr_outfit == "commander" else ""))

        # Mode Gaming & RAM Boost
        menu.addSeparator()
        is_gaming = gaming_mode.is_gaming_mode()
        gaming_label = "🎮 Désactiver Mode Gaming" if is_gaming else "🎮 Activer Mode Gaming (Boost FPS)"
        action_gaming = menu.addAction(gaming_label)
        action_boost_ram = menu.addAction("⚡ Vider le cache RAM (Boost FPS)")

        # Clonage Vocal Zero Two RVC (RTX 4080)
        menu.addSeparator()
        is_vc_on = memory_manager.is_voice_cloning_enabled()
        vc_label = "🎙️ Voix Zero Two Clonnée (RTX 4080) " + ("[Activée ✓]" if is_vc_on else "[Désactivée]")
        action_toggle_vc = menu.addAction(vc_label)

        # Domotique & Philips Hue
        menu.addSeparator()
        action_smart_home = menu.addAction("🏠 Maison & Domotique (Philips Hue)...")

        menu.addSeparator()

        # Sécurité et Santé
        action_security = menu.addAction("🛡️ Scan de Sécurité Complet")
        action_health = menu.addAction("📊 Bilan Santé du PC")
        
        # Contrôles PC directs
        menu.addSeparator()
        vol_muted = False
        try:
            from pycaw.pycaw import AudioUtilities
            spk = AudioUtilities.GetSpeakers()
            if spk and hasattr(spk, 'EndpointVolume'):
                vol_muted = bool(spk.EndpointVolume.GetMute())
        except Exception:
            pass
        mute_label = "🔊 Rétablir le Son" if vol_muted else "🔇 Couper le Son"
        action_mute = menu.addAction(mute_label)
        action_clean_bin = menu.addAction("🗑️ Vider la Corbeille")
        action_lock = menu.addAction("🔒 Verrouiller le PC")

        # Alertes & Démarrage
        menu.addSeparator()
        alerts_text = "🔔 Désactiver Alertes PC" if self.system_alerts_enabled else "🔕 Activer Alertes PC"
        action_toggle_alerts = menu.addAction(alerts_text)

        is_startup = setup_shortcuts.is_startup_enabled()
        startup_text = "☑ Lancer au démarrage de Windows" if is_startup else "☐ Lancer au démarrage de Windows"
        action_startup = menu.addAction(startup_text)

        menu.addSeparator()
        action_clean = menu.addAction("🧹 Ranger mes Téléchargements")
        action_dup = menu.addAction("🔍 Isoler les doublons")
        menu.addSeparator()
        action_quit = menu.addAction("❌ Quitter Nora")

        action = menu.exec(global_pos)
        if action == action_qg:
            self.toggle_qg()
        elif action == action_voice:
            self.start_voice_input()
        elif action == action_handsfree:
            self.toggle_hands_free()
        elif action == action_vision:
            self.trigger_screen_vision("")
        elif action == action_roam:
            self.toggle_roaming_mode()
        elif action == action_walk_now:
            screen = QApplication.primaryScreen().availableGeometry()
            min_x = screen.left() + 20
            max_x = max(min_x + 100, screen.right() - self.width() - 20)
            import random
            target = random.randint(min_x, max_x)
            self.start_walking_to(target, speed=3, announcement="C'est parti pour une petite promenade sur votre écran, Maverick !")
        elif action == action_nap:
            self.force_nap_mode()
        elif action == action_read:
            self.read_learning_note()
        elif action == act_franxx:
            self.set_outfit("franxx")
            self.display_message("🚀 Tenue de Pilote Franxx enfilée, Maverick.")
        elif action == act_school:
            self.set_outfit("school")
            self.display_message("🎓 Tenue d'Écolière Sailor enfilée, Maverick.")
        elif action == act_hoodie:
            self.set_outfit("hoodie")
            self.display_message("🧸 Hoodie tout doux enfilé, Maverick.")
        elif action == act_cyberpunk:
            self.set_outfit("cyberpunk")
            self.display_message("⚡ Tenue Cyberpunk Techwear enfilée, Maverick !")
        elif action == act_commander:
            self.set_outfit("commander")
            self.display_message("👑 Manteau d'Officier Commandant Écarlate enfilé, Maverick !")
        elif action == action_gaming:
            new_state, msg = gaming_mode.toggle_gaming_mode()
            if hasattr(self, 'qg') and self.qg:
                self.qg.update_gaming_ui()
            self.display_message(msg)
            self.speak_nora(msg, force=True)
        elif action == action_boost_ram:
            count, freed = gaming_mode.optimize_ram_boost()
            msg = f"⚡ RAM Boostée ! {count} applications vidées ({freed} Mo libérés)."
            self.display_message(msg)
            self.speak_nora(msg, force=True)
        elif action == action_toggle_vc:
            new_state = not is_vc_on
            memory_manager.set_voice_cloning_enabled(new_state)
            stat = "activée" if new_state else "désactivée"
            self.display_message(f"🎙️ Voix de Nora {stat} (accélérée par RTX 4080) !")
            if hasattr(self, 'qg') and self.qg:
                self.qg.update_vc_ui()
            self.speak_nora(f"Ma voix Nora est maintenant {stat}, Maverick.", force=True)
        elif action == action_smart_home:
            self.show_smart_home_menu()
        elif action == action_security:
            self.run_security_scan_action()
        elif action == action_health:
            self.show_system_health_report()
        elif action == action_mute:
            ok, msg = tools_pc_control.toggle_mute()
            self.display_message(msg)
        elif action == action_clean_bin:
            ok, msg = tools_pc_control.empty_recycle_bin()
            self.display_message(f"🗑️ {msg}")
            self.speak_nora(msg)
        elif action == action_lock:
            tools_pc_control.lock_workstation()
        elif action == action_toggle_alerts:
            self.system_alerts_enabled = not self.system_alerts_enabled
            stat = "activées" if self.system_alerts_enabled else "désactivées"
            self.display_message(f"🔔 Les alertes système sont maintenant {stat}.")
        elif action == action_startup:
            new_startup = not is_startup
            setup_shortcuts.set_startup_enabled(new_startup)
            if new_startup:
                self.display_message("🚀 Nora se lancera désormais automatiquement à l'allumage de Windows !")
            else:
                self.display_message("Démarrage automatique au lancement de Windows désactivé.")
        elif action == action_clean:
            self.execute_mission("Réorganise mon dossier Téléchargements en triant tout par catégories.")
        elif action == action_dup:
            self.execute_mission("Scanne mon dossier Téléchargements et isole les doublons.")
        elif action == action_quit:
            self.hotkey_running = False
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
            if hasattr(self, 'qg'):
                self.qg.close()
            if hasattr(self, 'sys_monitor'):
                self.sys_monitor.stop()
            if hasattr(self, 'sec_watchdog'):
                self.sec_watchdog.stop()
            if hasattr(self, 'wake_detector'):
                self.wake_detector.stop()
            QApplication.quit()

def run_app():
    # Démarrer le serveur API mobile en arrière-plan pour le smartphone
    try:
        import nora_server
        nora_server.start_server_background(8000)
    except Exception as e:
        print(f"Avertissement serveur mobile: {e}")

    app = QApplication(sys.argv)
    mascot = NoraMascot()
    mascot.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
