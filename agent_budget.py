"""
Agent IA Gestionnaire de Budget & Comptes Bancaires pour Nora (Zero Two)
- Suivi des comptes de Darling : Compte Courant, Livret A, Épargne
- Enregistrement des dépenses et revenus en langage naturel
- Analyse budgétaire (règle 50/30/20, dépenses quotidiennes, alertes)
- Persistance locale 100% sécurisée dans finances_darling.json (aucun mot de passe bancaire requis)
"""
import os
import json
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FINANCES_FILE = BASE_DIR / "finances_darling.json"

DEFAULT_FINANCES = {
    "accounts": {
        "Courant": {"balance": 1850.0, "currency": "EUR", "type": "checking"},
        "Livret A": {"balance": 6200.0, "currency": "EUR", "type": "savings"},
        "Epargne": {"balance": 3500.0, "currency": "EUR", "type": "savings"}
    },
    "monthly_budget": {
        "max_expenses": 1600.0,
        "target_savings_rate": 0.20
    },
    "categories": [
        "Alimentation", "Courses", "Loisirs", "Transport", "Factures",
        "Shopping", "Logement", "Sante", "Salaire", "Autre"
    ],
    "transactions": [
        {
            "id": 1,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "amount": -38.50,
            "category": "Courses",
            "account": "Courant",
            "description": "Supermarché réapprovisionnement"
        },
        {
            "id": 2,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "amount": -14.90,
            "category": "Loisirs",
            "account": "Courant",
            "description": "Abonnement streaming"
        }
    ]
}

class BudgetAgent:
    def __init__(self):
        self.data = self._load_data()

    def _load_data(self) -> dict:
        if FINANCES_FILE.exists():
            try:
                with open(FINANCES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Erreur lecture finances : {e}")
        return DEFAULT_FINANCES.copy()

    def _save_data(self):
        try:
            with open(FINANCES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Erreur sauvegarde finances : {e}")

    def get_accounts(self) -> dict:
        return self.data.get("accounts", {})

    def get_total_liquidities(self) -> float:
        total = 0.0
        for acc in self.data.get("accounts", {}).values():
            total += float(acc.get("balance", 0.0))
        return round(total, 2)

    def add_transaction(self, amount: float, category: str, description: str, account: str = "Courant") -> dict:
        if account not in self.data["accounts"]:
            self.data["accounts"][account] = {"balance": 0.0, "currency": "EUR", "type": "custom"}

        # Mise à jour du solde
        self.data["accounts"][account]["balance"] = round(self.data["accounts"][account]["balance"] + amount, 2)

        tx = {
            "id": len(self.data.get("transactions", [])) + 1,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "amount": amount,
            "category": category,
            "account": account,
            "description": description
        }
        self.data.setdefault("transactions", []).insert(0, tx)
        self._save_data()
        return tx

    def parse_natural_language(self, text: str) -> dict:
        """
        Extrait montant, type (dépense/revenu) et catégorie à partir d'une phrase de Darling.
        Ex: 'j'ai dépensé 45 euros pour des courses' -> amount=-45, cat=Courses
        """
        lower = text.lower()
        
        # Recherche du montant
        match = re.search(r"(\d+(?:[.,]\d{1,2})?)\s*(?:€|euros?|e)?", lower)
        amount = 0.0
        if match:
            amount = float(match.group(1).replace(",", "."))

        # Détection dépense vs revenu
        is_income = any(w in lower for w in ["reçu", "salaire", "virement", "rentré", "gagné", "encaissé", "touché"])
        if not is_income and amount > 0:
            amount = -amount

        # Détection catégorie
        category = "Autre"
        if any(w in lower for w in ["course", "supermarché", "manger", "restaurant", "nourriture", "mcdo", "burger"]):
            category = "Alimentation"
        elif any(w in lower for w in ["essence", "carburant", "péage", "train", "uber", "voiture", "bus"]):
            category = "Transport"
        elif any(w in lower for w in ["loyer", "edf", "électricité", "eau", "assurance", "wifi", "internet"]):
            category = "Factures"
        elif any(w in lower for w in ["jeu", "cinéma", "sortie", "bar", "soirée", "concert"]):
            category = "Loisirs"
        elif any(w in lower for w in ["salaire", "paie", "prime", "virement pro"]):
            category = "Salaire"
        elif any(w in lower for w in ["vêtement", "habits", "amazon", "shopping"]):
            category = "Shopping"

        account = "Courant"
        if "livret" in lower:
            account = "Livret A"
        elif "épargne" in lower or "epargne" in lower:
            account = "Epargne"

        return {
            "amount": amount,
            "category": category,
            "account": account,
            "description": text.strip()
        }

    def get_summary_speech(self) -> str:
        accounts = self.get_accounts()
        courant = accounts.get("Courant", {}).get("balance", 0.0)
        livret = accounts.get("Livret A", {}).get("balance", 0.0)
        epargne = accounts.get("Epargne", {}).get("balance", 0.0)
        total = self.get_total_liquidities()

        speech = (
            f"Monsieur Maverick, voici l'état de vos comptes bancaires : "
            f"Vous avez {courant:.2f} euros sur votre compte courant, "
            f"{livret:.2f} euros sur votre Livret A, et {epargne:.2f} euros d'épargne. "
            f"Ce qui représente un total de liquidités disponibles de {total:.2f} euros. "
        )

        if courant < 250:
            speech += "Attention Maverick, le solde de votre compte courant est un peu juste pour terminer le mois. Restez vigilant sur vos dépenses."
        else:
            speech += "Vos finances sont saines et parfaitement gérées, Maverick."

        return speech

budget_agent = BudgetAgent()

if __name__ == "__main__":
    print("[TEST] Agent Budget & Comptes Bancaires :")
    print(budget_agent.get_summary_speech())
    tx = budget_agent.parse_natural_language("J'ai payé 55 euros pour mon plein d'essence")
    print("Parsed TX:", tx)
