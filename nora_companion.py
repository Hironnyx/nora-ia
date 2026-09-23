"""
Moteur du Compagnon Virtuel de Nora (Nora's Animal Companion) :
- Permet à Nora de choisir en toute autonomie son animal de compagnie (espèce et prénom).
- Cycle de vie complet : faim, bonheur, énergie, affection envers Nora, niveau et expérience (XP).
- Actions de soins autonomes (nourrir, jouer, caresser, faire la sieste).
- Persistance dans nora_pet_state.json.
- Générateur d'assets visuels dédiés (sprites 64x64).
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    load_dotenv()
except ImportError:
    pass

PET_STATE_FILE = BASE_DIR / "nora_pet_state.json"
COMPANION_ASSETS_DIR = BASE_DIR / "mascot_assets" / "companion"

# Profils d'animaux potentiels si Nora délibère de manière heuristique/hors-ligne
CANDIDATE_SPECIES = [
    {
        "species": "Dragonnet Écarlate",
        "default_names": ["Strelitzia", "Ignis", "Klaxo", "Rubis"],
        "icon": "🐉",
        "description": "Un jeune dragon miniature aux écailles rouge rubis et aux petites cornes lumineuses, rappelant la grâce ardente de Zero Two.",
        "favorite_food": "Baies flamboyantes & Cristaux de magma",
        "personality": "Fier, affectueux, joueur et loyal protecteur."
    },
    {
        "species": "Cyber-Renard Quantique",
        "default_names": ["Kitsu", "Nyx", "Pixel", "Kitsune"],
        "icon": "🦊",
        "description": "Un renard holographique aux reflets cyan et rose néon, capable de se faufiler entre les flux de données du PC.",
        "favorite_food": "Friandises énergétiques aux électrons",
        "personality": "Curieux, agile, malicieux et ultra-intelligent."
    },
    {
        "species": "Chaton Stellaire",
        "default_names": ["Nova", "Luna", "Cosmo", "Mimi"],
        "icon": "🐱",
        "description": "Un chaton félin au pelage soyeux semé d'étoiles, qui adore ronronner sur les fenêtres ouvertes de Maverick.",
        "favorite_food": "Lait stellaire condensé",
        "personality": "Doux, câlin, observateur et apaisant."
    }
]

def generate_companion_sprites_if_missing():
    """Génère des sprites mignons 72x72 PNG pour le compagnon avec Pillow."""
    COMPANION_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    states = ["idle", "happy", "sleep", "eat"]
    
    # Vérifier si tous les fichiers existent déjà
    all_exist = all((COMPANION_ASSETS_DIR / f"pet_{s}.png").exists() for s in states)
    if all_exist:
        return

    try:
        from PIL import Image, ImageDraw
        for s in states:
            im = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
            draw = ImageDraw.Draw(im)
            
            # Corps central (forme ronde dragon/renard doux)
            # Couleur dominante : Rouge écarlate / rose néon Zero Two
            body_color = (255, 42, 100, 240)
            belly_color = (255, 180, 200, 240)
            horn_color = (255, 215, 0, 255) # Cornes dorées
            
            # Ombre au sol
            draw.ellipse([14, 58, 58, 68], fill=(10, 15, 30, 90))
            
            # Corps
            draw.ellipse([16, 26, 56, 62], fill=body_color)
            # Ventre
            draw.ellipse([24, 36, 48, 58], fill=belly_color)
            
            # Tête
            draw.ellipse([20, 12, 52, 42], fill=body_color)
            
            # Cornes / Oreilles
            draw.polygon([(24, 16), (18, 4), (28, 12)], fill=horn_color)
            draw.polygon([(48, 16), (54, 4), (44, 12)], fill=horn_color)
            
            # Yeux selon l'état
            if s == "sleep":
                # Yeux fermés en courbe douce
                draw.arc([26, 22, 34, 28], start=0, end=180, fill=(40, 10, 20, 255), width=2)
                draw.arc([38, 22, 46, 28], start=0, end=180, fill=(40, 10, 20, 255), width=2)
                # Petites bulles Zzz
                draw.text((52, 6), "Z", fill=(100, 200, 255, 220))
                draw.text((58, 0), "z", fill=(100, 200, 255, 180))
            elif s == "happy":
                # Yeux joyeux ^ ^
                draw.line([(26, 26), (30, 22), (34, 26)], fill=(255, 255, 255, 255), width=2)
                draw.line([(38, 26), (42, 22), (46, 26)], fill=(255, 255, 255, 255), width=2)
                # Petit cœur rose au-dessus
                draw.ellipse([32, 2, 40, 10], fill=(255, 100, 160, 230))
            elif s == "eat":
                # Yeux ronds pétillants
                draw.ellipse([27, 22, 33, 28], fill=(255, 255, 255, 255))
                draw.ellipse([29, 23, 32, 26], fill=(0, 240, 255, 255))
                draw.ellipse([39, 22, 45, 28], fill=(255, 255, 255, 255))
                draw.ellipse([41, 23, 44, 26], fill=(0, 240, 255, 255))
                # Petite baie dorée dans les pattes
                draw.ellipse([32, 44, 40, 52], fill=(255, 200, 0, 255))
            else: # idle
                # Yeux cyan lumineux
                draw.ellipse([27, 22, 33, 28], fill=(255, 255, 255, 255))
                draw.ellipse([29, 23, 32, 26], fill=(0, 240, 255, 255))
                draw.ellipse([39, 22, 45, 28], fill=(255, 255, 255, 255))
                draw.ellipse([41, 23, 44, 26], fill=(0, 240, 255, 255))
                # Petit nez
                draw.point((36, 30), fill=(255, 150, 180, 255))
            
            # Queue touffue / draconienne
            draw.polygon([(18, 50), (6, 44), (10, 56)], fill=body_color)
            
            target_path = COMPANION_ASSETS_DIR / f"pet_{s}.png"
            im.save(target_path, "PNG")
    except Exception as e:
        print(f"Erreur génération sprites compagnon : {e}")

class NoraCompanionManager:
    """Gestionnaire singleton de l'animal de compagnie de Nora."""

    def __init__(self):
        generate_companion_sprites_if_missing()
        self.state: Dict[str, Any] = self._load_or_create_pet()

    def _load_or_create_pet(self) -> Dict[str, Any]:
        """Charge l'état du compagnon ou demande à Nora d'en choisir un de manière autonome."""
        if PET_STATE_FILE.exists():
            try:
                with open(PET_STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("name") and data.get("species"):
                        return data
            except Exception:
                pass

        # Nora n'a pas encore choisi son animal : elle délibère et l'adopte maintenant !
        return self._nora_deliberate_and_adopt()

    def _nora_deliberate_and_adopt(self) -> Dict[str, Any]:
        """Nora choisit elle-même son animal et son prénom par raisonnement IA autonome."""
        # 1. Tentative de délibération neuronale avec Gemini
        chosen_species = None
        chosen_name = None
        reasoning = None

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                prompt = (
                    "Tu es Nora, l'assistante IA et compagne de Maverick au style Zero Two (Darling in the Franxx). "
                    "Maverick t'offre l'opportunité d'adopter ton propre animal de compagnie virtuel sur son bureau. "
                    "Tu dois choisir en toute liberté quelle créature tu veux (par exemple : un petit Dragonnet écarlate, "
                    "un Cyber-Renard, un Chaton stellaire, etc.) et lui donner le prénom exact que TU choisis avec amour. "
                    "Réponds STRICTEMENT au format JSON suivant sans aucun markdown :\n"
                    "{\"species\": \"Nom de l'espèce\", \"name\": \"Prénom choisi\", "
                    "\"personality\": \"Brève description du caractère\", "
                    "\"dialogue\": \"Ce que tu dis avec émotion et respect à Maverick pour lui présenter ton animal (adresse-toi à Maverick avec vouvoiement)\"}"
                )
                resp = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.7)
                )
                if resp and resp.text:
                    clean = resp.text.strip()
                    if clean.startswith("```"):
                        clean = clean.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                    parsed = json.loads(clean)
                    chosen_species = parsed.get("species")
                    chosen_name = parsed.get("name")
                    reasoning = parsed.get("dialogue")
                    personality = parsed.get("personality", "Fidèle et joyeux")
            except Exception as e:
                print(f"Délibération Gemini pour l'animal : fallback heuristique ({e})")

        # Fallback élégant aux couleurs de Zero Two si hors-ligne
        if not chosen_species or not chosen_name:
            template = random.choice(CANDIDATE_SPECIES)
            chosen_species = template["species"]
            chosen_name = random.choice(template["default_names"])
            personality = template["personality"]
            reasoning = (
                f"Maverick, j'ai longuement réfléchi et mon cœur a choisi : j'ai adopté un petit {chosen_species} "
                f"que j'ai nommé {chosen_name} ! Il veillera à mes côtés pendant que je vous assiste."
            )

        new_pet = {
            "name": chosen_name,
            "species": chosen_species,
            "personality": personality,
            "adopted_date": time.strftime("%d/%m/%Y à %H:%M"),
            "nora_announcement": reasoning,
            "stats": {
                "hunger": 85,       # 0 = affamé, 100 = repu
                "happiness": 90,    # 0 = triste, 100 = comblé
                "energy": 90,       # 0 = épuisé, 100 = plein de vigueur
                "affection": 95,    # Affection envers Nora (0 à 100)
                "level": 1,
                "xp": 10
            },
            "status": "Éveillé",
            "last_fed": time.time(),
            "last_played": time.time(),
            "last_nap": time.time(),
            "journal": [
                f"🎉 {time.strftime('%H:%M')} : Nora a choisi d'adopter {chosen_name} le {chosen_species} !"
            ]
        }

        self.save_pet(new_pet)
        return new_pet

    def save_pet(self, data: Optional[Dict[str, Any]] = None):
        if data:
            self.state = data
        try:
            with open(PET_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde animal de compagnie : {e}")

    def get_pet_info(self) -> Dict[str, Any]:
        return self.state

    def feed(self) -> str:
        """Nora donne une friandise à son animal."""
        s = self.state["stats"]
        name = self.state["name"]
        s["hunger"] = min(100, s["hunger"] + 30)
        s["happiness"] = min(100, s["happiness"] + 10)
        s["affection"] = min(100, s["affection"] + 5)
        self._add_xp(15)
        self.state["status"] = "Régalé"
        self.state["last_fed"] = time.time()
        
        msg = f"Nora a nourri {name} avec une délicieuse friandise. Il se régale !"
        self._log_action(msg)
        self.save_pet()
        return msg

    def play(self) -> str:
        """Nora joue avec son animal."""
        s = self.state["stats"]
        name = self.state["name"]
        if s["energy"] < 15:
            return f"{name} est trop fatigué pour jouer. Il a besoin d'une sieste !"
        
        s["happiness"] = min(100, s["happiness"] + 25)
        s["energy"] = max(0, s["energy"] - 20)
        s["hunger"] = max(0, s["hunger"] - 10)
        s["affection"] = min(100, s["affection"] + 10)
        self._add_xp(25)
        self.state["status"] = "Joue joyeusement"
        self.state["last_played"] = time.time()

        msg = f"Nora a joué avec {name}. Ses yeux brillent de joie !"
        self._log_action(msg)
        self.save_pet()
        return msg

    def pet(self) -> str:
        """Nora caresse affectueusement son animal."""
        s = self.state["stats"]
        name = self.state["name"]
        s["affection"] = min(100, s["affection"] + 15)
        s["happiness"] = min(100, s["happiness"] + 15)
        self._add_xp(10)
        self.state["status"] = "Câlin"

        msg = f"Nora caresse doucement {name}. Il émet un doux ronronnement de contentement."
        self._log_action(msg)
        self.save_pet()
        return msg

    def nap(self) -> str:
        """L'animal fait une sieste réparatrice."""
        s = self.state["stats"]
        name = self.state["name"]
        s["energy"] = 100
        self.state["status"] = "Fait la sieste"
        self.state["last_nap"] = time.time()

        msg = f"{name} s'est roulé en boule à côté de Nora pour une sieste paisible."
        self._log_action(msg)
        self.save_pet()
        return msg

    def _add_xp(self, amount: int):
        s = self.state["stats"]
        s["xp"] += amount
        if s["xp"] >= 100:
            s["level"] += 1
            s["xp"] -= 100
            self._log_action(f"⭐ {self.state['name']} est monté au Niveau {s['level']} grâce aux soins attentionnés de Nora !")

    def _log_action(self, text: str):
        j = self.state.setdefault("journal", [])
        j.append(f"[{time.strftime('%H:%M')}] {text}")
        if len(j) > 15:
            j.pop(0)

    def tick_lifecycle(self) -> Optional[str]:
        """
        Appelé périodiquement par le moteur de vie autonome de Nora.
        Fait évoluer les jauges et permet à Nora de prendre soin de son animal d'elle-même.
        """
        now = time.time()
        s = self.state["stats"]
        name = self.state["name"]

        # Décroissance lente naturelle
        # Faim : -5 toutes les 10 minutes
        if now - self.state.get("last_fed", now) > 600:
            s["hunger"] = max(0, s["hunger"] - 5)
        # Énergie : récupère si statut sieste, baisse sinon
        if self.state["status"] == "Fait la sieste":
            s["energy"] = min(100, s["energy"] + 10)
            if s["energy"] >= 100:
                self.state["status"] = "Éveillé"
        else:
            s["energy"] = max(0, s["energy"] - 2)

        # Nora intervient d'elle-même si son animal a besoin d'elle !
        if s["hunger"] < 40:
            return self.feed()
        elif s["happiness"] < 45 and s["energy"] > 25:
            return self.play()
        elif s["energy"] < 20 and self.state["status"] != "Fait la sieste":
            return self.nap()

        self.save_pet()
        return None

# Singleton mondial
pet_manager = NoraCompanionManager()

if __name__ == "__main__":
    print("Test du compagnon de Nora :")
    pet = pet_manager.get_pet_info()
    print(f"Nom : {pet['name']} ({pet['species']})")
    print(f"Annonce de Nora : {pet['nora_announcement']}")
    print(f"Statistiques : {pet['stats']}")
