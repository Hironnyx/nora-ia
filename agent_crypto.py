"""
Agent IA Vigie Marché Crypto & Web3 pour Nora (Zero Two)
- Cotations en direct des cryptos majeures (Bitcoin, Ethereum, Solana, BNB, XRP) via flux Binance
- Indice Fear & Greed (Sentiment de Marché en direct) via Alternative.me
- Suivi de portefeuille crypto de Darling (Quantités, PRU en euros, plus-values/moins-values latentes)
- Conseils DCA et alertes de volatilité avec la personnalité de Zero Two
- Persistance locale dans crypto_darling.json
"""
import os
import json
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CRYPTO_FILE = BASE_DIR / "crypto_darling.json"

DEFAULT_CRYPTO = {
    "portfolio": [],
    "watchlist": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"],
    "eur_usd_rate": 1.08
}

class CryptoAgent:
    def __init__(self):
        self.data = self._load_data()

    def _load_data(self) -> dict:
        if CRYPTO_FILE.exists():
            try:
                with open(CRYPTO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Erreur lecture crypto : {e}")
        return DEFAULT_CRYPTO.copy()

    def _save_data(self):
        try:
            with open(CRYPTO_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Erreur sauvegarde crypto : {e}")

    def fetch_crypto_price_usd(self, symbol: str) -> dict:
        """Récupère le prix en direct et la variation 24h via l'API publique Binance."""
        clean = symbol.strip().upper().replace("EUR", "").replace("USDT", "").replace("USD", "")
        pair = f"{clean}USDT"
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                d = json.loads(response.read().decode("utf-8"))
                price_usd = float(d.get("lastPrice", 0.0))
                change_pct = float(d.get("priceChangePercent", 0.0))
                high_24h = float(d.get("highPrice", 0.0))
                low_24h = float(d.get("lowPrice", 0.0))

                to_eur = 1.0 / self.data.get("eur_usd_rate", 1.08)
                price_eur = round(price_usd * to_eur, 2)

                return {
                    "symbol": clean,
                    "price_usd": round(price_usd, 2),
                    "price_eur": price_eur,
                    "change_24h_pct": round(change_pct, 2),
                    "high_24h_usd": round(high_24h, 2),
                    "low_24h_usd": round(low_24h, 2)
                }
        except Exception as e:
            return {"symbol": clean, "error": str(e), "price_eur": 0.0, "change_24h_pct": 0.0}

    def fetch_fear_and_greed_index(self) -> dict:
        """Récupère l'indice Fear & Greed actuel (0 = Peur extrême, 100 = Euphorie/Cupidité extrême)."""
        url = "https://api.alternative.me/fng/"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as response:
                payload = json.loads(response.read().decode("utf-8"))
                item = payload.get("data", [{}])[0]
                value = int(item.get("value", 50))
                classification = item.get("value_classification", "Neutral")
                
                # Traduction en français pour Zero Two
                trad = {
                    "Extreme Fear": "Peur Extreme",
                    "Fear": "Peur",
                    "Neutral": "Neutre",
                    "Greed": "Cupidite",
                    "Extreme Greed": "Cupidite Extreme (Euphorie)"
                }
                fr_class = trad.get(classification, classification)

                return {
                    "value": value,
                    "classification": classification,
                    "classification_fr": fr_class
                }
        except Exception as e:
            return {"value": 50, "classification": "Neutral", "classification_fr": "Neutre", "error": str(e)}

    def get_portfolio_valuation(self) -> dict:
        """Calcule la valeur totale et les plus-values latentes du portefeuille crypto de Darling."""
        items = []
        total_value_eur = 0.0
        total_cost_eur = 0.0

        for pos in self.data.get("portfolio", []):
            sym = pos["symbol"]
            amount = float(pos.get("amount", 0.0))
            pru_eur = float(pos.get("pru_eur", 0.0))

            quote = self.fetch_crypto_price_usd(sym)
            current_eur = quote.get("price_eur", pru_eur)

            pos_val = round(amount * current_eur, 2)
            pos_cost = round(amount * pru_eur, 2)
            pnl_eur = round(pos_val - pos_cost, 2)
            pnl_pct = round(((current_eur - pru_eur) / pru_eur * 100) if pru_eur > 0 else 0.0, 2)

            total_value_eur += pos_val
            total_cost_eur += pos_cost

            items.append({
                "symbol": sym,
                "name": pos.get("name", sym),
                "amount": amount,
                "pru_eur": pru_eur,
                "current_price_eur": current_eur,
                "price_usd": quote.get("price_usd", 0.0),
                "change_24h_pct": quote.get("change_24h_pct", 0.0),
                "value_eur": pos_val,
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

    def add_or_update_position(self, symbol: str, amount: float, pru_eur: float, name: str = ""):
        symbol = symbol.strip().upper()
        found = False
        for pos in self.data.get("portfolio", []):
            if pos["symbol"] == symbol:
                pos["amount"] = amount
                pos["pru_eur"] = pru_eur
                if name:
                    pos["name"] = name
                found = True
                break
        if not found:
            self.data.setdefault("portfolio", []).append({
                "symbol": symbol,
                "name": name or symbol,
                "amount": amount,
                "pru_eur": pru_eur
            })
        self._save_data()

    def get_summary_speech(self) -> str:
        """Génère le bulletin crypto oral de Nora."""
        btc = self.fetch_crypto_price_usd("BTC")
        eth = self.fetch_crypto_price_usd("ETH")
        fng = self.fetch_fear_and_greed_index()
        val = self.get_portfolio_valuation()

        if not val["positions"]:
            speech = (
                f"Monsieur Maverick, voici votre point sur le marché crypto. "
                f"Le Bitcoin cote à {btc['price_eur']:.0f} euros ({btc['change_24h_pct']:+.1f}% sur 24h), "
                f"et l'Ethereum est à {eth['price_eur']:.0f} euros ({eth['change_24h_pct']:+.1f}%). "
                f"L'indice de sentiment Fear & Greed est à {fng['value']}/100, en zone '{fng['classification_fr']}'. "
                f"Vous n'avez pas encore renseigné d'actifs dans votre portefeuille crypto. Vous pouvez m'indiquer vos détentions pour que je les intègre à votre patrimoine."
            )
            return speech

        total_val = val["total_value_eur"]
        pnl = val["total_pnl_eur"]
        pnl_pct = val["total_pnl_pct"]
        status_txt = "en profit de" if pnl >= 0 else "en retrait de"

        speech = (
            f"Monsieur Maverick, voici votre point sur le marché crypto. "
            f"Le Bitcoin cote à {btc['price_eur']:.0f} euros ({btc['change_24h_pct']:+.1f}% sur 24h), "
            f"et l'Ethereum est à {eth['price_eur']:.0f} euros ({eth['change_24h_pct']:+.1f}%). "
            f"L'indice de sentiment de marché Fear & Greed est à {fng['value']}/100, en zone '{fng['classification_fr']}'. "
            f"Votre portefeuille crypto total est valorisé à {total_val:.2f} euros, vous êtes {status_txt} {abs(pnl):.2f} euros ({pnl_pct:+.1f}%). "
        )

        if fng["value"] >= 75:
            speech += "Le marché entre en zone d'euphorie élevée, Maverick. Restez prudent et songez à sécuriser des bénéfices si vous le souhaitez."
        elif fng["value"] <= 25:
            speech += "Le sentiment de marché est très craintif, Maverick. Historiquement, ces creux représentent d'excellents points d'entrée."
        else:
            speech += "Le marché est équilibré, votre stratégie d'investissement reste sereine, Maverick."

        return speech

crypto_agent = CryptoAgent()

if __name__ == "__main__":
    print("[TEST] Agent Crypto & Web3 :")
    print(crypto_agent.get_summary_speech())
    print("\nPositions Crypto :")
    v = crypto_agent.get_portfolio_valuation()
    for p in v["positions"]:
        print(f" - {p['name']} ({p['symbol']}): {p['amount']} | Prix: {p['current_price_eur']} EUR | P&L: {p['pnl_eur']} EUR ({p['pnl_pct']}%)")
