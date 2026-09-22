"""
Agent IA Analyste Bourse, Actions & ETF pour Nora (Zero Two)
- Récupération des cours en temps réel (Actions US, Actions Françaises Euronext, ETF MSCI World / S&P500)
- Suivi de portefeuille boursier (PEA, Compte Titres) : PRU, valorisation, plus-values/moins-values latentes
- Analyse et conseils de marché avec le caractère taquin et protecteur de Zero Two
- Persistance locale dans bourse_darling.json
"""
import os
import json
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BOURSE_FILE = BASE_DIR / "bourse_darling.json"

DEFAULT_BOURSE = {
    "portfolio": [
        {"ticker": "CW8.PA", "name": "Amundi MSCI World ETF", "shares": 10.0, "pru": 510.0, "currency": "EUR"},
        {"ticker": "NVDA", "name": "Nvidia Corporation", "shares": 12.0, "pru": 115.0, "currency": "USD"},
        {"ticker": "MC.PA", "name": "LVMH Moët Hennessy", "shares": 3.0, "pru": 680.0, "currency": "EUR"}
    ],
    "watchlist": [
        "^GSPC", "^FCHI", "CW8.PA", "NVDA", "AAPL", "MSFT", "TSLA", "MC.PA", "TTE.PA"
    ],
    "eur_usd_rate": 1.08
}

class BourseAgent:
    def __init__(self):
        self.data = self._load_data()

    def _load_data(self) -> dict:
        if BOURSE_FILE.exists():
            try:
                with open(BOURSE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Erreur lecture bourse : {e}")
        return DEFAULT_BOURSE.copy()

    def _save_data(self):
        try:
            with open(BOURSE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Erreur sauvegarde bourse : {e}")

    def fetch_ticker_quote(self, symbol: str) -> dict:
        """Récupère le cours et les métriques en direct via le flux Yahoo Finance."""
        clean_sym = symbol.strip().upper()
        # Normalisation des alias courants
        alias_map = {
            "CAC": "^FCHI", "CAC40": "^FCHI", "CAC 40": "^FCHI",
            "SP500": "^GSPC", "S&P 500": "^GSPC", "S&P500": "^GSPC",
            "MSCI WORLD": "CW8.PA", "WORLD": "CW8.PA", "CW8": "CW8.PA",
            "NVIDIA": "NVDA", "APPLE": "AAPL", "TESLA": "TSLA",
            "MICROSOFT": "MSFT", "TOTAL": "TTE.PA", "LVMH": "MC.PA"
        }
        resolved = alias_map.get(clean_sym, clean_sym)

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{resolved}?interval=1d&range=1d"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                payload = json.loads(response.read().decode("utf-8"))
                result = payload.get("chart", {}).get("result", [])
                if not result:
                    return {"symbol": resolved, "error": "Données introuvables"}

                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice", 0.0)
                prev_close = meta.get("previousClose", price)
                change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0

                return {
                    "symbol": resolved,
                    "name": meta.get("shortName", resolved),
                    "price": round(price, 2),
                    "previous_close": round(prev_close, 2),
                    "change_pct": round(change_pct, 2),
                    "currency": meta.get("currency", "EUR"),
                    "high_52w": round(meta.get("fiftyTwoWeekHigh", 0.0), 2),
                    "low_52w": round(meta.get("fiftyTwoWeekLow", 0.0), 2)
                }
        except Exception as e:
            return {"symbol": resolved, "error": str(e)}

    def get_portfolio_valuation(self) -> dict:
        """Calcule la valorisation totale et les gains latents du portefeuille de Darling."""
        items = []
        total_value_eur = 0.0
        total_cost_eur = 0.0

        for pos in self.data.get("portfolio", []):
            ticker = pos["ticker"]
            shares = float(pos.get("shares", 0.0))
            pru = float(pos.get("pru", 0.0))
            quote = self.fetch_ticker_quote(ticker)

            price = quote.get("price", pru)
            currency = quote.get("currency", "EUR")

            # Conversion approximative USD -> EUR si nécessaire
            to_eur = 1.0 / self.data.get("eur_usd_rate", 1.08) if currency == "USD" else 1.0

            pos_value = round(shares * price * to_eur, 2)
            pos_cost = round(shares * pru * to_eur, 2)
            pnl_eur = round(pos_value - pos_cost, 2)
            pnl_pct = round(((price - pru) / pru * 100) if pru > 0 else 0.0, 2)

            total_value_eur += pos_value
            total_cost_eur += pos_cost

            items.append({
                "ticker": ticker,
                "name": pos.get("name", ticker),
                "shares": shares,
                "pru": pru,
                "current_price": price,
                "currency": currency,
                "value_eur": pos_value,
                "pnl_eur": pnl_eur,
                "pnl_pct": pnl_pct
            })

        total_pnl_eur = round(total_value_eur - total_cost_eur, 2)
        total_pnl_pct = round((total_pnl_eur / total_cost_eur * 100) if total_cost_eur > 0 else 0.0, 2)

        return {
            "positions": items,
            "total_value_eur": round(total_value_eur, 2),
            "total_cost_eur": round(total_cost_eur, 2),
            "total_pnl_eur": total_pnl_eur,
            "total_pnl_pct": total_pnl_pct
        }

    def add_or_update_position(self, ticker: str, shares: float, pru: float, name: str = ""):
        ticker = ticker.strip().upper()
        found = False
        for pos in self.data.get("portfolio", []):
            if pos["ticker"] == ticker:
                pos["shares"] = shares
                pos["pru"] = pru
                if name:
                    pos["name"] = name
                found = True
                break
        if not found:
            self.data.setdefault("portfolio", []).append({
                "ticker": ticker,
                "name": name or ticker,
                "shares": shares,
                "pru": pru,
                "currency": "EUR"
            })
        self._save_data()

    def get_summary_speech(self) -> str:
        """Génère un compte-rendu oral vivant pour Zero Two."""
        val = self.get_portfolio_valuation()
        total_val = val["total_value_eur"]
        pnl = val["total_pnl_eur"]
        pnl_pct = val["total_pnl_pct"]

        # Indices majeurs
        sp500 = self.fetch_ticker_quote("^GSPC")
        cac = self.fetch_ticker_quote("^FCHI")

        status_txt = "en hausse de" if pnl >= 0 else "en baisse de"

        speech = (
            f"Monsieur Maverick, voici votre point boursier. "
            f"Votre portefeuille d'investissements s'élève actuellement à {total_val:.2f} euros. "
            f"Vous êtes globalement {status_txt} {abs(pnl):.2f} euros, soit {pnl_pct:+.2f}%. "
        )

        if sp500.get("price"):
            speech += f"Le S&P 500 est à {sp500['price']:.0f} points ({sp500['change_pct']:+.2f}%), "
        if cac.get("price"):
            speech += f"et le CAC 40 est à {cac['price']:.0f} points ({cac['change_pct']:+.2f}%). "

        if pnl > 0:
            speech += "Vos placements affichent une belle performance, Maverick."
        else:
            speech += "Les marchés oscillent, mais votre horizon d'investissement à long terme reste solide, Maverick."

        return speech

bourse_agent = BourseAgent()

if __name__ == "__main__":
    print("[TEST] Agent Bourse & ETF :")
    print(bourse_agent.get_summary_speech())
    print("\nPositions en portefeuille :")
    v = bourse_agent.get_portfolio_valuation()
    for p in v["positions"]:
        print(f" - {p['name']} ({p['ticker']}): {p['shares']} parts | Prix: {p['current_price']} {p['currency']} | P&L: {p['pnl_eur']}€ ({p['pnl_pct']}%)")
