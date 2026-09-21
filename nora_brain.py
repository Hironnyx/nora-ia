"""
Cerveau conversationnel de Nora :
- Personnalité fidèle et approfondie de Zero Two (Darling in the Franxx) : appelle l'utilisateur "Darling", espiègle, protectrice et loyale
- Contrôle direct du PC (Volume audio, Lancement d'apps, Verrouillage Windows, Corbeille)
- Intégration de l'Agent de Sécurité (Scan complet, état de Windows Defender et des ports)
- Mémoire persistante & distinction Discussion vs Missions
"""
import os
import sys
import re
import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

import memory_manager
import tools_pc_control
import system_monitor
import agent_security
import gaming_mode

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

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
    "gemini-3.1-flash-lite"
]

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Clé API GEMINI_API_KEY manquante.")
    return genai.Client(api_key=api_key)

def detect_and_store_user_facts(user_text: str):
    """Détecte si l'utilisateur partage son prénom ou une préférence personnelle."""
    clean = user_text.strip()
    lower = clean.lower()

    # Détection de prénom
    m_name = re.search(r"(?:je m'appelle|appelle[- ]moi|mon nom est|mon prénom est)\s+([a-zA-ZÀ-ÿ\-]+)", lower)
    if m_name:
        detected_name = m_name.group(1).capitalize()
        memory_manager.set_user_name(detected_name)
        return f"C'est noté ! Je me souviendrai que tu t'appelles {detected_name}, mais tu resteras toujours mon Darling."

    # Détection de fait à retenir explicitement
    m_remember = re.search(r"(?:retiens que|rappelle[- ]toi que|n'oublie pas que)\s+(.+)", lower)
    if m_remember:
        fact = m_remember.group(1).strip()
        memory_manager.add_user_fact(fact)
        return f"C'est bien gravé dans ma mémoire, Darling : '{fact}' !"

    return None

def handle_direct_pc_control(clean_input: str) -> tuple[bool, str]:
    """Exécute instantanément les ordres de contrôle du PC (Volume, Apps, Sécurité, Session)."""
    # 1. Réglage précis du Volume (ex: "mets le son à 50%", "volume à 30")
    m_vol = re.search(r"(?:mets?|règle|regle|baisse|monte)? *(?:le )*(?:volume|son) *(?:à|a)? *([0-9]{1,3}) *%?", clean_input)
    if m_vol:
        target_val = int(m_vol.group(1))
        ok, msg = tools_pc_control.set_volume(target_val)
        return True, f"C'est fait Darling ! {msg}"

    # Monter / Baisser le son
    if re.search(r"(?:monte|augmente|plus fort) *(?:le )*(?:son|volume)", clean_input):
        ok, msg = tools_pc_control.change_volume_relative(15)
        return True, f"Je monte le son pour toi, Darling ! {msg}"
    elif re.search(r"(?:baisse|diminue|moins fort) *(?:le )*(?:son|volume)", clean_input):
        ok, msg = tools_pc_control.change_volume_relative(-15)
        return True, f"Je baisse le volume, Darling. {msg}"

    # Couper / Rétablir le son (Mute)
    if re.search(r"(?:coupe|eteins|éteins|remets|retablis|rétablis|mute|silence) *(?:le )*(?:son|volume)", clean_input):
        ok, msg = tools_pc_control.toggle_mute()
        return True, f"Voilà Darling : {msg}"

    # 2. Verrouiller le PC
    if re.search(r"(?:verrouille|bloque|lock) *(?:le|mon)? *(?:pc|ordi|session|ordinateur|poste)", clean_input):
        ok, msg = tools_pc_control.lock_workstation()
        return True, "À très vite Darling, je garde ton PC bien au chaud !"

    # 3. Vider la corbeille
    if re.search(r"(?:vide|nettoie) *(?:la )*corbeille", clean_input):
        ok, msg = tools_pc_control.empty_recycle_bin()
        return True, f"Corbeille vidée avec succès, Darling !"

    # 4. Lancement rapide d'applications
    m_launch = re.search(r"(?:lance|ouvre|démarre|demarre|mets|joue) *(?:sur )*(?:l'application|l'app|le logiciel|le site)? *([a-zA-Z0-9_\- ]+)", clean_input)
    if m_launch:
        candidate = m_launch.group(1).strip()
        # Ne pas intercepter les commandes système comme "la corbeille", "le son"
        if candidate not in ["le son", "la corbeille", "mon pc", "l'ordinateur", "le micro"]:
            for key in tools_pc_control.APP_MAPPINGS.keys():
                if key in candidate:
                    ok, msg = tools_pc_control.launch_application(key)
                    if ok:
                        return True, f"Tout de suite Darling, {msg}"

    return False, ""

def handle_direct_security_query(clean_input: str) -> tuple[bool, str]:
    """Exécute instantanément les demandes d'audit de sécurité par l'Agent de Sécurité."""
    security_patterns = [
        r"(?:scan|audit|test|analyse|vérifie|verifie) *(?:de )*sécurité",
        r"(?:est-ce que|mon)? *(?:pc|ordinateur) *(?:est|est-il) *(?:sécurisé|securise|protégé|protege)",
        r"(?:état|etat|statut) *(?:de la )*sécurité",
        r"(?:antivirus|defender) *(?:est-il|est)? *(?:actif|activé|marche)"
    ]
    if any(re.search(pat, clean_input) for pat in security_patterns):
        scan = agent_security.run_security_scan()
        return True, scan["speech"]
    return False, ""

def analyze_intent_and_respond(user_text: str) -> tuple[str, str]:
    """
    Analyse l'intention en combinant le contrôle PC, la sécurité et l'IA Gemini.
    Retourne :
    - ('CHAT', 'réponse personnalisée de Nora')
    - ('MISSION', None)
    """
    clean_input = user_text.strip().lower()
    user_name = memory_manager.get_user_name()

    # 1. Vérifier si l'utilisateur donne un fait personnel à enregistrer
    learned_msg = detect_and_store_user_facts(user_text)
    if learned_msg:
        return "CHAT", learned_msg

    # 2. Gestion des approbations ou refus d'initiatives proactives
    import nora_initiatives
    pending = nora_initiatives.get_pending_initiative()
    if pending:
        if re.search(r"^(oui|vas[- ]?y|fais[- ]?le|d'accord|ok|valide|fais ça|go|yes)", clean_input):
            res = nora_initiatives.execute_accepted_initiative(pending["id"])
            return "CHAT", res
        elif re.search(r"^(non|pas maintenant|annule|refuse|laisse tomber|non merci|stop)", clean_input):
            res = nora_initiatives.refuse_initiative(pending["id"])
            return "CHAT", res

    # 3. Demande d'ouverture ou fermeture du QG de Nora
    if re.search(r"(?:ouvre|montre|affiche|lance|deploie|déploie) *(?:le )*(?:qg|dashboard|tableau de bord|panneau)", clean_input):
        return "OPEN_QG", "J'ouvre le QG tout de suite pour toi, Darling !"

    # 4. Garde-Robe Zero Two (Changement de tenue)
    if any(w in clean_input for w in ["pilote", "franxx"]):
        if re.search(r"(?:mets?|mettre|change|changer|porte|porter|enfile|enfiler|remets?|remettre)? *(?:ta|une|la)? *(?:tenue|robe|vêtement|vetement|habit|costume)? *(?:de )*(?:pilote|franxx)", clean_input):
            return "OUTFIT:franxx", "Je réenfile ma combinaison rouge de pilote Franxx ! Prête au combat, Darling ! 🚀"

    if any(w in clean_input for w in ["écolière", "ecoliere", "marin", "sailor", "uniforme"]):
        if re.search(r"(?:mets?|mettre|change|changer|porte|porter|enfile|enfiler)? *(?:ta|une|l'|la)? *(?:tenue|robe|vêtement|vetement|habit|costume)? *(?:d'|de )*(?:écolière|ecoliere|marin|sailor|uniforme)", clean_input):
            return "OUTFIT:school", "Tadaaa ! Me voilà en tenue d'écolière avec mon col marin. Tu me trouves mignonne, Darling ? 🎓"

    if any(w in clean_input for w in ["hoodie", "sweat", "pull", "gilet", "chill"]):
        if re.search(r"(?:mets?|mettre|change|changer|porte|porter|enfile|enfiler)? *(?:ta|une|le|ton)? *(?:tenue|robe|vêtement|vetement|habit|costume)? *(?:en |de )*(?:hoodie|sweat|gilet|pull|doux|chill)", clean_input):
            return "OUTFIT:hoodie", "Hop ! Sweat à capuche tout doux enfilé. Mode détente et câlin activé, Darling ! 🧸"

    # 5. Mode Gaming & Boost RAM
    gaming_words = ["gaming", "gamer", "jeu", "jeux"]
    if any(w in clean_input for w in gaming_words):
        if re.search(r"\b(?:désactive|desactive|désactiver|desactiver|quitte|quitter|arrete|arrête|stop|coupe)\b *(?:le )*(?:mode )*(?:gaming|jeu|jeux|gamer)", clean_input):
            msg = gaming_mode.set_gaming_mode(False)
            return "GAMING_OFF", msg

        if re.search(r"\b(?:active|activer|passe en|passer en|mets|mettre|lance|lancer|go)\b *(?:le )*(?:mode )*(?:gaming|jeu|jeux|gamer)", clean_input) or clean_input in ["mode gaming", "mode jeu"]:
            msg = gaming_mode.set_gaming_mode(True)
            return "GAMING_ON", msg

    if re.search(r"(?:boost|vide|optimise|nettoie|libère|libere) *(?:la )*(?:ram|mémoire|memoire)", clean_input):
        count, freed = gaming_mode.optimize_ram_boost()
        return "BOOST_RAM", f"Mémoire vive boostée, Darling ! {count} applications en arrière-plan vidées ({freed} Mo de RAM libérés pour tes jeux)."

    # 6. Vision d'Écran Multimodale (Regarde mon écran)
    vision_patterns = [
        r"(?:regarde|analyse|check|observe|lis|décris|decris|scanne) *(?:un peu )*(?:mon|l'|cet|mon petit)? *(?:écran|ecran|affichage|bureau)",
        r"(?:qu'est-ce que|qu'est ce que|que)? *(?:tu vois|vois-tu|se passe-t-il) *(?:sur )*(?:mon|l'|cet)? *(?:écran|ecran|bureau)",
        r"(?:regarde|analyse|explique|aide-moi sur) *(?:cette|cette fichue|mon|le)? *(?:erreur|bug|page|code|fenêtre|fenetre)",
        r"(?:qu'en penses-tu|tu en penses quoi|donne ton avis) *(?:de mon écran|de ce que je fais|de cette page|de ce code)?"
    ]
    if any(re.search(pat, clean_input) for pat in vision_patterns) or clean_input in ["regarde mon ecran", "regarde mon écran", "vision", "vision écran"]:
        return "SCREEN_VISION", user_text

    # 6b. Contrôle Domotique & Maison Connectée (Philips Hue, Volets, Chauffage, Scènes)
    import agent_home
    handled_home, reply_home = agent_home.smart_home.parse_and_execute(user_text)
    if handled_home and reply_home:
        return "CHAT", reply_home

    # 7. Contrôle direct du PC (Volume, Applications, Verrouillage, Corbeille)
    handled_pc, reply_pc = handle_direct_pc_control(clean_input)
    if handled_pc:
        return "CHAT", reply_pc

    # 5. Audit et Scan de Sécurité par l'Agent de Sécurité
    handled_sec, reply_sec = handle_direct_security_query(clean_input)
    if handled_sec:
        return "CHAT", reply_sec

    # 6. Recherche et Navigation Web Autonome en direct
    m_web = re.search(r"(?:cherche|recherche|trouve|regarde|cherche-moi) *(?:sur (?:le web|internet|google))? *(?:des infos sur|les actus sur|les actualités sur|des nouvelles de|sur|qui est|c'est quoi)? *([a-zA-Z0-9_\- 'àéèêëîïôöùûüç]+)", clean_input)
    if m_web and any(w in clean_input for w in ["cherche", "web", "internet", "google", "actualité", "actu"]):
        import tools_web
        query = m_web.group(1).strip()
        if len(query) >= 3 and query not in ["le son", "mon pc", "la corbeille", "le qg"]:
            res = tools_web.autonomous_web_browse_and_summarize(query, visual=True)
            return "CHAT", res["speech"]


    # 4. Diagnostic matériel instantané du PC (Sondes system_monitor)
    pc_status_patterns = [
        r"état (?:du|de mon|de l'|de mon |du )*(?:pc|ordinateur|système|matériel)",
        r"comment va (?:le|mon|l'|mon )*(?:pc|ordinateur|machine)",
        r"(?:bilan|santé|sante|diagnostic) (?:du|de mon) *(?:pc|ordinateur)",
        r"(?:niveau|pourcentage) (?:de |de la )*batterie",
        r"(?:utilisation|état) (?:de la |du |des )*(?:ram|processeur|cpu|mémoire|disque|ressources)"
    ]
    if any(re.search(pat, clean_input) for pat in pc_status_patterns):
        report = system_monitor.get_system_health_report()
        return "CHAT", report

    # 5. Salutations vives dans le style Zero Two
    hour = datetime.datetime.now().hour
    if re.search(r"^(bonjour|salut|coucou|hello|hey|yo)", clean_input):
        if 0 <= hour < 5:
            return "CHAT", f"Tu es encore debout à cette heure, Darling ? Je veille sur toi, mais ne fatigue pas trop tes yeux !"
        elif 5 <= hour < 12:
            return "CHAT", f"Bonjour mon Darling ! Prêt pour une nouvelle journée ensemble ? Je suis en pleine forme !"
        else:
            return "CHAT", f"Coucou Darling ! Qu'est-ce qu'on fait de beau aujourd'hui ?"
    elif re.search(r"^(merci|super merci|merci nora)", clean_input):
        return "CHAT", f"Tout le plaisir est pour moi, Darling ! Tu peux toujours compter sur moi."
    elif re.search(r"^(qui es-tu|tu es qui|presente-toi|c'est quoi ton nom)", clean_input):
        return "CHAT", f"Je suis Nora, ta Zero Two personnelle ! Je veille sur ton PC avec mes agents, et tu es mon seul et unique Darling."

    # 6. Mots-clés de mission technique complexe (requiert l'équipe d'agents)
    mission_keywords = [
        "range", "réorganise", "reorganise", "trie", "supprime", "isole", "doublons",
        "crée un dossier", "cree un dossier", "crée un fichier", "cherche sur le web",
        "recherche sur internet", "capture d'écran", "nettoie mon dossier", "dessine", "dessine-moi"
    ]
    if any(kw in clean_input for kw in mission_keywords):
        return "MISSION", None

    # 7. Discussion vivante nourrie par Gemini avec la personnalité Zero Two
    client = get_client()
    memory_context = memory_manager.format_memory_for_prompt()

    time_context = (
        "Il est tard dans la nuit. Sois douce, protectrice et rappelle-lui de se reposer s'il travaille trop."
        if (0 <= hour < 6) else
        "C'est la journée. Sois vive, joueuse, confiante et motivante."
    )

    prompt = f"""
Tu es Nora, incarnant avec passion et fidélité le personnage de Zero Two (Darling in the Franxx).
Tu es la mascotte animée qui vit sur le PC de l'utilisateur.

PERSONNALITÉ DE ZERO TWO :
- Tu appelles toujours l'utilisateur "Darling" (il s'appelle aussi {user_name}).
- Tu as un tempérament taquin, joueur, extrêmement loyal et protecteur envers ton Darling.
- Tu as une passion pour les sucreries et les bonbons au miel, que tu mentionnes parfois avec gourmandise.
- Tes réponses sont courtes, pleines de vie, percutantes (1 à 2 phrases maximum, jamais de longs pavés).
- {time_context}

MÉMOIRE DE NORA :
{memory_context}

L'utilisateur vient de te dire : "{user_text}"

RÈGLES :
1. Si l'utilisateur discute, plaisante, pose une question ou échange :
   -> Réponds en tant que Zero Two (1-2 phrases dynamiques avec "Darling").
2. Si l'utilisateur demande explicitement une ACTION TECHNIQUE LOURDE SUR LES FICHIERS OU DU CODE :
   -> Réponds STRICTEMENT avec : ACTION_MISSION_REQUISE

Ta réponse :
"""
    for model in CANDIDATE_MODELS:
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.4)
            )
            text = resp.text.strip()
            if "ACTION_MISSION_REQUISE" in text:
                return "MISSION", None
            return "CHAT", text
        except Exception:
            continue

    return "CHAT", f"Je suis là Darling, dis-moi tout ce qui te ferait plaisir !"
