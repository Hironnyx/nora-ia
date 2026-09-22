"""
Script d'écoute et d'appairage interactif pour le pont Philips Hue (192.168.1.29).
Ce script attend pendant 60 secondes que Maverick appuie sur le bouton rond du pont Hue.
Dès que le bouton est pressé, il enregistre le jeton dans smart_home_config.json
et récupère la liste réelle des ampoules et pièces de la maison.
"""
import sys
import time
import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "smart_home_config.json"

def run_pairing_listener(timeout_seconds: int = 60):
    bridge_ip = "192.168.1.29"
    url = f"http://{bridge_ip}/api"
    payload = {"devicetype": "NoraFranxx#DesktopPC"}

    print(f"[HUE PAIRING] En attente du bouton physique sur le pont Hue ({bridge_ip})...")
    print("[HUE PAIRING] Veuillez appuyer sur le gros bouton rond au centre du pont Philips Hue.")

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            r = requests.post(url, json=payload, timeout=2.0)
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                if "success" in item:
                    username = item["success"]["username"]
                    print(f"\n[SUCCÈS] Appairage validé avec succès ! Token : {username[:10]}...")

                    # Sauvegarde de la configuration
                    config = {}
                    if CONFIG_FILE.exists():
                        try:
                            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                                config = json.load(f)
                        except Exception:
                            pass
                    config["hue_bridge_ip"] = bridge_ip
                    config["hue_username"] = username
                    config["mode"] = "hue"
                    config["last_discovered_ip"] = bridge_ip
                    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)

                    # Récupération des ampoules réelles
                    lights_res = requests.get(f"http://{bridge_ip}/api/{username}/lights", timeout=3.0)
                    if lights_res.status_code == 200:
                        lights = lights_res.json()
                        print(f"[LUMIERES] {len(lights)} équipement(s) Philips Hue détecté(s) :")
                        for lid, info in lights.items():
                            state = "Allumée" if info.get("state", {}).get("on") else "Éteinte"
                            print(f"  - ID {lid} : {info.get('name')} ({state}, {info.get('type')})")
                    return True, username
                elif "error" in item and item["error"].get("type") == 101:
                    # Bouton pas encore pressé, on patiente
                    elapsed = int(time.time() - start_time)
                    sys.stdout.write(f"\r[En attente... {elapsed}s/{timeout_seconds}s] Appuyez sur le bouton rond du pont Hue...")
                    sys.stdout.flush()
                else:
                    print(f"\n[ERREUR] {item}")
        except Exception as e:
            print(f"\n[ERREUR RESEAU] {e}")

        time.sleep(1.0)

    print(f"\n[TIMEOUT] Le bouton n'a pas été pressé dans le délai imparti ({timeout_seconds}s).")
    return False, None

if __name__ == "__main__":
    success, user = run_pairing_listener(60)
    sys.exit(0 if success else 1)
