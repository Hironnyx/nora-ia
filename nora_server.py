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
ACTIVE_AUDIO_JOBS: dict[str, threading.Event] = {}

def _synthesize_audio_background(text: str, target_path: Path, job_id: str, evt: threading.Event):
    """Synthétise l'audio en arrière-plan sans bloquer la réponse texte."""
    try:
        asyncio.run(voice_engine._generate_audio_async(text, target_path))
        try:
            import voice_cloning
            final_audio = voice_cloning.convert_to_zero_two(target_path)
            if final_audio != target_path and final_audio.exists():
                try:
                    import shutil
                    shutil.copy2(final_audio, target_path)
                except Exception:
                    pass
        except Exception as ex:
            print(f"[RVC Background Convert] {ex}")
    except Exception as e:
        print(f"[Audio Background Error] {e}")
    finally:
        evt.set()

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
        # 6. Carnet d'apprentissage autonome
        elif path == "/api/learning":
            self._handle_learning()
        # 7. Données Santé & Bien-Être
        elif path == "/api/health":
            self._handle_health_get()
        # 8. Suite Financière (Budget, Bourse, Crypto, Patrimoine)
        elif path == "/api/finances":
            self._handle_finances_get()
        elif path == "/api/bourse":
            self._handle_bourse_get()
        elif path == "/api/crypto":
            self._handle_crypto_get()
        elif path == "/api/patrimoine":
            self._handle_patrimoine_get()
        # 9. Courriels (Emails)
        elif path == "/api/emails":
            self._handle_emails_get()
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
        # 4. Synchronisation Santé Mobile (Health Connect / Pas)
        elif path == "/api/health":
            self._handle_health_post(data)
        # 5. Ajout de transaction financière
        elif path == "/api/finances":
            self._handle_finances_post(data)
        # 6. Gestion et envoi de courriels
        elif path == "/api/emails":
            self._handle_emails_post(data)
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
            },
            {
                "id": "create_video",
                "title": "Créer une Vidéo",
                "icon": "🎬",
                "category": "studio",
                "action": "create_video",
                "active": False
            },
            {
                "id": "learn_new",
                "title": "Apprendre un Sujet",
                "icon": "🧠",
                "category": "learning",
                "action": "learn_new",
                "active": False
            },
            {
                "id": "learning_journal",
                "title": "Carnet d'Apprentissage",
                "icon": "📖",
                "category": "learning",
                "action": "learning_journal",
                "active": False
            },
            {
                "id": "optimize_code",
                "title": "Optimiser le Code",
                "icon": "🛠️",
                "category": "pc",
                "action": "optimize_code",
                "active": False
            },
            {
                "id": "log_water",
                "title": "Boire un Verre d'Eau",
                "icon": "💧",
                "category": "sante",
                "action": "log_water",
                "active": False
            },
            {
                "id": "screen_pause",
                "title": "Pause Écran / Yeux",
                "icon": "🧘",
                "category": "sante",
                "action": "screen_pause",
                "active": False
            },
            {
                "id": "health_report",
                "title": "Bilan Santé Darling",
                "icon": "🩺",
                "category": "sante",
                "action": "health_report",
                "active": False
            },
            {
                "id": "patrimoine_report",
                "title": "Bilan Patrimoine 💎",
                "icon": "💎",
                "category": "finance",
                "action": "patrimoine_report",
                "active": False
            },
            {
                "id": "crypto_market",
                "title": "Marché Crypto (BTC)",
                "icon": "🪙",
                "category": "finance",
                "action": "crypto_market",
                "active": False
            },
            {
                "id": "bourse_report",
                "title": "Bourse & ETF",
                "icon": "📈",
                "category": "finance",
                "action": "bourse_report",
                "active": False
            },
            {
                "id": "budget_report",
                "title": "Comptes Bancaires",
                "icon": "🏦",
                "category": "finance",
                "action": "budget_report",
                "active": False
            },
            {
                "id": "check_emails",
                "title": "Mes Courriels",
                "icon": "📧",
                "category": "comms",
                "action": "check_emails",
                "active": False
            },
            {
                "id": "call_standardiste",
                "title": "Mode Standardiste",
                "icon": "🎙️",
                "category": "comms",
                "action": "call_standardiste",
                "active": False
            },
            {
                "id": "read_sms",
                "title": "Derniers SMS",
                "icon": "✉️",
                "category": "comms",
                "action": "read_sms",
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

        # Synchroniser les métriques de santé mobiles éventuelles transmises
        if "mobile_health" in data or "battery" in data:
            import agent_health
            agent_health.health_agent.sync_mobile_health_data(data.get("mobile_health", data))

        # 1. Analyse de l'intention et réponse par le cerveau Nora
        intent, chat_reply = nora_brain.analyze_intent_and_respond(user_message)

        # Extraction d'ordre matériel pour le téléphone
        device_cmd = None
        if intent.startswith("PHONE_ACTION:"):
            parts = intent.split(":")
            if len(parts) >= 3 and parts[1] == "flashlight":
                device_cmd = {"type": "flashlight", "action": parts[2]}
            elif len(parts) >= 3 and parts[1] == "volume":
                device_cmd = {"type": "volume", "value": int(parts[2])}
            elif len(parts) >= 3 and parts[1] == "launch_app":
                device_cmd = {"type": "launch_app", "package": parts[2]}
            elif len(parts) >= 3 and parts[1] == "send_sms":
                device_cmd = {"type": "send_sms", "contact": parts[2], "body": parts[3] if len(parts) >= 4 else ""}
            elif len(parts) >= 2 and parts[1] == "call_standardiste":
                device_cmd = {"type": "call_standardiste"}
            elif len(parts) >= 2 and parts[1] == "read_sms":
                device_cmd = {"type": "read_sms"}
            elif len(parts) >= 2 and parts[1] == "call_log":
                device_cmd = {"type": "call_log"}

        # 2. Découplage Audio Asynchrone : Réponse texte immédiate en ~0,17s !
        audio_id = f"speech_mobile_{int(time.time()*1000)}.mp3"
        audio_path = AUDIO_DIR / audio_id
        evt = threading.Event()
        ACTIVE_AUDIO_JOBS[audio_id] = evt

        threading.Thread(
            target=_synthesize_audio_background,
            args=(chat_reply, audio_path, audio_id, evt),
            daemon=True
        ).start()
        audio_url = f"/api/audio/{audio_id}"

        resp = {
            "user_message": user_message,
            "reply": chat_reply,
            "intent": intent,
            "audio_url": audio_url,
            "sprite_state": "idle",
            "outfit": memory_manager.get_current_outfit(),
            "device_command": device_cmd
        }
        self._set_cors_headers(200)
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

    def _handle_action(self, data: dict):
        action_name = data.get("action", "")
        reply = "Action effectuée, Maverick."

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
            reply = "Cache RAM vidé ! Les performances de votre PC sont optimales, Maverick."
        elif action_name == "create_video":
            import nora_video_studio
            res = nora_video_studio.create_video_from_latest_learning(format_type="shorts")
            if res.get("success"):
                reply = f"Vidéo générée avec succès sur '{res['title']}' ! Elle vous attend dans le dossier creations_videos, Maverick."
            else:
                reply = f"J'ai rencontré un petit souci pendant le montage de la vidéo : {res.get('error')}"
        elif action_name in ["read_sms", "comms:read_sms"]:
            reply = "Je vous invite à consulter vos SMS directement sur l'écran de votre smartphone, Maverick."
        elif action_name in ["check_emails", "comms:emails"]:
            import agent_mail
            reply = agent_mail.mail_agent.get_summary_speech()
        elif action_name in ["call_standardiste", "comms:standardiste"]:
            reply = "Le mode standardiste est prêt sur votre téléphone, Maverick."
        elif action_name == "learn_new":
            import nora_learner
            res = nora_learner.learn_something_new()
            reply = res.get("message_vocal", "J'ai enrichi mes connaissances dans mon carnet, Maverick.")
        elif action_name == "learning_journal":
            import nora_learner
            reply = nora_learner.get_recent_learnings_summary()
        elif action_name == "optimize_code":
            import nora_code_evolver
            res = nora_code_evolver.analyze_and_propose_improvement("system_monitor.py")
            if res.get("success"):
                reply = f"Maverick : {res['explication']} Dites-moi 'Oui applique' si vous souhaitez valider."
            else:
                reply = "Le code est déjà parfaitement optimisé, Maverick."
        elif action_name == "log_water":
            import agent_health
            _, reply = agent_health.health_agent.log_water(1)
        elif action_name == "screen_pause":
            import agent_health
            reply = agent_health.health_agent.log_screen_break()
        elif action_name == "health_report":
            import agent_health
            reply = agent_health.health_agent.get_health_report_speech()
        elif action_name == "patrimoine_report":
            import finance_manager
            reply = finance_manager.get_global_speech_report()
        elif action_name == "crypto_market":
            import agent_crypto
            reply = agent_crypto.crypto_agent.get_summary_speech()
        elif action_name == "bourse_report":
            import agent_bourse
            reply = agent_bourse.bourse_agent.get_summary_speech()
        elif action_name == "budget_report":
            import agent_budget
            reply = agent_budget.budget_agent.get_summary_speech()
        elif action_name == "check_emails":
            import agent_mail
            reply = agent_mail.mail_agent.get_summary_speech()
        elif action_name == "call_standardiste":
            reply = "Mode Standardiste actif, Maverick. Je prendrai vos prochains appels avec professionnalisme."
        elif action_name == "read_sms":
            reply = "Synchronisation de vos derniers messages mobiles demandée, Maverick."

        # Générer l'audio de confirmation en tâche de fond non-bloquante
        audio_id = f"speech_action_{int(time.time()*1000)}.mp3"
        audio_path = AUDIO_DIR / audio_id
        evt = threading.Event()
        ACTIVE_AUDIO_JOBS[audio_id] = evt
        threading.Thread(
            target=_synthesize_audio_background,
            args=(reply, audio_path, audio_id, evt),
            daemon=True
        ).start()
        audio_url = f"/api/audio/{audio_id}"

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
        # Si la génération audio est en cours en tâche de fond, attendre qu'elle se termine
        if filename in ACTIVE_AUDIO_JOBS:
            ACTIVE_AUDIO_JOBS[filename].wait(timeout=12.0)

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

    def _handle_learning(self):
        import nora_learner
        kb = nora_learner.load_knowledge_base()
        journal_text = ""
        if nora_learner.JOURNAL_FILE.exists():
            try:
                with open(nora_learner.JOURNAL_FILE, "r", encoding="utf-8") as f:
                    journal_text = f.read()
            except Exception:
                pass
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "knowledge": kb,
            "journal_markdown": journal_text,
            "summary": nora_learner.get_recent_learnings_summary()
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_health_get(self):
        import agent_health
        today = agent_health.health_agent.get_today()
        journal_md = ""
        if agent_health.JOURNAL_FILE.exists():
            try:
                with open(agent_health.JOURNAL_FILE, "r", encoding="utf-8") as f:
                    journal_md = f.read()
            except Exception:
                pass
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "today": today,
            "speech_report": agent_health.health_agent.get_health_report_speech(),
            "journal_markdown": journal_md
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_health_post(self, data: dict):
        import agent_health
        agent_health.health_agent.sync_mobile_health_data(data)
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "success": True,
            "today": agent_health.health_agent.get_today(),
            "reply": "Données santé synchronisées avec succès, Darling !"
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_finances_get(self):
        import agent_budget
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "accounts": agent_budget.budget_agent.get_accounts(),
            "total_liquidities": agent_budget.budget_agent.get_total_liquidities(),
            "transactions": agent_budget.budget_agent.data.get("transactions", []),
            "speech": agent_budget.budget_agent.get_summary_speech()
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_finances_post(self, data: dict):
        import agent_budget
        amount = float(data.get("amount", 0.0))
        category = data.get("category", "Autre")
        desc = data.get("description", "Dépense enregistrée")
        acc = data.get("account", "Courant")
        tx = agent_budget.budget_agent.add_transaction(amount, category, desc, acc)
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "success": True,
            "transaction": tx,
            "accounts": agent_budget.budget_agent.get_accounts()
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_bourse_get(self):
        import agent_bourse
        val = agent_bourse.bourse_agent.get_portfolio_valuation()
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "portfolio": val,
            "speech": agent_bourse.bourse_agent.get_summary_speech()
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_crypto_get(self):
        import agent_crypto
        val = agent_crypto.crypto_agent.get_portfolio_valuation()
        fng = agent_crypto.crypto_agent.fetch_fear_and_greed_index()
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "portfolio": val,
            "fear_and_greed": fng,
            "speech": agent_crypto.crypto_agent.get_summary_speech()
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_patrimoine_get(self):
        import finance_manager
        pat = finance_manager.get_patrimoine_global()
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "patrimoine": pat,
            "speech": finance_manager.get_global_speech_report()
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_emails_get(self):
        import agent_mail
        emails = agent_mail.mail_agent.fetch_recent_emails(unread_only=False, limit=5)
        self._set_cors_headers(200)
        self.wfile.write(json.dumps({
            "emails": emails,
            "speech": agent_mail.mail_agent.get_summary_speech()
        }, ensure_ascii=False).encode("utf-8"))

    def _handle_emails_post(self, data: dict):
        import agent_mail
        action = data.get("action", "summary")
        if action == "draft":
            to = data.get("to", "")
            subject = data.get("subject", "")
            instr = data.get("instructions", "")
            draft = agent_mail.mail_agent.draft_reply(to, subject, instr)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"draft": draft}, ensure_ascii=False).encode("utf-8"))
        elif action == "send":
            to = data.get("to", "")
            subject = data.get("subject", "")
            body = data.get("body", "")
            ok, msg = agent_mail.mail_agent.send_email(to, subject, body)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"success": ok, "message": msg}, ensure_ascii=False).encode("utf-8"))
        else:
            self._handle_emails_get()

    def log_message(self, format, *args):
        print(f"[Nora Mobile API] {self.client_address[0]} - {format % args}", flush=True)

def start_server_background(port: int = SERVER_PORT) -> ThreadingSimpleServer:
    server = ThreadingSimpleServer(("0.0.0.0", port), NoraAPIHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"🚀 Serveur Nora Mobile actif sur http://0.0.0.0:{port} (Wi-Fi : http://192.168.1.183:{port})")

    # Pré-chauffage VRAM automatique pour la RTX 4080
    try:
        import voice_cloning
        voice_cloning.warmup_in_background()
        print("🌸 [VoiceCloning] Pré-chauffage VRAM du modèle vocal lancé en arrière-plan.")
    except Exception as e:
        print(f"⚠️ Pré-chauffage VRAM : {e}")

    # Démarrage automatique du tunnel 4G/5G sécurisé en arrière-plan
    try:
        import tunnel_manager
        threading.Thread(target=tunnel_manager.start_remote_tunnel, args=(True,), daemon=True).start()
    except Exception as e:
        print(f"⚠️ Démarrage tunnel 4G/5G : {e}")

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
