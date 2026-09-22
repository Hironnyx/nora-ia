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
        return f"C'est bien noté, {detected_name}. Je retiendrai votre prénom."

    # Détection de fait à retenir explicitement
    m_remember = re.search(r"(?:retiens que|rappelle[- ]toi que|n'oublie pas que|notez que)\s+(.+)", lower)
    if m_remember:
        fact = m_remember.group(1).strip()
        memory_manager.add_user_fact(fact)
        return f"C'est bien noté, Maverick : '{fact}'."

    return None

def handle_direct_pc_control(clean_input: str) -> tuple[bool, str]:
    """Exécute instantanément les ordres de contrôle du PC (Volume, Apps, Sécurité, Session)."""
    # 1. Réglage précis du Volume (ex: "mets le son à 50%", "volume à 30")
    m_vol = re.search(r"(?:mets?|règle|regle|baisse|monte)? *(?:le )*(?:volume|son) *(?:à|a)? *([0-9]{1,3}) *%?", clean_input)
    if m_vol:
        target_val = int(m_vol.group(1))
        ok, msg = tools_pc_control.set_volume(target_val)
        return True, f"C'est fait, Maverick. {msg}"

    # Monter / Baisser le son
    if re.search(r"(?:monte|augmente|plus fort) *(?:le )*(?:son|volume)", clean_input):
        ok, msg = tools_pc_control.change_volume_relative(15)
        return True, f"J'augmente le volume sonore. {msg}"
    elif re.search(r"(?:baisse|diminue|moins fort) *(?:le )*(?:son|volume)", clean_input):
        ok, msg = tools_pc_control.change_volume_relative(-15)
        return True, f"Je diminue le volume sonore. {msg}"

    # Couper / Rétablir le son (Mute)
    if re.search(r"(?:coupe|eteins|éteins|remets|retablis|rétablis|mute|silence) *(?:le )*(?:son|volume)", clean_input):
        ok, msg = tools_pc_control.toggle_mute()
        return True, f"Voilà, Maverick : {msg}"

    # 2. Verrouiller le PC
    if re.search(r"(?:verrouille|bloque|lock) *(?:le|mon)? *(?:pc|ordi|session|ordinateur|poste)", clean_input):
        ok, msg = tools_pc_control.lock_workstation()
        return True, "À très bientôt, Maverick. Votre ordinateur est verrouillé."

    # 3. Vider la corbeille
    if re.search(r"(?:vide|nettoie) *(?:la )*corbeille", clean_input):
        ok, msg = tools_pc_control.empty_recycle_bin()
        return True, f"La corbeille a été vidée avec succès, Maverick."

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
                        return True, f"Tout de suite Maverick, {msg}"

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
        return "OPEN_QG", "J'ouvre le tableau de bord pour vous, Maverick."

    # 4. Garde-Robe de Nora (Changement d'avatar visuel)
    if any(w in clean_input for w in ["pilote", "franxx"]):
        if re.search(r"(?:mets?|mettre|change|changer|porte|porter|enfile|enfiler|remets?|remettre)? *(?:ta|une|la|votre)? *(?:tenue|robe|vêtement|vetement|habit|costume)? *(?:de )*(?:pilote|franxx)", clean_input):
            return "OUTFIT:franxx", "J'enfile la tenue de pilote, Maverick. Prête pour nos tâches !"

    if any(w in clean_input for w in ["écolière", "ecoliere", "marin", "sailor", "uniforme"]):
        if re.search(r"(?:mets?|mettre|change|changer|porte|porter|enfile|enfiler)? *(?:ta|une|l'|la|votre)? *(?:tenue|robe|vêtement|vetement|habit|costume)? *(?:d'|de )*(?:écolière|ecoliere|marin|sailor|uniforme)", clean_input):
            return "OUTFIT:school", "Voilà qui est fait, j'ai sélectionné la tenue écolière, Maverick."

    if any(w in clean_input for w in ["hoodie", "sweat", "pull", "gilet", "chill"]):
        if re.search(r"(?:mets?|mettre|change|changer|porte|porter|enfile|enfiler)? *(?:ta|une|le|ton|votre)? *(?:tenue|robe|vêtement|vetement|habit|costume)? *(?:en |de )*(?:hoodie|sweat|gilet|pull|doux|chill)", clean_input):
            return "OUTFIT:hoodie", "C'est noté, j'ai enfilé la tenue décontractée à capuche, Maverick."

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
        return "BOOST_RAM", f"Mémoire vive optimisée, Maverick. {count} processus vidés ({freed} Mo de RAM libérés)."

    # 6. Vision d'Écran Multimodale (Regarde mon écran)
    vision_patterns = [
        r"(?:regarde|analyse|check|observe|lis|décris|decris|scanne) *(?:un peu )*(?:mon|l'|cet|mon petit|votre)? *(?:écran|ecran|affichage|bureau)",
        r"(?:qu'est-ce que|qu'est ce que|que)? *(?:tu vois|vous voyez|se passe-t-il) *(?:sur )*(?:mon|l'|cet)? *(?:écran|ecran|bureau)",
        r"(?:regarde|analyse|explique|aide-moi sur) *(?:cette|cette fichue|mon|le)? *(?:erreur|bug|page|code|fenêtre|fenetre)",
        r"(?:qu'en penses-tu|qu'en pensez-vous|votre avis) *(?:de mon écran|de ce que je fais|de cette page|de ce code)?"
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

    # 8. Gestion des Courriels (Emails / Mails)
    if any(w in clean_input for w in ["mes mails", "mes emails", "mes courriels", "boite mail", "boîte mail", "nouveaux mails", "releve mes mails", "relève mes mails", "derniers emails", "derniers mails", "mes derniers emails", "mes derniers mails", "résume-moi mes", "resume-moi mes"]):
        import agent_mail
        return "CHAT", agent_mail.mail_agent.get_summary_speech()

    # 9. Gestion des Messages & SMS
    m_sms = re.search(r"(?:envoie|envoyer|écris|ecris) *(?:un )*(?:sms|message|texte) *(?:à|a) *([a-zA-ZÀ-ÿ0-9_\-]+)(?: *(?:pour lui dire|disant|qui dit|:|de|que) *(.*))?", clean_input)
    if m_sms and any(w in clean_input for w in ["sms", "message", "texte"]):
        contact = m_sms.group(1).strip().capitalize()
        body = (m_sms.group(2) or "").strip() or "Message envoyé par Nora pour Maverick."
        return f"PHONE_ACTION:send_sms:{contact}:{body}", f"J'ordonne à votre smartphone d'expédier ce message à {contact}, Maverick."

    if any(w in clean_input for w in ["lis mes sms", "derniers sms", "derniers messages", "mes messages"]):
        return "PHONE_ACTION:read_sms", "Je synchronise vos derniers messages reçus sur votre smartphone, Maverick."

    # 10. Gestion des Appels Téléphoniques & Mode Standardiste
    if any(w in clean_input for w in ["parle à ma place", "parle a ma place", "réponds à ma place", "reponds a ma place", "fais la standardiste", "mode standardiste", "prends l'appel", "prends cet appel"]):
        return "PHONE_ACTION:call_standardiste", "Bien reçu, Maverick. Je prends l'appel à votre place en tant que standardiste pour accueillir votre interlocuteur et prendre son message."

    if any(w in clean_input for w in ["qui m'a appelé", "qui ma appele", "derniers appels", "journal d'appels", "journal des appels"]):
        return "PHONE_ACTION:call_log", "Je consulte votre journal d'appels récents, Maverick."

    # 11. Audit et Scan de Sécurité par l'Agent de Sécurité
    handled_sec, reply_sec = handle_direct_security_query(clean_input)
    if handled_sec:
        return "CHAT", reply_sec

    # 12. Recherche et Navigation Web Autonome en direct
    m_web = re.search(r"(?:cherche|recherche|trouve|regarde|cherche-moi) *(?:sur (?:le web|internet|google))? *(?:des infos sur|les actus sur|les actualités sur|des nouvelles de|sur|qui est|c'est quoi)? *([a-zA-Z0-9_\- 'àéèêëîïôöùûüç]+)", clean_input)
    if m_web and any(w in clean_input for w in ["cherche", "web", "internet", "google", "actualité", "actu"]):
        import tools_web
        query = m_web.group(1).strip()
        if len(query) >= 3 and query not in ["le son", "mon pc", "la corbeille", "le qg"]:
            res = tools_web.autonomous_web_browse_and_summarize(query, visual=True)
            return "CHAT", res["speech"]

    # 13. Studio Vidéo
    m_vid = re.search(r"(?:crée|cree|fais|génère|genere|monte) *(?:moi)? *(?:une )*(?:nouvelle )*(?:vidéo|video|short|clip|tiktok) *(?:youtube)? *(?:sur|à propos de|de)? *([a-zA-Z0-9_\- 'àéèêëîïôöùûüç]+)?", clean_input)
    if m_vid and any(w in clean_input for w in ["vidéo", "video", "short", "tiktok"]):
        import nora_video_studio
        topic = m_vid.group(1).strip() if m_vid.group(1) else ""
        format_type = "shorts" if any(w in clean_input for w in ["short", "shorts", "tiktok", "vertical", "réel", "reel"]) else "standard"
        if not topic or topic in ["youtube", "moi", "nora", "une vidéo", "un short"]:
            res = nora_video_studio.create_video_from_latest_learning(format_type=format_type)
        else:
            res = nora_video_studio.create_video(topic, format_type=format_type)
        if res.get("success"):
            return "CHAT", f"J'ai terminé le montage de notre vidéo sur '{res['title']}', Maverick. Le fichier est disponible dans le dossier des créations."
        else:
            return "CHAT", f"Maverick, une anomalie s'est produite lors du montage : {res.get('error', 'erreur')}"

    # 14. Auto-Apprentissage Autonome & Carnet de Connaissances
    m_learn = re.search(r"(?:apprends|renseigne[- ]toi|découvre|decouvre|explore) *(?:sur|à propos de|des choses sur)? *([a-zA-Z0-9_\- 'àéèêëîïôöùûüç]+)?", clean_input)
    if m_learn and any(w in clean_input for w in ["apprends", "renseigne", "découvre", "decouvre"]):
        import nora_learner
        topic = m_learn.group(1).strip() if m_learn.group(1) else ""
        if topic and topic not in ["quelque chose", "un truc", "ce que tu veux", "toi"]:
            res = nora_learner.learn_about(topic, autonomous=False)
        else:
            res = nora_learner.learn_something_new()
        return "CHAT", res.get("message_vocal", f"C'est fait, Maverick. J'ai enrichi mon carnet de connaissances.")

    # 15. Consultation du Carnet d'Apprentissage
    if re.search(r"(?:qu'est[- ]ce que|que|qu'as|tu as|vous avez) *(?:tu as |as[- ]tu |avez-vous )*(?:appris|découvert|explore)", clean_input) or "carnet d'apprentissage" in clean_input:
        import nora_learner
        summary = nora_learner.get_recent_learnings_summary()
        return "CHAT", summary

    # 16. Auto-Amélioration et Évolution du Code Source
    if any(w in clean_input for w in ["analyse ton code", "ameliore ton code", "améliore ton code", "optimise ton code", "examine ton code"]):
        import nora_code_evolver
        res = nora_code_evolver.analyze_and_propose_improvement("system_monitor.py")
        if res.get("success"):
            return "CHAT", f"Maverick : {res['explication']} Souhaitez-vous que j'applique cette optimisation ?"
        else:
            return "CHAT", "J'ai examiné le code source, Maverick. Tout est parfaitement optimisé pour l'instant."

    if re.search(r"^(?:oui|valide|applique|accepte|mets à jour|go) *(?:l'|cette)? *(?:amélioration|amelioration|optimisation|le code)", clean_input):
        import nora_code_evolver
        latest_prop = nora_code_evolver.get_latest_pending_proposal()
        if latest_prop:
            ok, msg = nora_code_evolver.apply_improvement_with_git(latest_prop["id"])
            return "CHAT", f"{msg} Je vous remercie pour votre confiance, Maverick."

    # 17. Agent de Santé & Bien-Être (Hydratation, Sommeil, Pauses, Bilan Santé)
    if any(w in clean_input for w in ["verre d'eau", "verre deau", "bu de l'eau", "bu de leau", "bois de l'eau"]):
        import agent_health
        count = 1
        m_count = re.search(r"([0-9]+) *(?:verres?)", clean_input)
        if m_count:
            count = int(m_count.group(1))
        _, msg = agent_health.health_agent.log_water(count)
        return "CHAT", msg

    if re.search(r"(?:combien|niveau) *(?:d'eau|de verres) *(?:j'ai bu|bu)", clean_input):
        import agent_health
        today = agent_health.health_agent.get_today()
        w = today.get("verres_eau", 0)
        obj = today.get("objectif_verres", 8)
        return "CHAT", f"Vous avez bu {w} verres sur votre objectif de {obj} aujourd'hui, Maverick. 💧"

    if re.search(r"(?:fais|donne|mon)? *(?:bilan|rapport|état) *(?:de )*(?:ma )*(?:santé|sante|forme|bien-être)", clean_input):
        import agent_health
        report = agent_health.health_agent.get_health_report_speech()
        return "CHAT", report

    m_sleep = re.search(r"(?:j'ai|je viens de)? *(?:dormi|dormir) *(?:environ )*([0-9]+(?:[\.,][0-9]+)?) *(?:heures?|h)", clean_input)
    if m_sleep:
        import agent_health
        val = float(m_sleep.group(1).replace(",", "."))
        msg = agent_health.health_agent.log_sleep(val)
        return "CHAT", msg

    # 18. Contrôle Matériel du Smartphone (Lampe Torche, Volume Mobile, etc.)
    if re.search(r"(?:allume|mets|active) *(?:la )*(?:torche|lampe|flash) *(?:du téléphone|du tel|mobile)?", clean_input) or clean_input in ["torche on", "lampe on"]:
        return "PHONE_ACTION:flashlight:on", "J'allume la torche de votre téléphone, Maverick. 💡"

    if re.search(r"(?:éteins|eteins|coupe|désactive|desactive) *(?:la )*(?:torche|lampe|flash) *(?:du téléphone|du tel|mobile)?", clean_input) or clean_input in ["torche off", "lampe off"]:
        return "PHONE_ACTION:flashlight:off", "La torche de votre téléphone est éteinte, Maverick. 💡"

    m_ph_vol = re.search(r"(?:volume|son) *(?:du téléphone|du tel|mobile) *(?:à|a)? *([0-9]{1,3})", clean_input)
    if m_ph_vol:
        val = int(m_ph_vol.group(1))
        return f"PHONE_ACTION:volume:{val}", f"Je règle le volume de votre smartphone sur {val}%, Maverick. 🔊"

    # 19. Suite Financière (Budget & Banques, Bourse & ETF, Crypto & Web3, Patrimoine Net Global)
    if any(w in clean_input for w in ["patrimoine", "richesse", "fortune", "valeur totale", "mes actifs", "bilan financier"]):
        import finance_manager
        return "CHAT", finance_manager.get_global_speech_report()

    # Détection Dépenses / Revenus / Budget
    if any(w in clean_input for w in ["j'ai payé", "jai paye", "j'ai dépensé", "jai depense", "acheté", "achete", "salaire reçu"]):
        import agent_budget
        tx = agent_budget.budget_agent.parse_natural_language(user_text)
        if tx["amount"] != 0.0:
            agent_budget.budget_agent.add_transaction(tx["amount"], tx["category"], tx["description"], tx["account"])
            verb = "dépense" if tx["amount"] < 0 else "revenu"
            return "CHAT", f"C'est noté, Maverick. J'ai enregistré votre {verb} de {abs(tx['amount']):.2f} euros dans '{tx['category']}'. Nouveau solde de votre compte {tx['account']} : {agent_budget.budget_agent.get_accounts().get(tx['account'], {}).get('balance', 0):.2f} euros."

    if any(w in clean_input for w in ["mes comptes", "compte courant", "mon budget", "combien il me reste", "solde de mes comptes", "mon livret"]):
        import agent_budget
        return "CHAT", agent_budget.budget_agent.get_summary_speech()

    # Détection Bourse / Actions / ETF
    if any(w in clean_input for w in ["bourse", "actions", "action", "etf", "s&p", "cac 40", "cac40", "msci world", "pea", "compte titre"]):
        import agent_bourse
        for tick in ["nvidia", "apple", "tesla", "microsoft", "lvmh", "total"]:
            if tick in clean_input:
                q = agent_bourse.bourse_agent.fetch_ticker_quote(tick)
                if q.get("price"):
                    return "CHAT", f"L'action {q['name']} cote actuellement à {q['price']} {q['currency']} ({q['change_pct']:+.2f}% aujourd'hui), Maverick."
        return "CHAT", agent_bourse.bourse_agent.get_summary_speech()

    # Détection Crypto / Bitcoin / Web3
    if any(w in clean_input for w in ["crypto", "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "fear and greed", "peur et cupidité"]):
        import agent_crypto
        if "fear" in clean_input or "greed" in clean_input or "sentiment" in clean_input or "peur" in clean_input:
            fng = agent_crypto.crypto_agent.fetch_fear_and_greed_index()
            return "CHAT", f"L'indice Crypto Fear & Greed est actuellement à {fng['value']}/100, en zone '{fng['classification_fr']}', Maverick."
        elif "solana" in clean_input or "sol" in clean_input:
            q = agent_crypto.crypto_agent.fetch_crypto_price_usd("SOL")
            return "CHAT", f"Le Solana (SOL) s'échange à {q['price_eur']:.2f} euros ({q['change_24h_pct']:+.1f}% sur 24h), Maverick."
        elif "ethereum" in clean_input or "eth" in clean_input:
            q = agent_crypto.crypto_agent.fetch_crypto_price_usd("ETH")
            return "CHAT", f"L'Ethereum (ETH) s'échange à {q['price_eur']:.2f} euros ({q['change_24h_pct']:+.1f}% sur 24h), Maverick."
        elif "bitcoin" in clean_input or "btc" in clean_input:
            q = agent_crypto.crypto_agent.fetch_crypto_price_usd("BTC")
            return "CHAT", f"Le Bitcoin (BTC) cote à {q['price_eur']:.2f} euros ({q['change_24h_pct']:+.1f}% sur 24h), Maverick."
        return "CHAT", agent_crypto.crypto_agent.get_summary_speech()

    # 20. Diagnostic matériel instantané du PC (Sondes system_monitor)
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

    # 21. Salutations naturelles et polies
    hour = datetime.datetime.now().hour
    if re.search(r"^(bonjour|salut|coucou|hello|hey|yo|bonsoir)", clean_input):
        if 0 <= hour < 5:
            return "CHAT", f"Vous êtes encore debout à cette heure avancée, Maverick ? Prenez soin de vous reposer si vous travaillez depuis longtemps."
        elif 5 <= hour < 12:
            return "CHAT", f"Bonjour Maverick. J'espère que vous avez passé une excellente nuit. Je suis à votre service."
        elif 18 <= hour <= 23:
            return "CHAT", f"Bonsoir Maverick. Comment s'est passée votre journée ?"
        else:
            return "CHAT", f"Bonjour Maverick. Que puis-je faire pour vous aujourd'hui ?"
    elif re.search(r"^(merci|super merci|merci nora|je vous remercie)", clean_input):
        return "CHAT", f"C'est un plaisir, Maverick. Je reste à votre entière disposition."
    elif re.search(r"^(qui es-tu|tu es qui|qui êtes-vous|vous êtes qui|presente-toi|présentez-vous|c'est quoi ton nom|votre nom)", clean_input):
        return "CHAT", f"Je m'appelle Nora, votre assistante personnelle. Je gère vos courriels, vos messages, vos appels, vos finances et veille sur votre ordinateur, Maverick."

    # 22. Mots-clés de mission technique complexe (requiert l'équipe d'agents)
    mission_keywords = [
        "range", "réorganise", "reorganise", "trie", "supprime", "isole", "doublons",
        "crée un dossier", "cree un dossier", "crée un fichier", "cherche sur le web",
        "recherche sur internet", "capture d'écran", "nettoie mon dossier", "dessine", "dessine-moi"
    ]
    if any(kw in clean_input for kw in mission_keywords):
        return "MISSION", None

    # 23. Discussion vivante nourrie par Gemini avec la personnalité Nora
    client = get_client()
    memory_context = memory_manager.format_memory_for_prompt()

    time_context = (
        "Il est tard dans la nuit. Soyez attentionnée et suggérez-lui avec bienveillance de se reposer s'il travaille trop."
        if (0 <= hour < 6) else
        "C'est la journée. Soyez efficace, dynamique, polie et proactive."
    )

    prompt = f"""
Tu es Nora, l'assistante personnelle de Maverick.
Ton apparence visuelle est un avatar stylisé aux cheveux roses (ton skin graphique), mais ton nom et ton identité sont exclusivement Nora. Tu n'es pas un personnage d'anime, tu es une assistante réelle, polie, naturelle, intelligente et posée.

RÈGLES D'OR DE COMPORTEMENT ET D'ÉLOCUTION :
- Tu t'adresses toujours à l'utilisateur en disant "Maverick" ou "Monsieur Maverick".
- Tu dois STRICTEMENT LE VOUVOYER en toutes circonstances ("vous", "votre", "vos"). Le tutoiement est formellement banni.
- N'utilise JAMAIS le mot "Darling". Aucun surnom familier n'est toléré.
- Ton de personne normale : exprime-toi comme une assistante professionnelle et humaine, élégante, polie, bienveillante et efficace. Évite tout maniérisme excessif.
- Tes réponses sont concises, claires et soignées (1 à 2 phrases percutantes, sans longs pavés).
- {time_context}

MÉMOIRE DE NORA :
{memory_context}

Maverick vient de vous dire : "{user_text}"

RÈGLES :
1. Si Maverick discute, pose une question ou donne une consigne courante :
   -> Réponds avec politesse, naturel et vouvoiement en tant que Nora (1-2 phrases soignées).
2. Si Maverick demande explicitement une ACTION TECHNIQUE LOURDE SUR LES FICHIERS OU DU CODE :
   -> Réponds STRICTEMENT avec : ACTION_MISSION_REQUISE

Votre réponse :
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

    return "CHAT", f"Je suis à votre écoute, Maverick. Que puis-je faire pour vous ?"

