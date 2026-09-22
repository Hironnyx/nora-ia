"""
Agent IA Gestionnaire de Courriels (Mails) pour Nora
- Consultation sécurisée via IMAP (Gmail, Outlook, Yahoo, serveurs privés)
- Envoi sécurisé via SMTP avec chiffrement SSL/TLS
- Synthèse vocale intelligente des emails importants pour Maverick avec vouvoiement
- Rédaction de brouillons et réponses soignées prêtes à l'envoi
- Configuration locale sécurisée dans config_mail.json
"""
import os
import sys
import json
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent
MAIL_CONFIG_FILE = BASE_DIR / "config_mail.json"

DEFAULT_MAIL_CONFIG = {
    "enabled": False,
    "email_address": "",
    "app_password": "",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_ssl": True
}

DEMO_EMAILS = [
    {
        "id": "demo-1",
        "sender": "Banque Populaire <alerte@banquepopulaire.fr>",
        "subject": "Relevé mensuel et synthèse de vos comptes",
        "date": "Aujourd'hui à 08:30",
        "unread": True,
        "priority": "important",
        "snippet": "Monsieur Maverick, votre relevé de compte pour la période passée est disponible sur votre espace sécurisé."
    },
    {
        "id": "demo-2",
        "sender": "Service Livraison <suivi@transporteur.fr>",
        "subject": "Votre commande sera livrée aujourd'hui",
        "date": "Aujourd'hui à 09:15",
        "unread": True,
        "priority": "normal",
        "snippet": "Votre colis n°FR-89423 est pris en charge par notre livreur. Créneau estimé : entre 14h00 et 16h30."
    },
    {
        "id": "demo-3",
        "sender": "Cabinet Juridique & Conseil <contact@cabinet-conseil.fr>",
        "subject": "Validation des documents et calendrier",
        "date": "Hier à 17:45",
        "unread": False,
        "priority": "normal",
        "snippet": "Bonjour Monsieur Maverick, nous vous confirmons la bonne réception des pièces justificatives. Nous attendons votre retour pour valider la date de signature."
    }
]

def _decode_mime_words(s: str) -> str:
    """Décode les en-têtes MIME encodés en utf-8 ou base64."""
    if not s:
        return ""
    try:
        decoded_fragments = decode_header(s)
        parts = []
        for text, encoding in decoded_fragments:
            if isinstance(text, bytes):
                parts.append(text.decode(encoding or "utf-8", errors="replace"))
            else:
                parts.append(str(text))
        return "".join(parts)
    except Exception:
        return s

class MailAgent:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if MAIL_CONFIG_FILE.exists():
            try:
                with open(MAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[MailAgent] Erreur lecture config : {e}")
        return DEFAULT_MAIL_CONFIG.copy()

    def save_config(self, new_config: dict):
        self.config.update(new_config)
        try:
            with open(MAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MailAgent] Erreur sauvegarde config : {e}")

    def is_configured(self) -> bool:
        return bool(
            self.config.get("enabled")
            and self.config.get("email_address")
            and self.config.get("app_password")
        )

    def fetch_recent_emails(self, unread_only: bool = True, limit: int = 5) -> List[Dict[str, Any]]:
        """Récupère les courriels récents via IMAP avec fallback démo si non configuré."""
        if not self.is_configured():
            return DEMO_EMAILS[:limit]

        results = []
        try:
            mail = imaplib.IMAP4_SSL(self.config["imap_server"], self.config.get("imap_port", 993))
            mail.login(self.config["email_address"], self.config["app_password"])
            mail.select("inbox")

            criterion = "UNSEEN" if unread_only else "ALL"
            status, data = mail.search(None, criterion)
            if status != "OK" or not data[0]:
                mail.logout()
                return []

            mail_ids = data[0].split()
            # Prendre les plus récents (derniers identifiants)
            recent_ids = mail_ids[-limit:]
            recent_ids.reverse()

            for mid in recent_ids:
                status, msg_data = mail.fetch(mid, "(RFC822)")
                if status != "OK":
                    continue
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = _decode_mime_words(msg.get("Subject", "(Sans objet)"))
                sender = _decode_mime_words(msg.get("From", "Inconnu"))
                date_str = msg.get("Date", "")

                snippet = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disp = str(part.get("Content-Disposition"))
                        if content_type == "text/plain" and "attachment" not in content_disp:
                            payload = part.get_payload(decode=True)
                            if payload:
                                snippet = payload.decode(errors="replace")[:300].strip()
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        snippet = payload.decode(errors="replace")[:300].strip()

                results.append({
                    "id": mid.decode("utf-8", errors="ignore"),
                    "sender": sender,
                    "subject": subject,
                    "date": date_str,
                    "unread": True,
                    "snippet": snippet
                })

            mail.logout()
            return results

        except Exception as e:
            print(f"[MailAgent] Erreur relève IMAP : {e}")
            return DEMO_EMAILS[:limit]

    def get_summary_speech(self) -> str:
        """Génère la synthèse vocale pour Maverick avec vouvoiement systématique."""
        emails = self.fetch_recent_emails(unread_only=True, limit=3)
        if not emails:
            return "Monsieur Maverick, vous n'avez aucun nouveau courriel non lu dans votre boîte de réception. Tout est à jour."

        nb = len(emails)
        if nb == 1:
            speech = f"Monsieur Maverick, vous avez un nouveau courriel non lu de {emails[0]['sender'].split('<')[0].strip()} concernant '{emails[0]['subject']}'."
        else:
            speech = f"Monsieur Maverick, vous avez {nb} nouveaux courriels non lus. Notamment un message de {emails[0]['sender'].split('<')[0].strip()} ayant pour objet '{emails[0]['subject']}', et un autre de {emails[1]['sender'].split('<')[0].strip()}."

        if not self.is_configured():
            speech += " (Ces messages sont des exemples d'illustration, vous pouvez associer votre compte dans config_mail.json)."
        return speech

    def draft_reply(self, recipient: str, original_subject: str, instructions: str) -> str:
        """Rédige une réponse d'email professionnelle et soignée au nom de Maverick."""
        try:
            import nora_brain
            client = nora_brain.get_client()
            prompt = f"""
Rédige un courriel de réponse professionnel, poli et clair au nom de Maverick.
Destinataire : {recipient}
Objet d'origine : {original_subject}
Consignes et points à aborder donnés par Maverick : "{instructions}"

Règles de rédaction :
- Ton : Professionnel, courtois, respectueux et élégant.
- Signature : "Cordialement, Maverick"
- Rédige uniquement le corps de l'email, prêt à être envoyé.
"""
            for model in nora_brain.CANDIDATE_MODELS:
                try:
                    resp = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    return resp.text.strip()
                except Exception:
                    continue
        except Exception as e:
            print(f"[MailAgent] Erreur rédaction IA : {e}")

        return f"Bonjour,\n\nJe fais suite à votre message concernant '{original_subject}'. {instructions}.\n\nRestant à votre disposition,\nCordialement,\nMaverick"

    def send_email(self, to_address: str, subject: str, body: str) -> tuple[bool, str]:
        """Envoie un email via SMTP."""
        if not self.is_configured():
            return False, "Votre compte de messagerie n'est pas encore configuré dans config_mail.json, Monsieur Maverick."

        try:
            msg = MIMEMultipart()
            msg["From"] = self.config["email_address"]
            msg["To"] = to_address
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            server = smtplib.SMTP(self.config["smtp_server"], self.config.get("smtp_port", 587))
            server.starttls()
            server.login(self.config["email_address"], self.config["app_password"])
            server.send_message(msg)
            server.quit()

            return True, f"Courriel envoyé avec succès à {to_address}, Monsieur Maverick."
        except Exception as e:
            return False, f"Impossible d'expédier le courriel : {str(e)}"

mail_agent = MailAgent()
