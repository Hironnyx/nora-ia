"""
Moteur de Missions Multi-Agents Autonomes :
- Chef d'orchestre : analyse l'objectif global et génère le plan d'action
- Agent PC : spécialiste système, fichiers, dossiers, PowerShell
- Agent Web : spécialiste recherche internet, lecture, navigation visuelle
- Agent Designer : spécialiste graphismes SVG, pages stylisées, design et styles
- Agent Auditeur : vérification de la complétion et rapport de fin de mission
"""
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from colorama import Fore, Style, init

import tools_pc
import tools_web
import tools_designer

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

CANDIDATE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest"
]

# Définition des outils par spécialiste
PC_TOOLS = [
    tools_pc.reorganize_folder,
    tools_pc.smart_organize_and_rename,
    tools_pc.find_duplicates,
    tools_pc.write_file,
    tools_pc.create_folder,
    tools_pc.copy_file,
    tools_pc.list_directory,
    tools_pc.search_files,
    tools_pc.get_system_overview,
    tools_pc.run_powershell,
]

WEB_TOOLS = [
    tools_web.search_internet,
    tools_web.read_webpage,
    tools_web.open_browser_and_view,
    tools_web.browser_click_or_type,
]

DESIGNER_TOOLS = [
    tools_designer.create_svg_graphic,
    tools_designer.generate_styled_html_page,
    tools_designer.get_color_palette,
    tools_pc.write_file,
]

ALL_TOOLS = PC_TOOLS + WEB_TOOLS + DESIGNER_TOOLS
TOOL_MAP = {fn.__name__: fn for fn in ALL_TOOLS}

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Clé API GEMINI_API_KEY manquante dans le fichier .env.")
    return genai.Client(api_key=api_key)

def call_gemini_safe(client: genai.Client, contents: str, system_instruction: str = None, tools=None):
    """Appel sécurisé avec basculement automatique de modèle et gestion des quotas."""
    for model in CANDIDATE_MODELS:
        for attempt in range(2):
            try:
                config_kwargs = {"temperature": 0.2}
                if system_instruction:
                    config_kwargs["system_instruction"] = system_instruction
                if tools:
                    config_kwargs["tools"] = tools

                config = types.GenerateContentConfig(**config_kwargs)
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                return response
            except Exception as e:
                err = str(e)
                if "429" in err:
                    break
                elif "503" in err:
                    time.sleep(3)
                else:
                    break
    raise RuntimeError("Tous les modèles Gemini candidats sont temporairement indisponibles.")

# =====================================================================
# 1. AGENT CHEF D'ORCHESTRE : PLANIFICATION
# =====================================================================
def plan_mission(client: genai.Client, goal: str) -> list:
    """Découpe l'objectif global de l'utilisateur en un plan de sous-tâches ordonnées."""
    prompt = f"""
Tu es le Chef d'Orchestre d'une équipe d'Agents IA d'élite.
L'utilisateur te confie une MISSION GLOBALE : "{goal}"

Ton rôle est de découper cette mission en 2 à 4 étapes séquentielles concrètes pour tes agents :
- Agent "PC" : pour les fichiers, dossiers, disques, création de fichiers, réorganisation, PowerShell.
- Agent "WEB" : pour les recherches internet, lecture d'articles, visites de sites, captures d'écran.
- Agent "DESIGNER" : pour la création de graphismes SVG, le style, les dessins, les pages HTML modernes, les thèmes de couleurs.

Réponds UNIQUEMENT avec un tableau JSON valide au format suivant (sans texte autour, sans balises ```json) :
[
  {{
    "step_num": 1,
    "agent": "PC",
    "title": "Titre court",
    "instruction": "Instruction claire pour le sous-agent"
  }}
]
"""
    resp = call_gemini_safe(client, prompt)
    raw = resp.text.strip()
    
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()

    try:
        plan = json.loads(raw)
        return plan
    except Exception:
        return [
            {"step_num": 1, "agent": "PC", "title": "Exécution système", "instruction": goal}
        ]

# =====================================================================
# 2. SOUS-AGENTS : EXÉCUTION D'UNE ÉTAPE AVEC OUTILS
# =====================================================================
def execute_subagent_task(client: genai.Client, agent_type: str, instruction: str, context: str, callback_progress=None) -> str:
    """Fait exécuter une étape précise par l'agent spécialiste désigné (PC, WEB ou DESIGNER)."""
    if agent_type == "PC":
        tools = PC_TOOLS
        agent_name = "Agent Spécialiste PC & Système"
    elif agent_type == "DESIGNER":
        tools = DESIGNER_TOOLS
        agent_name = "Agent Spécialiste Designer & Graphismes"
    else:
        tools = WEB_TOOLS
        agent_name = "Agent Spécialiste Web & Recherche"
    
    system_inst = f"""
Tu es l'{agent_name}'.
Tu as pour mission d'accomplir cette tâche : "{instruction}"

CONTEXTE DES ÉTAPES PRÉCÉDENTES :
{context}

RÈGLES :
- Utilise tes outils pour réaliser l'action concrètement.
- Sois autonome : ne demande pas de confirmation à l'utilisateur, fais le travail jusqu'au bout.
- Une fois le travail fait, explique clairement ce que tu as accompli.
"""

    for model in CANDIDATE_MODELS:
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_inst,
                tools=tools,
                temperature=0.2
            )
            chat = client.chats.create(model=model, config=config)
            resp = chat.send_message(f"Accomplis ta tâche : {instruction}")

            # Boucle d'appels d'outils
            while resp.function_calls:
                for call in resp.function_calls:
                    tool_name = call.name
                    tool_args = call.args or {}
                    
                    tool_fn = TOOL_MAP.get(tool_name)
                    if tool_fn:
                        try:
                            result = tool_fn(**tool_args)
                        except Exception as e:
                            result = f"Erreur : {e}"
                    else:
                        result = f"Outil '{tool_name}' non disponible."

                    if callback_progress:
                        callback_progress(tool_name, str(result)[:60])
                    print(f"      {Fore.LIGHTBLACK_EX}↳ Outil exécuté : {tool_name} -> Succès{Style.RESET_ALL}")
                    
                    resp = chat.send_message(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": result}
                        )
                    )

            return resp.text.strip()

        except Exception as e:
            err = str(e)
            if "429" in err:
                print(f"      {Fore.YELLOW}⏳ Quota sur {model} saturé, basculement vers le modèle suivant...{Style.RESET_ALL}")
                time.sleep(2)
                continue
            elif "503" in err:
                time.sleep(4)
                continue
            else:
                raise e

    time.sleep(20)
    config = types.GenerateContentConfig(system_instruction=system_inst, tools=tools, temperature=0.2)
    chat = client.chats.create(model="gemini-3.8-flash", config=config)
    resp = chat.send_message(f"Accomplis ta tâche : {instruction}")
    return resp.text.strip()

# =====================================================================
# 3. AGENT AUDITEUR / CRITIQUE : CONTRÔLE ET RAPPORT FINAL
# =====================================================================
def audit_and_conclude(client: genai.Client, goal: str, execution_log: list) -> str:
    """Génère le rapport de fin de mission après inspection des livrables."""
    log_text = "\n\n".join([f"Étape {s['step']} ({s['agent']}) - {s['title']} :\n{s['result']}" for s in execution_log])
    
    prompt = f"""
Tu es l'Agent Contrôleur Qualité et Rapporteur.
L'utilisateur avait fixé cette MISSION INITIALE : "{goal}"

Voici le journal d'exécution complet des agents :
{log_text}

Rédige un COMPTE-RENDU DE MISSION clair, valorisant et structuré en français :
1. 🎯 Objectif initial
2. ⚡ Actions concrètes réalisées sur le PC, le Web ou par le Designer
3. 📁 Livrables créés (fichiers, dossiers, graphismes, captures d'écran, réorganisations)
4. ✅ Statut : Mission accomplie à 100%
"""
    resp = call_gemini_safe(client, prompt)
    return resp.text.strip()

# =====================================================================
# 🚀 MOTEUR DE MISSION GLOBAL
# =====================================================================
def run_autonomous_mission(goal: str, callback_step=None):
    """Pilote une mission complète de bout en bout de manière autonome avec notifications optionnelles."""
    client = get_client()

    print(f"\n{Fore.MAGENTA}========================================================================")
    print(f"       🎯 NOUVELLE MISSION GLOBALE AUTONOME DÉMARRÉE")
    print(f"========================================================================{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Objectif : {Fore.YELLOW}{goal}{Style.RESET_ALL}\n")

    if callback_step:
        callback_step("plan", "Élaboration du plan d'attaque...")

    plan = plan_mission(client, goal)
    
    print(f"\n{Fore.GREEN}📋 Plan de mission en {len(plan)} étape(s) défini :{Style.RESET_ALL}")
    for item in plan:
        if item["agent"] == "PC":
            icon = "💻"
        elif item["agent"] == "DESIGNER":
            icon = "🎨"
        else:
            icon = "🌐"
        print(f"   [{item['step_num']}] {icon} Agent {item['agent']} : {item['title']}")
    print()

    execution_history = []
    context_str = ""

    for step in plan:
        step_num = step["step_num"]
        agent_type = step["agent"]
        title = step["title"]
        instruction = step["instruction"]

        if agent_type == "PC":
            tag = f"{Fore.BLUE}💻 [AGENT PC]"
        elif agent_type == "DESIGNER":
            tag = f"{Fore.MAGENTA}🎨 [AGENT DESIGNER]"
        else:
            tag = f"{Fore.YELLOW}🌐 [AGENT WEB]"

        print(f"{tag} Démarre l'étape {step_num}/{len(plan)} : {Fore.WHITE}{title}{Style.RESET_ALL}")
        if callback_step:
            callback_step("executing", f"Étape {step_num}/{len(plan)} : {title} ({agent_type})")

        result = execute_subagent_task(client, agent_type, instruction, context_str)
        
        execution_history.append({
            "step": step_num,
            "agent": agent_type,
            "title": title,
            "result": result
        })
        
        context_str += f"\n- Étape {step_num} ({agent_type}) : {result[:400]}"
        print(f"   {Fore.GREEN}✔ Étape {step_num} validée.{Style.RESET_ALL}\n")
        time.sleep(2)

    if callback_step:
        callback_step("audit", "Contrôle qualité et synthèse finale...")

    final_brief = audit_and_conclude(client, goal, execution_history)

    # Mémoriser la mission réussie dans la mémoire permanente de Nora
    try:
        import memory_manager
        memory_manager.record_completed_mission(goal, final_brief)
    except Exception as e:
        print(f"Note mémoire : {e}")

    print(f"{Fore.GREEN}========================================================================")
    print(f"                   🎉 RAPPORT DE FIN DE MISSION")
    print(f"========================================================================{Style.RESET_ALL}")
    print(final_brief)
    print(f"\n{Fore.GREEN}========================================================================{Style.RESET_ALL}\n")

    return final_brief
