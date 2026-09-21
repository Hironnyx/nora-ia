"""
Serveur API REST & Streaming Asynchrone de Nora pour Mobile & Réseau Local :
- Permet à l'application Android (smartphone/tablette) de communiquer avec Nora
- Distribution dynamique des capacités (/api/capabilities) : toute nouveauté ajoutée sur PC apparaît automatiquement sur le smartphone sans réinstaller l'APK !
- Synthèse et streaming audio de la voix Zero Two (RTX 4080)
- Pilotage direct de la domotique (Philips Hue sur 192.168.1.29)
- Distribution des sprites HD de Zero Two (3 tenues, expressions)
- Compatible Wi-Fi local (http://192.168.1.183:8000) et accès distant sécurisé (Tailscale)
"""
import os
import sys
import json
import time
import asyncio
import threading
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "mascot_assets"
AUDIO_DIR = BASE_DIR / "temp_audio"
AUDIO_DIR.mkdir(exist_ok=True)

import nora_brain
import agent_home
import memory_manager
import system_monitor
import voice_engine
import mascot_assets

SERVER_PORT = 8000

class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class NoraAPIHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Statut général
        if path == "/api/status":
            self._handle_status()
        # 2. Capacités et boutons dynamiques (Synchro auto PC -> Mobile)
        elif path == "/api/capabilities":
            self._handle_capabilities()
        # 3. Récupération d'un fichier audio pour streaming
        elif path.startswith("/api/audio/"):
            self._handle_audio(path.replace("/api/audio/", ""))
        # 4. Récupération des sprites Zero Two pour mobile
        elif path.startswith("/api/sprites/"):
            self._handle_sprite(path.replace("/api/sprites/", ""))
        # 5. État complet de la domotique
        elif path == "/api/home/status":
            self._handle_home_status()
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint introuvable"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        # 1. Discussion & Ordres Vocaux / Texte
        if path == "/api/chat":
            self._handle_chat(data)
        # 2. Exécution d'une action domotique ou système
        elif path == "/api/action":
            self._handle_action(data)
        # 3. Changement de tenue de Zero Two
        elif path == "/api/outfit":
            self._handle_set_outfit(data)
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint POST introuvable"}).encode("utf-8"))

    def _handle_status(self):
        metrics = system_monitor.get_system_stats()
        curr_outfit = memory_manager.get_current_outfit()
        hue_paired = agent_home.smart_home.is_hue_paired()

        resp = {
            "status": "online",
            "name": "Nora",
            "character": "Zero Two",
            "version": "2.0.0",
            "outfit": curr_outfit,
            "pc_metrics": {
                "cpu_percent": metrics.get("cpu_percent", 0),
                "ram_percent": metrics.get("ram_percent", 0),
                "battery": metrics.get("battery", "Secteur"),
            },
            "smart_home": {
                "hue_paired": hue_paired,
                "hue_ip": agent_home.smart_home.config.get("hue_ip") or agent_home.smart_home.config.get("last_discovered_ip", "192.168.1.29"),
            }
        }
        self._set_cors_headers(200)
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

    def _handle_capabilities(self):
        """Retourne dynamiquement les boutons, actions et options disponibles."""
        curr_outfit = memory_manager.get_current_outfit()
        hue_state = agent_home.smart_home.state

        # Définition dynamique des cartes d'action (enrichissable à volonté sur PC)
        actions = [
            {
                "id": "salon",
                "title": "Lumière Salon",
                "icon": "💡",
                "category": "lumiere",
                "action": "toggle_light:salon",
                "active": hue_state.get("lights", {}).get("salon", {}).get("on", False)
            },
            {
                "id": "chambre",
                "title": "Lumière Chambre",
                "icon": "💡",
                "category": "lumiere",
                "action": "toggle_light:chambre",
                "active": hue_state.get("lights", {}).get("chambre", {}).get("on", False)
            },
            {
                "id": "zero_two",
                "title": "Ambiance Zero Two",
                "icon": "🌸",
                "category": "ambiance",
                "action": "ambiance_zero_two",
                "active": False
            },
            {
                "id": "night",
                "title": "Mode Nuit",
                "icon": "🌙",
                "category": "ambiance",
                "action": "night_mode",
                "active": False
            },
            {
                "id": "covers",
                "title": "Volets",
                "icon": "🪟",
                "category": "volet",
                "action": "toggle_covers",
                "active": hue_state.get("covers", {}).get("salon", "ouvert") == "ouvert"
            },
            {
                "id": "status_home",
                "title": "Bilan Maison",
                "icon": "📊",
                "category": "info",
                "action": "home_status",
                "active": False
            },
            {
                "id": "boost_ram",
                "title": "Boost RAM PC",
                "icon": "⚡",
                "category": "pc",
                "action": "boost_ram",
                "active": False
            }
        ]

        outfits = [
            {"id": "franxx", "name": "Pilote Franxx 🚀", "active": curr_outfit == "franxx"},
            {"id": "school", "name": "Écolière Sailor 🎓", "active": curr_outfit == "school"},
            {"id": "hoodie", "name": "Hoodie Doux 🧸", "active": curr_outfit == "hoodie"},
        ]

        resp = {
            "actions": actions,
            "outfits": outfits,
            "current_outfit": curr_outfit
        }
        self._set_cors_headers(200)
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

    def _handle_chat(self, data: dict):
        user_message = data.get("message", "").strip()
        if not user_message:
            self._set_cors_headers(400)
            self.wfile.write(json.dumps({"error": "Message vide"}).encode("utf-8"))
            return

        # 1. Analyse de l'intention et réponse par le cerveau Nora
        intent, chat_reply = nora_brain.analyze_intent_and_respond(user_message)

        # 2. Génération audio de la voix Zero Two via edge-tts + RVC (RTX 4080)
        audio_id = f"speech_mobile_{int(time.time()*1000)}.mp3"
        audio_path = AUDIO_DIR / audio_id

        try:
            asyncio.run(voice_engine._generate_audio_async(chat_reply, audio_path))
            try:
                import voice_cloning
                final_audio = voice_cloning.convert_to_zero_two(audio_path)
                if final_audio != audio_path and final_audio.exists():
                    audio_id = final_audio.name
            except Exception:
                pass
            audio_url = f"/api/audio/{audio_id}"
        except Exception as e:
            print(f"[Audio Error] {e}")
            audio_url = None

        resp = {
            "user_message": user_message,
            "reply": chat_reply,
            "intent": intent,
            "audio_url": audio_url,
            "sprite_state": "idle",
            "outfit": memory_manager.get_current_outfit()
        }
        self._set_cors_headers(200)
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

    def _handle_action(self, data: dict):
        action_name = data.get("action", "")
        reply = "Action effectuée, Darling !"

        if action_name.startswith("toggle_light:"):
            room = action_name.split(":")[1]
            lights = agent_home.smart_home.state.get("lights", {}).get(room, {})
            new_on = not lights.get("on", False)
            ok, reply = agent_home.smart_home.set_light(room, on=new_on)
        elif action_name == "ambiance_zero_two":
            ok, reply = agent_home.smart_home.activate_zero_two_ambiance()
        elif action_name == "night_mode":
            ok, reply = agent_home.smart_home.activate_night_mode()
        elif action_name == "toggle_covers":
            cov = agent_home.smart_home.state.get("covers", {}).get("salon", "ouvert")
            new_state = (cov != "ouvert")
            ok, reply = agent_home.smart_home.set_cover("all", open_state=new_state)
        elif action_name == "home_status":
            reply = agent_home.smart_home.get_status_report()
        elif action_name == "boost_ram":
            system_monitor.clean_ram_cache()
            reply = "Cache RAM vidé ! Les performances de ton PC sont au top, Darling !"

        # Générer l'audio de confirmation avec la voix de Zero Two
        audio_id = f"speech_action_{int(time.time()*1000)}.mp3"
        audio_path = AUDIO_DIR / audio_id
        audio_url = None
        try:
            asyncio.run(voice_engine._generate_audio_async(reply, audio_path))
            try:
                import voice_cloning
                final_audio = voice_cloning.convert_to_zero_two(audio_path)
                if final_audio != audio_path and final_audio.exists():
                    audio_id = final_audio.name
            except Exception:
                pass
            audio_url = f"/api/audio/{audio_id}"
        except Exception:
            pass

        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "success": True,
            "reply": reply,
            "audio_url": audio_url
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_set_outfit(self, data: dict):
        outfit = data.get("outfit", "franxx")
        if outfit in ["franxx", "school", "hoodie"]:
            memory_manager.set_current_outfit(outfit)
            mascot_assets.set_active_outfit(outfit)
            msg = f"J'ai revêtu ma tenue {outfit}, Darling !"
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"success": True, "outfit": outfit, "reply": msg}).encode("utf-8"))
        else:
            self._set_cors_headers(400)
            self.wfile.write(json.dumps({"error": "Tenue invalide"}).encode("utf-8"))

    def _handle_audio(self, filename: str):
        file_path = AUDIO_DIR / filename
        if file_path.exists() and file_path.is_file():
            self._set_cors_headers(200, "audio/mpeg")
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self._set_cors_headers(404)
            self.wfile.write(b"Audio introuvable")

    def _handle_sprite(self, subpath: str):
        parts = subpath.split("/")
        if len(parts) == 2:
            outfit, state = parts[0], parts[1].replace(".png", "")
            file_path = ASSETS_DIR / f"nora_{outfit}_{state}.png"
            if not file_path.exists():
                file_path = ASSETS_DIR / f"nora_{state}.png"
            if not file_path.exists():
                file_path = ASSETS_DIR / "nora_idle.png"
        else:
            file_path = ASSETS_DIR / subpath

        if file_path.exists() and file_path.is_file():
            self._set_cors_headers(200, "image/png")
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self._set_cors_headers(404)
            self.wfile.write(b"Sprite introuvable")

    def _handle_home_status(self):
        rep = agent_home.smart_home.get_status_report()
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "report": rep,
            "state": agent_home.smart_home.state
        }, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[Nora Mobile API] {self.client_address[0]} - {format % args}", flush=True)

def start_server_background(port: int = SERVER_PORT) -> ThreadingSimpleServer:
    server = ThreadingSimpleServer(("0.0.0.0", port), NoraAPIHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"🚀 Serveur Nora Mobile actif sur http://0.0.0.0:{port} (Wi-Fi : http://192.168.1.183:{port})")
    return server

if __name__ == "__main__":
    server = start_server_background(SERVER_PORT)
    print("Appuyez sur Ctrl+C pour arrêter le serveur.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
        print("Serveur arrêté.")
