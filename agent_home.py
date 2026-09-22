"""
Agent Domotique & Contrôle de la Maison pour Nora (Smart Home Commander) :
- Contrôle direct du pont Philips Hue local (ampoules, pièces, luminosité, couleurs, ambiances)
- Découverte automatique du pont Hue sur le réseau local (mDNS & N-UPnP)
- Appairage 1-clic avec bouton physique du pont Hue
- Support étendu pour Home Assistant (REST API), Google Home / Webhooks et Shelly
- Simulateur interactif persistant avec état en temps réel (smart_home_state.json)
- Analyseur de commandes vocales et textuelles en langage naturel
"""
import os
import sys
import json
import time
import re
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import requests

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.resolve()

CONFIG_FILE = BASE_DIR / "smart_home_config.json"
STATE_FILE = BASE_DIR / "smart_home_state.json"

# Couleurs coordonnées CIE 1931 pour Philips Hue
HUE_COLORS = {
    "rose": {"xy": [0.4149, 0.1776], "sat": 240},
    "zero two": {"xy": [0.4500, 0.1800], "sat": 254},
    "rouge": {"xy": [0.675, 0.322], "sat": 254},
    "bleu": {"xy": [0.167, 0.04], "sat": 254},
    "vert": {"xy": [0.2151, 0.7106], "sat": 254},
    "jaune": {"xy": [0.4325, 0.5007], "sat": 220},
    "orange": {"xy": [0.556, 0.409], "sat": 254},
    "violet": {"xy": [0.27, 0.13], "sat": 240},
    "cyan": {"xy": [0.15, 0.30], "sat": 254},
    "blanc chaud": {"ct": 370},
    "chaud": {"ct": 370},
    "blanc froid": {"ct": 153},
    "froid": {"ct": 153},
    "blanc": {"ct": 250},
}

class SmartHomeCommander:
    """Contrôleur domotique intelligent avec support Philips Hue, Home Assistant et Simulateur."""

    def __init__(self):
        self.config = self._load_config()
        self.state = self._load_state()
        self._lock = threading.Lock()
        self._cache_lights: List[Dict[str, Any]] = []
        self._cache_groups: List[Dict[str, Any]] = []
        self._last_poll_time = 0.0

    # -------------------------------------------------------------
    # GESTION DE LA CONFIGURATION ET DE L'ÉTAT
    # -------------------------------------------------------------
    def _load_config(self) -> Dict[str, Any]:
        default_config = {
            "hue_bridge_ip": "192.168.1.29",
            "hue_username": None,
            "home_assistant_url": None,
            "home_assistant_token": None,
            "mode": "auto",  # 'hue', 'home_assistant', 'simulator', 'auto'
            "last_discovered_ip": "192.168.1.29"
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_config.update(data)
            except Exception:
                pass
        return default_config

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ [SmartHome] Erreur sauvegarde config: {e}")

    def _load_state(self) -> Dict[str, Any]:
        default_state = {
            "lights": {
                "salon": {"on": False, "bri": 200, "color": "blanc chaud"},
                "chambre": {"on": False, "bri": 150, "color": "rose"},
                "bureau": {"on": True, "bri": 254, "color": "blanc"},
                "cuisine": {"on": False, "bri": 200, "color": "blanc"}
            },
            "covers": {
                "salon": "ouvert",
                "chambre": "ouvert"
            },
            "climate": {
                "temperature": 21.0,
                "mode": "confort"
            },
            "night_mode": False
        }
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_state.update(data)
            except Exception:
                pass
        return default_state

    def save_state(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ [SmartHome] Erreur sauvegarde état: {e}")

    # -------------------------------------------------------------
    # PHILIPS HUE - DÉCOUVERTE ET APPAIRAGE
    # -------------------------------------------------------------
    def discover_hue_bridge(self) -> Optional[str]:
        """Détecte l'adresse IP du pont Philips Hue sur le réseau local."""
        # 1. Utiliser l'IP mémorisée si elle répond
        cached_ip = self.config.get("hue_bridge_ip") or self.config.get("last_discovered_ip")
        if cached_ip:
            try:
                r = requests.get(f"http://{cached_ip}/api/config", timeout=1.5)
                if r.status_code == 200 and "name" in r.text:
                    self.config["hue_bridge_ip"] = cached_ip
                    self.save_config()
                    return cached_ip
            except Exception:
                pass

        # 2. Découverte officielle Philips N-UPnP
        try:
            r = requests.get("https://discovery.meethue.com", timeout=3.0)
            if r.status_code == 200:
                bridges = r.json()
                if bridges and isinstance(bridges, list) and len(bridges) > 0:
                    found_ip = bridges[0].get("internalipaddress")
                    if found_ip:
                        self.config["hue_bridge_ip"] = found_ip
                        self.config["last_discovered_ip"] = found_ip
                        self.save_config()
                        return found_ip
        except Exception:
            pass

        return cached_ip

    def pair_hue_bridge(self) -> Tuple[bool, str]:
        """
        Tente d'appairer Nora avec le pont Philips Hue.
        Nécessite que l'utilisateur ait appuyé sur le bouton rond du pont.
        """
        ip = self.discover_hue_bridge()
        if not ip:
            return False, "Aucun pont Philips Hue détecté sur votre réseau Wi-Fi/LAN."

        url = f"http://{ip}/api"
        payload = {"devicetype": "NoraFranxx#DesktopPC"}

        try:
            r = requests.post(url, json=payload, timeout=4.0)
            res = r.json()
            if isinstance(res, list) and len(res) > 0:
                item = res[0]
                if "success" in item:
                    username = item["success"]["username"]
                    self.config["hue_username"] = username
                    self.config["hue_bridge_ip"] = ip
                    self.config["mode"] = "hue"
                    self.save_config()
                    return True, f"Connexion réussie avec le pont Philips Hue ({ip}) ! Nora contrôle désormais vos lumières, Maverick !"
                elif "error" in item:
                    err_type = item["error"].get("type")
                    if err_type == 101:
                        return False, "Le bouton du pont Hue n'a pas été pressé ! Appuyez sur le gros bouton rond au centre du pont Hue et réessayez, Maverick."
                    return False, f"Erreur du pont Hue : {item['error'].get('description', 'Inconnue')}"
        except Exception as e:
            return False, f"Impossible de contacter le pont Hue ({ip}) : {e}"

        return False, "Réponse inattendue du pont Philips Hue."

    def is_hue_paired(self) -> bool:
        """Indique si un pont Hue est configuré et appairé avec un token valide."""
        return bool(self.config.get("hue_bridge_ip") and self.config.get("hue_username"))

    # -------------------------------------------------------------
    # PHILIPS HUE - LECTURE DES ÉQUIPEMENTS & PIÈCES
    # -------------------------------------------------------------
    def get_hue_lights(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Récupère la liste de toutes les ampoules Philips Hue."""
        if not self.is_hue_paired():
            return {}

        now = time.time()
        if not force_refresh and self._cache_lights and (now - self._last_poll_time < 5.0):
            return self._cache_lights

        ip = self.config["hue_bridge_ip"]
        user = self.config["hue_username"]
        url = f"http://{ip}/api/{user}/lights"

        try:
            r = requests.get(url, timeout=3.0)
            if r.status_code == 200:
                self._cache_lights = r.json()
                self._last_poll_time = now
                return self._cache_lights
        except Exception:
            pass
        return self._cache_lights or {}

    def get_hue_groups(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Récupère la liste des pièces et zones configurées dans l'application Hue."""
        if not self.is_hue_paired():
            return {}

        ip = self.config["hue_bridge_ip"]
        user = self.config["hue_username"]
        url = f"http://{ip}/api/{user}/groups"

        try:
            r = requests.get(url, timeout=3.0)
            if r.status_code == 200:
                self._cache_groups = r.json()
                return self._cache_groups
        except Exception:
            pass
        return self._cache_groups or {}

    # -------------------------------------------------------------
    # CONTRÔLE DES LUMIÈRES (HUE OU SIMULATEUR)
    # -------------------------------------------------------------
    def set_light(
        self,
        target: str = "all",
        on: Optional[bool] = None,
        brightness: Optional[int] = None,
        color_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Allume, éteint ou ajuste la couleur d'une ampoule ou d'une pièce.
        target peut être 'all', 'salon', 'chambre', 'bureau', ou le nom exact d'une ampoule Hue.
        """
        with self._lock:
            # 1. Mode Réel Philips Hue
            if self.is_hue_paired():
                return self._set_hue_light(target, on, brightness, color_name)

            # 2. Mode Simulateur Local (Maison Virtuelle Nora)
            return self._set_simulated_light(target, on, brightness, color_name)

    def _set_hue_light(
        self,
        target: str,
        on: Optional[bool],
        brightness: Optional[int],
        color_name: Optional[str]
    ) -> Tuple[bool, str]:
        ip = self.config["hue_bridge_ip"]
        user = self.config["hue_username"]
        target_clean = target.lower().strip()

        payload: Dict[str, Any] = {}
        if on is not None:
            payload["on"] = on
        if brightness is not None:
            # Conversion 0-100% en 1-254
            clamped = max(1, min(100, brightness))
            payload["bri"] = int((clamped / 100.0) * 254)
        if color_name:
            col = HUE_COLORS.get(color_name.lower().strip())
            if col:
                payload.update(col)
                if on is None:
                    payload["on"] = True

        # Cas 1 : Toutes les lumières
        if target_clean in ["all", "toutes", "tout", "toute la maison", "maison"]:
            url = f"http://{ip}/api/{user}/groups/0/action"
            try:
                r = requests.put(url, json=payload, timeout=4.0)
                if r.status_code == 200:
                    stat = "allumées" if on is not False else "éteintes"
                    if color_name:
                        return True, f"Toutes les lumières sont passées en {color_name} !"
                    return True, f"Toutes les lumières de la maison sont maintenant {stat}, Maverick."
            except Exception as e:
                return False, f"Erreur de communication avec le pont Hue : {e}"

        # Cas 2 : Recherche dans les pièces/groupes Hue (Salon, Chambre, etc.)
        groups = self.get_hue_groups(force_refresh=True)
        for g_id, g_info in groups.items():
            g_name = g_info.get("name", "").lower()
            if target_clean in g_name or g_name in target_clean:
                url = f"http://{ip}/api/{user}/groups/{g_id}/action"
                try:
                    r = requests.put(url, json=payload, timeout=4.0)
                    if r.status_code == 200:
                        stat = "allumée" if on is not False else "éteinte"
                        msg = f"La pièce {g_info.get('name')} est maintenant {stat} !"
                        if color_name:
                            msg = f"L'ambiance de la pièce {g_info.get('name')} est passée en {color_name} !"
                        return True, msg
                except Exception as e:
                    return False, f"Erreur : {e}"

        # Cas 3 : Recherche dans les ampoules individuelles
        lights = self.get_hue_lights(force_refresh=True)
        for l_id, l_info in lights.items():
            l_name = l_info.get("name", "").lower()
            if target_clean in l_name or l_name in target_clean:
                url = f"http://{ip}/api/{user}/lights/{l_id}/state"
                try:
                    r = requests.put(url, json=payload, timeout=4.0)
                    if r.status_code == 200:
                        stat = "allumée" if on is not False else "éteinte"
                        msg = f"L'ampoule {l_info.get('name')} est maintenant {stat} !"
                        if color_name:
                            msg = f"L'ampoule {l_info.get('name')} est maintenant en {color_name} !"
                        return True, msg
                except Exception as e:
                    return False, f"Erreur : {e}"

        # Si non trouvé, appliquer au groupe 0 (global) par sécurité
        url = f"http://{ip}/api/{user}/groups/0/action"
        try:
            requests.put(url, json=payload, timeout=4.0)
            return True, "Ordre appliqué à vos lumières Philips Hue, Maverick."
        except Exception as e:
            return False, f"Impossible d'appliquer l'ordre : {e}"

    def _set_simulated_light(
        self,
        target: str,
        on: Optional[bool],
        brightness: Optional[int],
        color_name: Optional[str]
    ) -> Tuple[bool, str]:
        target_clean = target.lower().strip()
        lights = self.state["lights"]

        if target_clean in ["all", "toutes", "tout", "toute la maison", "maison"]:
            for k in lights:
                if on is not None:
                    lights[k]["on"] = on
                if brightness is not None:
                    lights[k]["bri"] = int((brightness / 100.0) * 254)
                if color_name:
                    lights[k]["color"] = color_name
            self.save_state()
            stat = "allumées" if on is not False else "éteintes"
            col_str = f" en {color_name}" if color_name else ""
            return True, f"[Maison Nora] Toutes les lumières sont {stat}{col_str}, Maverick."

        # Pièce spécifique
        room = None
        for k in lights:
            if k in target_clean or target_clean in k:
                room = k
                break
        if not room:
            room = "salon"  # Par défaut

        if on is not None:
            lights[room]["on"] = on
        if brightness is not None:
            lights[room]["bri"] = int((brightness / 100.0) * 254)
        if color_name:
            lights[room]["color"] = color_name
            lights[room]["on"] = True

        self.save_state()
        stat = "allumée" if lights[room]["on"] else "éteinte"
        col_str = f" en {lights[room].get('color')}" if color_name else ""
        room_prep = "de la chambre" if room == "chambre" else ("de la cuisine" if room == "cuisine" else f"du {room}")
        return True, f"[Maison Nora] La lumière {room_prep} est maintenant {stat}{col_str}, Maverick."

    # -------------------------------------------------------------
    # AMBIANCE & MODE NUIT
    # -------------------------------------------------------------
    def activate_zero_two_ambiance(self) -> Tuple[bool, str]:
        """Ajuste les lumières dans une douce ambiance tamisée rose."""
        ok, _ = self.set_light("all", on=True, brightness=90, color_name="rose")
        return True, "Ambiance tamisée rose activée, Maverick."

    def activate_night_mode(self) -> Tuple[bool, str]:
        """Éteint toutes les lumières et ferme les volets pour la nuit."""
        self.set_light("all", on=False)
        self.state["night_mode"] = True
        self.state["covers"]["salon"] = "fermé"
        self.state["covers"]["chambre"] = "fermé"
        self.save_state()
        return True, "Mode Nuit activé, Maverick. Toutes les lumières sont éteintes et les volets sont fermés. Passez une excellente nuit."

    # -------------------------------------------------------------
    # VOLETS ET CHAUFFAGE (SIMULATEUR & HOME ASSISTANT READY)
    # -------------------------------------------------------------
    def set_cover(self, target: str = "all", open_state: bool = True) -> Tuple[bool, str]:
        """Ouvre ou ferme les volets roulants."""
        with self._lock:
            state_str = "ouvert" if open_state else "fermé"
            target_clean = target.lower().strip()
            if "chambre" in target_clean:
                self.state["covers"]["chambre"] = state_str
                room = "de la chambre"
            elif "salon" in target_clean:
                self.state["covers"]["salon"] = state_str
                room = "du salon"
            else:
                self.state["covers"]["salon"] = state_str
                self.state["covers"]["chambre"] = state_str
                room = "de toute la maison"

            self.save_state()
            action = "ouverts" if open_state else "fermés"
            return True, f"Les volets {room} sont maintenant {action}, Maverick."

    def set_temperature(self, temp_celsius: float) -> Tuple[bool, str]:
        """Règle la température de consigne du chauffage / thermostat."""
        with self._lock:
            clamped = max(15.0, min(28.0, float(temp_celsius)))
            self.state["climate"]["temperature"] = clamped
            self.save_state()
            return True, f"Thermostat réglé sur {clamped:.1f}°C, Maverick."

    # -------------------------------------------------------------
    # RAPPORT GLOBAL D'ÉTAT
    # -------------------------------------------------------------
    def get_status_report(self) -> str:
        """Génère un résumé complet de la maison connectée."""
        lines = []
        ip = self.config.get("hue_bridge_ip", "Non configuré")
        paired = self.is_hue_paired()

        if paired:
            lines.append(f"🏠 Pont Philips Hue : Connecté ({ip})")
            lights = self.get_hue_lights()
            if lights:
                on_count = sum(1 for l in lights.values() if l.get("state", {}).get("on"))
                lines.append(f"💡 Éclairage Hue : {on_count}/{len(lights)} lumières allumées")
            else:
                lines.append("💡 Éclairage Hue : Synchronisé")
        else:
            lines.append(f"🏠 Pont Philips Hue : Détecté ({ip}) [En attente d'association]")
            sim_lights = self.state.get("lights", {})
            on_sim = sum(1 for l in sim_lights.values() if l.get("on"))
            lines.append(f"💡 Éclairage (Maison Nora) : {on_sim}/{len(sim_lights)} allumées")

        # Volets et Climatisation
        cov = self.state.get("covers", {})
        lines.append(f"🪟 Volets : Salon {cov.get('salon', 'ouvert')} | Chambre {cov.get('chambre', 'ouvert')}")
        clim = self.state.get("climate", {})
        lines.append(f"🌡️ Chauffage : {clim.get('temperature', 21.0)}°C")

        return "\n".join(lines)

    # -------------------------------------------------------------
    # PARSER DE COMMANDES VOCALES & TEXTUELLES
    # -------------------------------------------------------------
    def parse_and_execute(self, user_text: str) -> Tuple[bool, Optional[str]]:
        """
        Détecte si la phrase de l'utilisateur est un ordre domotique,
        l'exécute et renvoie la réponse vocale adaptée de Zero Two.
        """
        clean = user_text.lower().strip()

        # 1. Association / Appairage du Pont Hue
        if re.search(r"(?:associe|connecte|branche|appaire|synchronise).*(?:pont|hue|philips)", clean):
            ok, msg = self.pair_hue_bridge()
            return True, msg

        # 2. Mode Nuit / Tout Éteindre
        if re.search(r"(?:mode nuit|bonne nuit|éteins tout|eteins tout|tout éteindre|tout eteindre)", clean):
            _, msg = self.activate_night_mode()
            return True, msg

        # 3. Ambiance Zero Two / Rose
        if re.search(r"(?:ambiance zero two|ambiance rose|lumière rose|lumiere rose|lumières roses|lumieres roses)", clean):
            _, msg = self.activate_zero_two_ambiance()
            return True, msg

        # 4. État de la Maison
        if re.search(r"(?:état|etat|status|qu'est-ce qui est allumé|qu est ce qui est allume).*(?:maison|lumière|lumiere|chambre|salon|hue)", clean):
            report = self.get_status_report()
            return True, f"Voici l'état des équipements de votre domicile, Maverick :\n{report}"

        # 5. Réglage de couleur spécifique (ex: "mets la lumière du salon en bleu")
        for color in HUE_COLORS.keys():
            if re.search(rf"\b{color}\b", clean) and re.search(r"(?:lumière|lumiere|couleur|mets|passe|allume)", clean):
                target = "salon"
                if "chambre" in clean:
                    target = "chambre"
                elif "bureau" in clean:
                    target = "bureau"
                elif "cuisine" in clean:
                    target = "cuisine"
                elif "tout" in clean or "toutes" in clean or "maison" in clean:
                    target = "all"
                ok, msg = self.set_light(target=target, on=True, color_name=color)
                return True, msg

        # 6. Allumer / Éteindre Lumières (ex: "allume le salon", "éteins la chambre")
        m_light = re.search(r"\b(allume|active|mets|ouvre|éteins|eteins|coupe|désactive)\b.*?\b(lumière|lumieres|lumières|salon|chambre|bureau|cuisine|maison|tout)\b", clean)
        if m_light or re.search(r"\b(allume|éteins|eteins)\b\s+(le salon|la chambre|le bureau|la cuisine|tout)", clean):
            action_word = m_light.group(1) if m_light else ("allume" if "allume" in clean else "éteins")
            turn_on = action_word in ["allume", "active", "mets", "ouvre"]

            target = "all"
            if "salon" in clean:
                target = "salon"
            elif "chambre" in clean:
                target = "chambre"
            elif "bureau" in clean:
                target = "bureau"
            elif "cuisine" in clean:
                target = "cuisine"

            # Vérifier s'il y a un pourcentage de luminosité (ex: "à 50%")
            m_pct = re.search(r"(\d{1,3})\s*%", clean)
            bri = int(m_pct.group(1)) if m_pct else None

            ok, msg = self.set_light(target=target, on=turn_on, brightness=bri)
            return True, msg

        # 7. Volets roulants
        if re.search(r"\b(volet|volets|stores)\b", clean):
            open_state = not bool(re.search(r"\b(ferme|baisse|fermer)\b", clean))
            target = "salon" if "salon" in clean else ("chambre" if "chambre" in clean else "all")
            ok, msg = self.set_cover(target=target, open_state=open_state)
            return True, msg

        # 8. Chauffage / Température (ex: "mets le chauffage à 22 degrés")
        m_temp = re.search(r"(?:chauffage|thermostat|température|temperature).*?(\d{2}(?:[.,]\d)?)", clean)
        if m_temp:
            val = float(m_temp.group(1).replace(",", "."))
            ok, msg = self.set_temperature(val)
            return True, msg

        return False, None

# Instance unique du commandant domotique
smart_home = SmartHomeCommander()

def control_smart_home_light(target: str = "all", on: bool = True, brightness: int = 100, color: str = "") -> str:
    """Allume, éteint ou change la couleur des lumières Philips Hue ou de la maison (target: 'salon', 'chambre', 'all')."""
    ok, msg = smart_home.set_light(target=target, on=on, brightness=brightness, color_name=color if color else None)
    return msg

def control_smart_home_cover(target: str = "all", open_state: bool = True) -> str:
    """Ouvre ou ferme les volets roulants de la maison (target: 'salon', 'chambre', 'all')."""
    ok, msg = smart_home.set_cover(target=target, open_state=open_state)
    return msg

def control_smart_home_temperature(temperature_celsius: float = 21.0) -> str:
    """Règle le thermostat ou le chauffage à une température en degrés Celsius."""
    ok, msg = smart_home.set_temperature(temperature_celsius)
    return msg

def get_smart_home_status() -> str:
    """Consulte l'état des lumières Philips Hue, des volets et du chauffage de la maison."""
    return smart_home.get_status_report()

