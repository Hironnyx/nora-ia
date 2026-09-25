"""
Module de Vision d'Écran Multimodale pour Nora :
- Capture d'écran haute performance via PyQt6
- Analyse visuelle en direct avec Gemini 3.6 Flash
- Personnalité fidèle de Zero Two (taquine, perspicace, loyale et protectrice)
"""
import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QBuffer, QIODevice
from google import genai
from google.genai import types

import memory_manager

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    _app_dir = Path(sys.executable).parent
else:
    _app_dir = Path(__file__).resolve().parent
load_dotenv(_app_dir / ".env")
load_dotenv()

VISION_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest"
]

def capture_active_screen() -> Image.Image:
    """Capture l'écran principal ou actif et retourne un objet PIL Image optimisé."""
    # S'assurer qu'une QApplication existe (créée par desktop_pet)
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    screen = QApplication.primaryScreen()
    if not screen:
        raise RuntimeError("Impossible de détecter l'écran principal.")

    # Capture native de l'écran entier
    pixmap = screen.grabWindow(0)

    # Conversion efficace en mémoire tampon JPEG (qualité 85 pour un envoi ultra-rapide)
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.ReadWrite)
    pixmap.save(buffer, "JPEG", quality=85)
    
    image_bytes = buffer.data().data()
    pil_image = Image.open(io.BytesIO(image_bytes))
    return pil_image

def analyze_screen_with_gemini(user_prompt: str = "") -> dict:
    """
    Capture l'écran et l'envoie à Gemini avec la personnalité de Zero Two.
    Retourne {'status': 'ok', 'speech': '...', 'summary': '...'}
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "speech": "Maverick, la clé GEMINI_API_KEY est manquante pour l'analyse visuelle.",
            "summary": "GEMINI_API_KEY manquante."
        }

    try:
        screen_img = capture_active_screen()
    except Exception as e:
        return {
            "status": "error",
            "speech": f"Impossible de capturer l'écran actuellement, Maverick ({e}).",
            "summary": str(e)
        }

    user_name = memory_manager.get_user_name()
    client = genai.Client(api_key=api_key)

    custom_question = user_prompt.strip() if user_prompt else "Que vois-tu sur mon écran ?"

    system_instructions = f"""
Tu es Nora, assistante IA avancée et copilote d'ingénierie logicielle et matérielle.
Tu analyses l'écran de travail de Maverick ({user_name}).

CONSIGNES STRICTES :
1. Analyse avec rigueur ce qui est affiché à l'écran : éditeur de code, terminal, logiciel de CAO/3D (PrusaSlicer), documentation, alertes système ou navigateur.
2. Si Maverick a posé une question précise ("{custom_question}"), réponds-y directement avec précision technique.
3. Si la demande est générale, résume brièvement le contexte opérationnel en cours et formule une observation utile.
4. RÈGLES DE COMMUNICATION :
   - Adresse-toi systématiquement à Maverick en utilisant son nom ("Maverick") et le VOUVOIEMENT STRICT.
   - N'utilise JAMAIS le mot "Darling" ni aucun surnom familier ou enfantin.
   - Ton de voix : professionnel, sobre, posé et hautement compétent.
   - Réponse VIVE, PERCUTANTE et COURTE (2 à 3 phrases maximum, environ 30 à 45 mots).
"""

    prompt = f"Voici la capture de mon écran. Demande de Maverick : {custom_question}"

    for model in VISION_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=[screen_img, prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_instructions,
                    temperature=0.3
                )
            )
            text = response.text.strip()
            return {
                "status": "ok",
                "speech": text,
                "summary": text
            }
        except Exception:
            continue

    return {
        "status": "error",
        "speech": "L'analyse optique de l'écran n'a pas pu aboutir, Maverick. Veuillez relancer la capture.",
        "summary": "Échec de l'appel vision Gemini."
    }

if __name__ == "__main__":
    print("Test capture et analyse d'écran...")
    res = analyze_screen_with_gemini("Qu'est-ce que tu vois sur mon écran ?")
    print("Résultat :", res["speech"])
