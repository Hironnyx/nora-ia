"""
Module d'outils pour l'interaction avec Internet, recherche et navigation visuelle avec Playwright.
"""
import os
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent

SCREENSHOTS_DIR = (BASE_DIR / "screenshots").resolve()
SCREENSHOTS_DIR.mkdir(exist_ok=True)

def search_internet(query: str, max_results: int = 5) -> str:
    """
    Effectue une recherche en temps réel sur Internet et renvoie les meilleurs résultats.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return f"Aucun résultat trouvé sur le web pour : '{query}'."

            formatted = [f"=== Résultats de recherche pour : {query} ==="]
            for idx, r in enumerate(results, start=1):
                formatted.append(
                    f"\n[{idx}] {r.get('title', 'Sans titre')}\n"
                    f"Lien : {r.get('href', '')}\n"
                    f"Extrait : {r.get('body', '')}"
                )
            return "\n".join(formatted)
    except Exception as e:
        return f"Erreur lors de la recherche sur Internet : {str(e)}"

def read_webpage(url: str, max_chars: int = 3500) -> str:
    """
    Télécharge et extrait le texte lisible d'une page web sans ouvrir de navigateur visible.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + f"\n... [Contenu tronqué à {max_chars} caractères]"

        return clean_text if clean_text else "Page web vide ou contenu non extractible en texte."
    except Exception as e:
        return f"Erreur lors de la lecture de la page web '{url}' : {str(e)}"

def open_browser_and_view(url: str, wait_seconds: int = 4, headless: bool = False) -> str:
    """
    Ouvre une vraie fenêtre de navigateur Chrome/Chromium visible sur votre écran,
    charge la page web demandée, prend une capture d'écran et extrait le texte visible.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    screenshot_path = SCREENSHOTS_DIR / "derniere_page.png"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless, channel=None)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if wait_seconds > 0:
                page.wait_for_timeout(wait_seconds * 1000)

            title = page.title()
            page.screenshot(path=str(screenshot_path))

            # Extraction du texte visible
            content = page.evaluate("() => document.body.innerText")
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            text_preview = "\n".join(lines[:25]) # 25 premières lignes

            browser.close()

        return (
            f"=== Navigation Réussie sur : {url} ===\n"
            f"Titre de la page : {title}\n"
            f"📸 Capture d'écran enregistrée dans : {screenshot_path}\n"
            f"\nAperçu du contenu affiché :\n{text_preview}"
        )
    except Exception as e:
        return f"Erreur lors de l'ouverture du navigateur visuel sur '{url}' : {str(e)}"

def browser_click_or_type(url: str, selector: str, text_to_type: str = None, click: bool = True, headless: bool = False) -> str:
    """
    Interagit avec un élément précis sur une page web (cliquer sur un bouton, taper du texte dans un champ).
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    screenshot_path = SCREENSHOTS_DIR / "action_page.png"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector(selector, timeout=10000)

            if text_to_type:
                page.fill(selector, text_to_type)
                action_done = f"Texte saisi dans '{selector}' : '{text_to_type}'"
            elif click:
                page.click(selector)
                action_done = f"Clic effectué sur l'élément '{selector}'"
            else:
                action_done = f"Élément '{selector}' localisé avec succès."

            page.wait_for_timeout(2000)
            page.screenshot(path=str(screenshot_path))
            browser.close()

        return (
            f"Action web réussie : {action_done}\n"
            f"📸 Capture d'écran après action : {screenshot_path}"
        )
    except Exception as e:
        return f"Erreur lors de l'interaction avec '{selector}' sur '{url}' : {str(e)}"

def autonomous_web_browse_and_summarize(query: str, visual: bool = True) -> dict:
    """
    Exécute une recherche et navigation web autonome :
    1. Recherche les meilleures pages sur DuckDuckGo
    2. Navigue sur la page principale avec Playwright et prend une capture d'écran
    3. Résume le contenu de manière claire et vivante avec l'IA
    """
    from google import genai
    from google.genai import types
    api_key = os.getenv("GEMINI_API_KEY")

    # 1. Recherche
    raw_search = search_internet(query, max_results=3)
    
    # Trouver la première URL valide dans les résultats
    import re
    urls = re.findall(r"Lien : (https?://[^\s]+)", raw_search)
    target_url = urls[0] if urls else None

    extracted_text = ""
    screenshot_file = None

    if target_url:
        if visual:
            try:
                screenshot_path = SCREENSHOTS_DIR / "web_live.png"
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": 1280, "height": 800})
                    page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(2000)
                    page.screenshot(path=str(screenshot_path))
                    content = page.evaluate("() => document.body.innerText")
                    lines = [l.strip() for l in content.splitlines() if l.strip()]
                    extracted_text = "\n".join(lines[:35])
                    browser.close()
                    screenshot_file = str(screenshot_path)
            except Exception as e:
                extracted_text = read_webpage(target_url, max_chars=2500)
        else:
            extracted_text = read_webpage(target_url, max_chars=2500)

    # Synthèse IA
    speech_summary = f"Recherche web effectuée pour Maverick sur '{query}'."
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
Tu es Nora, assistante IA et copilote technique de Maverick.
Maverick a demandé une recherche sur : "{query}".
Voici les données extraites du web :
{raw_search}

Contenu de la page explorée :
{extracted_text[:2000]}

CONSIGNES STRICTES :
- Formule une synthèse claire, technique et concise (2 à 3 phrases maximum) pour Maverick.
- Vouvoie systématiquement Maverick et ne mentionne jamais aucun surnom affectif.
"""
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            )
            speech_summary = resp.text.strip()
        except Exception:
            pass

    return {
        "success": True,
        "speech": speech_summary,
        "search_results": raw_search,
        "url": target_url,
        "screenshot": screenshot_file
    }
