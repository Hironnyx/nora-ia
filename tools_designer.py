"""
Module d'outils pour l'Agent Designer : création visuelle, graphismes SVG, styles CSS et thèmes.
"""
import os
from pathlib import Path

DESIGNS_DIR = Path("creations_visuelles").resolve()
DESIGNS_DIR.mkdir(exist_ok=True)

THEME_PALETTES = {
    "cyberpunk": {
        "primary": "#00f0ff",
        "secondary": "#ff007f",
        "background": "#0b0c10",
        "surface": "#1f2833",
        "text": "#ffffff",
        "accent": "#ffe600"
    },
    "kawaii": {
        "primary": "#ff9ebb",
        "secondary": "#a2d2ff",
        "background": "#fbf8cc",
        "surface": "#ffffff",
        "text": "#4a4e69",
        "accent": "#ffcbf2"
    },
    "minimal_dark": {
        "primary": "#6366f1",
        "secondary": "#8b5cf6",
        "background": "#0f172a",
        "surface": "#1e293b",
        "text": "#f8fafc",
        "accent": "#38bdf8"
    },
    "nature_zen": {
        "primary": "#2d6a4f",
        "secondary": "#52b788",
        "background": "#f7f9f7",
        "surface": "#d8f3dc",
        "text": "#1b4332",
        "accent": "#74c69d"
    }
}

def create_svg_graphic(filename: str, svg_code: str) -> str:
    """Crée et enregistre un graphique vectoriel SVG (icône, illustration, logo, schéma)."""
    if not filename.endswith(".svg"):
        filename += ".svg"
    out_file = DESIGNS_DIR / filename
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(svg_code.strip())
        return f"Graphique SVG créé avec succès : {out_file} ({len(svg_code)} octets)"
    except Exception as e:
        return f"Erreur lors de la création du fichier SVG : {str(e)}"

def generate_styled_html_page(title: str, html_body: str, theme: str = "cyberpunk", filename: str = None) -> str:
    """
    Génère une page web moderne et stylisée avec un design soigné (carte, typographie, responsive).
    Thèmes disponibles : 'cyberpunk', 'kawaii', 'minimal_dark', 'nature_zen'.
    """
    palette = THEME_PALETTES.get(theme.lower(), THEME_PALETTES["minimal_dark"])
    if not filename:
        filename = f"{title.lower().replace(' ', '_')[:30]}.html"
    elif not filename.endswith(".html"):
        filename += ".html"

    out_file = DESIGNS_DIR / filename

    styled_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }}
        body {{
            background-color: {palette['background']};
            color: {palette['text']};
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .card {{
            background-color: {palette['surface']};
            border: 2px solid {palette['primary']};
            border-radius: 16px;
            padding: 30px;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: {palette['primary']};
            border-bottom: 2px solid {palette['secondary']};
            padding-bottom: 12px;
            margin-bottom: 20px;
        }}
        .badge {{
            display: inline-block;
            background: {palette['secondary']};
            color: #fff;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-bottom: 15px;
        }}
        .content {{ line-height: 1.6; font-size: 1.05rem; }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">Créé par l'Agent Designer</span>
        <h1>{title}</h1>
        <div class="content">
            {html_body}
        </div>
    </div>
</body>
</html>
"""
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(styled_html)
        return f"Page stylisée générée avec succès : {out_file} (Thème: {theme})"
    except Exception as e:
        return f"Erreur lors de la génération de la page stylisée : {str(e)}"

def get_color_palette(theme_name: str = "cyberpunk") -> str:
    """Renvoie la palette de couleurs d'un thème pour guider la conception visuelle."""
    palette = THEME_PALETTES.get(theme_name.lower(), THEME_PALETTES["minimal_dark"])
    return f"Palette '{theme_name}' : " + ", ".join([f"{k}={v}" for k, v in palette.items()])
