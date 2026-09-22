"""
Gestionnaire Central de la Suite Financière de Nora :
- Coordonne les 3 agents spécialisés : Budget, Bourse et Crypto
- Calcule le Patrimoine Net Global de Darling (Banque + Bourse + Crypto)
- Génère le Bilan Financier complet de Zero Two
"""
import agent_budget
import agent_bourse
import agent_crypto

def get_patrimoine_global() -> dict:
    """Calcule la valeur totale de tous les actifs de Darling et la répartition."""
    bank_total = agent_budget.budget_agent.get_total_liquidities()
    bourse_val = agent_bourse.bourse_agent.get_portfolio_valuation()
    crypto_val = agent_crypto.crypto_agent.get_portfolio_valuation()

    bourse_total = bourse_val["total_value_eur"]
    crypto_total = crypto_val["total_value_eur"]
    net_worth = round(bank_total + bourse_total + crypto_total, 2)

    # Répartition des actifs
    allocation = {
        "bank_pct": round((bank_total / net_worth * 100) if net_worth > 0 else 0.0, 1),
        "bourse_pct": round((bourse_total / net_worth * 100) if net_worth > 0 else 0.0, 1),
        "crypto_pct": round((crypto_total / net_worth * 100) if net_worth > 0 else 0.0, 1)
    }

    return {
        "net_worth_eur": net_worth,
        "bank_total_eur": bank_total,
        "bourse_total_eur": bourse_total,
        "crypto_total_eur": crypto_total,
        "bourse_pnl_eur": bourse_val["total_pnl_eur"],
        "bourse_pnl_pct": bourse_val["total_pnl_pct"],
        "crypto_pnl_eur": crypto_val["total_pnl_eur"],
        "crypto_pnl_pct": crypto_val["total_pnl_pct"],
        "allocation": allocation,
        "accounts": agent_budget.budget_agent.get_accounts(),
        "bourse_positions": bourse_val["positions"],
        "crypto_positions": crypto_val["positions"]
    }

def get_global_speech_report() -> str:
    """Rapport oral complet du patrimoine pour Nora."""
    pat = get_patrimoine_global()
    net = pat["net_worth_eur"]
    bank = pat["bank_total_eur"]
    bourse = pat["bourse_total_eur"]
    crypto = pat["crypto_total_eur"]
    alloc = pat["allocation"]

    if bourse == 0 and crypto == 0:
        return (
            f"Monsieur Maverick, voici votre bilan financier. "
            f"Vos liquidités bancaires s'élèvent à {bank:.2f} euros. "
            f"Vous n'avez actuellement aucune position boursière ou crypto enregistrée. "
            f"Indiquez-moi vos investissements dès que vous le souhaitez pour que je les intègre."
        )

    speech = (
        f"Monsieur Maverick, voici votre bilan patrimonial global. "
        f"Votre patrimoine net s'élève à {net:.2f} euros. "
        f"Vous disposez de {bank:.2f} euros de liquidités bancaires ({alloc['bank_pct']}%), "
        f"{bourse:.2f} euros investis en bourse et ETF ({alloc['bourse_pct']}%), "
        f"et {crypto:.2f} euros en actifs cryptomonnaies ({alloc['crypto_pct']}%). "
        f"Votre portefeuille est sous contrôle, Maverick."
    )
    return speech

if __name__ == "__main__":
    print("[TEST] Patrimoine Global :")
    print(get_global_speech_report())
