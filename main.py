"""
Interface Principale pour piloter le Réseau d'Agents IA Autonomes (PC & Web).
"""
import sys
from colorama import Fore, Style, init
from mission_engine import run_autonomous_mission
from agent_core import run_agent_turn

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

init(autoreset=True)

BANNER = f"""
{Fore.MAGENTA}========================================================================
       🚀 SYSTÈME MULTI-AGENTS IA AUTONOMES (PC & INTERNET) - GEMINI
========================================================================{Style.RESET_ALL}
{Fore.CYAN}Comment ça marche ?{Style.RESET_ALL}
Vous donnez un **OBJECTIF GLOBAL (Mission)**, et l'équipe d'agents prend les commandes :
 - 👑 {Fore.CYAN}Chef d'orchestre{Style.RESET_ALL} : Découpe votre objectif en plan d'action multi-étapes.
 - 💻 {Fore.BLUE}Agent PC{Style.RESET_ALL} : Trie vos dossiers, isole les doublons, crée des fichiers, etc.
 - 🌐 {Fore.YELLOW}Agent Web{Style.RESET_ALL} : Fait des recherches, navigue, extrait des articles, captures.
 - 🕵️ {Fore.GREEN}Agent Auditeur{Style.RESET_ALL} : Vérifie le résultat et livre le bilan final.

{Fore.YELLOW}Exemples de Missions à lui confier :{Style.RESET_ALL}
 1. "Réorganise mon dossier Téléchargements, isole les doublons et donne-moi l'espace récupéré."
 2. "Fais une recherche sur les 3 sorties IA de la semaine et crée un dossier 'Veille_IA' sur mon Bureau avec un fichier resume.md."
 3. "Nettoie mon Bureau, range les captures d'écran et prépare un compte-rendu."

{Fore.RED}Tapez 'exit' pour quitter.{Style.RESET_ALL}
------------------------------------------------------------------------
"""

def main():
    print(BANNER)
    while True:
        try:
            mission_prompt = input(f"{Fore.MAGENTA}Votre Mission > {Style.RESET_ALL}").strip()
            
            if not mission_prompt:
                continue

            if mission_prompt.lower() in ["exit", "quitter", "q"]:
                print(f"\n{Fore.CYAN}Fin de session. À bientôt ! 👋{Style.RESET_ALL}")
                break

            # Lancement de la mission autonome
            run_autonomous_mission(mission_prompt)

        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}Mission interrompue. À bientôt ! 👋{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"\n{Fore.RED}Erreur lors de la mission : {str(e)}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()
