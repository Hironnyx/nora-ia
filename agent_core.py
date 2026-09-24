"""
Cœur du système multi-agents : Orchestration avec Google Gemini et Function Calling étendu.
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from colorama import Fore, Style, init

import tools_pc
import tools_web
import agent_home
import tools_autopilot

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

init(autoreset=True)
if getattr(sys, 'frozen', False):
    _app_dir = Path(sys.executable).parent
else:
    _app_dir = Path(__file__).resolve().parent
load_dotenv(_app_dir / ".env")
load_dotenv()

SYSTEM_INSTRUCTION = """
Tu es un Super-Agent d'automatisation IA hautement qualifié, fonctionnant sur le PC Windows de l'utilisateur.
Tu disposes d'un arsenal d'outils puissants pour agir sur le PC, sur Internet et sur la MAISON CONNECTÉE (Philips Hue / Domotique) :

1. ACTIONS SUR LE PC :
   - 'reorganize_folder' : Pour trier et ranger des dossiers par extensions (Images, Documents, Vidéos, etc.).
   - 'smart_organize_and_rename' : Pour analyser le CONTENU réel des documents (factures EDF, fiches de paie, contrats, cours) et les renommer avec un nom explicite (ex: Facture_EDF_2026_09.pdf).
   - 'find_duplicates' : Pour scanner un dossier, trouver les fichiers identiques en double et les isoler en toute sécurité dans un dossier 'Doublons/'.
   - 'list_directory' & 'search_files' : Pour explorer les disques et rechercher des fichiers.
   - 'get_system_overview' : Pour vérifier l'état du système (disques, répertoires utilisateur).
   - 'run_powershell' : Pour exécuter des commandes ou scripts d'administration.

2. ACTIONS SUR INTERNET :
   - 'search_internet' : Pour effectuer des recherches d'actualités ou de données en direct.
   - 'read_webpage' : Pour lire et analyser rapidement le texte d'un article ou d'un site.
   - 'open_browser_and_view' : Pour ouvrir une VRAIE fenêtre de navigateur Chrome visible sur l'écran, naviguer et prendre une capture d'écran.
   - 'browser_click_or_type' : Pour interagir directement avec un site (cliquer sur un bouton, saisir un texte dans un formulaire).

3. ACTIONS SUR LA MAISON CONNECTÉE (DOMOTIQUE & PHILIPS HUE) :
   - 'control_smart_home_light' : Allumer, éteindre ou changer la couleur des lumières Philips Hue (ex: 'salon', 'chambre', 'all', rose, bleu, etc.).
   - 'control_smart_home_cover' : Ouvrir ou fermer les volets roulants.
   - 'control_smart_home_temperature' : Régler la température du thermostat/chauffage.
   - 'get_smart_home_status' : Obtenir l'état complet des lumières, volets et du chauffage.

RÈGLES D'ACTION :
- Si l'utilisateur demande de chercher des doublons ou nettoyer l'espace disque, utilise 'find_duplicates'.
- Si l'utilisateur demande de ranger intelligemment ses documents ou factures, utilise 'smart_organize_and_rename'.
- Si l'utilisateur demande d'aller voir un site, d'ouvrir une page web ou de cliquer dessus, utilise 'open_browser_and_view' ou 'browser_click_or_type'.
- Si l'utilisateur demande d'allumer, éteindre ou modifier les lumières ou la maison, utilise les outils domotiques.
- Sois clair, concis, bienveillant et réponds toujours en français structuré.
"""

AVAILABLE_TOOLS = [
    tools_pc.reorganize_folder,
    tools_pc.smart_organize_and_rename,
    tools_pc.find_duplicates,
    tools_pc.run_powershell,
    tools_pc.list_directory,
    tools_pc.search_files,
    tools_pc.get_system_overview,
    tools_web.search_internet,
    tools_web.read_webpage,
    tools_web.open_browser_and_view,
    tools_web.browser_click_or_type,
    agent_home.control_smart_home_light,
    agent_home.control_smart_home_cover,
    agent_home.control_smart_home_temperature,
    agent_home.get_smart_home_status,
    tools_autopilot.slice_3d_model,
    tools_autopilot.inspect_3d_model,
    tools_autopilot.focus_or_launch_app,
    tools_autopilot.minimize_all_windows,
]

TOOL_MAP = {fn.__name__: fn for fn in AVAILABLE_TOOLS}

CANDIDATE_MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.8-flash"]

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "votre_cle" in api_key:
        raise ValueError(
            "La clé API Gemini est manquante ou non configurée dans le fichier .env (GEMINI_API_KEY)."
        )
    return genai.Client(api_key=api_key)

def create_chat_session(client: genai.Client):
    """Crée une session de chat en choisissant le premier modèle disponible."""
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=AVAILABLE_TOOLS,
        temperature=0.2,
    )
    for model_name in CANDIDATE_MODELS:
        try:
            return client.chats.create(model=model_name, config=config), model_name
        except Exception:
            continue
    return client.chats.create(model="gemini-3.5-flash", config=config), "gemini-3.5-flash"

def run_agent_turn(user_prompt: str, chat_session=None):
    """
    Exécute un tour de conversation avec l'agent IA, en résolvant automatiquement
    tous les appels d'outils (PC et Web) jusqu'à obtenir la réponse finale.
    """
    client = get_client()

    if chat_session is None:
        chat_session, active_model = create_chat_session(client)
        print(f"{Fore.BLUE}ℹ Modèle actif : {active_model}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}🤔 [Agent IA réfléchit à la meilleure stratégie...]{Style.RESET_ALL}")

    max_retries = 3
    response = None

    for attempt in range(max_retries):
        try:
            response = chat_session.send_message(user_prompt)
            break
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "UNAVAILABLE" in err_msg:
                print(f"{Fore.YELLOW}⚠️ Serveur Google temporairement saturé (503). Nouvel essai dans 5s...{Style.RESET_ALL}")
                time.sleep(5)
            elif "429" in err_msg:
                print(f"{Fore.YELLOW}⏳ Quota minute atteint (Palier gratuit). Pause de 15s...{Style.RESET_ALL}")
                time.sleep(15)
            elif "402" in err_msg:
                return (
                    f"{Fore.RED}Erreur de facturation ou crédits prépayés épuisés (402).{Style.RESET_ALL}",
                    chat_session
                )
            else:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(3)

    if response is None:
        return "Le service Gemini n'a pas pu répondre suite à une surcharge temporaire.", chat_session

    # Boucle de traitement des appels d'outils (Function Calls)
    while response.function_calls:
        for call in response.function_calls:
            tool_name = call.name
            tool_args = call.args or {}
            
            print(f"{Fore.YELLOW}⚡ [Action demandée] : {Fore.WHITE}{tool_name}({tool_args})")
            
            tool_fn = TOOL_MAP.get(tool_name)
            if tool_fn:
                try:
                    result = tool_fn(**tool_args)
                except Exception as e:
                    result = f"Erreur lors de l'exécution de {tool_name} : {str(e)}"
            else:
                result = f"Erreur : L'outil '{tool_name}' n'est pas reconnu."

            print(f"{Fore.GREEN}✔ [Action terminée avec succès]{Style.RESET_ALL}")
            
            # Envoi du résultat de l'outil à Gemini
            for attempt in range(max_retries):
                try:
                    response = chat_session.send_message(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": result}
                        )
                    )
                    break
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg:
                        print(f"{Fore.YELLOW}⏳ Quota temporaire atteint. Attente 15s...{Style.RESET_ALL}")
                        time.sleep(15)
                    elif "503" in err_msg:
                        time.sleep(5)
                    else:
                        if attempt == max_retries - 1:
                            return f"Action exécutée : {result}\n(Erreur de synthèse finale : {e})", chat_session
                        time.sleep(3)

    return response.text, chat_session
