"""
Génération et gestion des sprites haute fidélité de Nora (Style Studio Anime Zero Two) :
- Sprites HD réalistes issus de créations studio anime haute définition
- 3 Tenues complètes : Pilote Franxx, Écolière Sailor, Hoodie Doux Pastel
- Détourage alpha avancé par flood-fill et lissage des contours sans halo
- 6 expressions et états d'animation par tenue (18 sprites au total)
- Support de l'icône multi-résolution Windows .ico
"""
import sys
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    PROJECT_DIR = Path(sys.executable).parent.resolve()
else:
    PROJECT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_DIR / "mascot_assets"
SOURCE_DIR = ASSETS_DIR / "source"
ASSETS_DIR.mkdir(exist_ok=True)
SOURCE_DIR.mkdir(exist_ok=True)

# Sources d'images HD générées (fichiers de référence haute résolution)
ARTIFACT_DIR = Path(r"C:\Users\maverick\.gemini\antigravity\brain\3c984a3c-b608-498e-9ac1-4cbe7a9ab2f1")

HD_SOURCES = {
    "franxx_idle": ARTIFACT_DIR / "zero_two_hd_preview_1789948772562.jpg",
    "franxx_blink": ARTIFACT_DIR / "zero_two_blink_hd_1789949236607.jpg",
    "franxx_talk": ARTIFACT_DIR / "zero_two_talk_hd_1789949246722.jpg",
    "school_idle": ARTIFACT_DIR / "zero_two_school_hd_1789949184453.jpg",
    "school_blink": ARTIFACT_DIR / "zero_two_school_blink_hd_1789949257641.jpg",
    "hoodie_idle": ARTIFACT_DIR / "zero_two_hoodie_hd_1789949194775.jpg",
    "hoodie_blink": ARTIFACT_DIR / "zero_two_hoodie_blink_hd_1789949269804.jpg",
}

SPRITE_SIZE = (280, 280)

def backup_and_localize_sources():
    """Copie les sources HD dans le dossier permanent du projet."""
    for key, art_path in HD_SOURCES.items():
        dest = SOURCE_DIR / f"{key}.jpg"
        if art_path.exists() and not dest.exists():
            shutil.copyfile(str(art_path), str(dest))

def remove_background_hd(img: Image.Image) -> Image.Image:
    """Extrait le personnage avec précision sur fond transparent et contours lisses."""
    w, h = img.size
    img_rgba = img.convert("RGBA")
    arr = np.array(img_rgba, dtype=np.int32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    brightness = (r + g + b) // 3
    max_diff = np.maximum(np.abs(r - g), np.maximum(np.abs(r - b), np.abs(g - b)))

    # Fond de studio blanc / très clair
    bg_candidate = (brightness > 230) & (max_diff < 26)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[bg_candidate] = 255

    # Flood fill depuis les 4 coins pour préserver l'intérieur (ex: chemisier blanc ou serre-tête)
    mask_img = Image.fromarray(mask, mode='L')
    canvas = Image.new('L', (w + 4, h + 4), 255)
    canvas.paste(mask_img, (2, 2))
    ImageDraw.floodfill(canvas, (0, 0), 128)
    ImageDraw.floodfill(canvas, (w + 3, 0), 128)
    ImageDraw.floodfill(canvas, (0, h + 3), 128)
    ImageDraw.floodfill(canvas, (w + 3, h + 3), 128)

    canvas_arr = np.array(canvas)
    outer_bg = (canvas_arr[2:h+2, 2:w+2] == 128)
    final_alpha = np.where(outer_bg, 0, 255).astype(np.uint8)

    # Nettoyage des ombres au niveau des coins inférieurs
    for y in range(int(h * 0.70), h):
        for x in list(range(0, int(w * 0.18))) + list(range(int(w * 0.82), w)):
            if brightness[y, x] > 215 and max_diff[y, x] < 35:
                final_alpha[y, x] = 0

    # Lissage léger des bords pour un fondu naturel
    alpha_img = Image.fromarray(final_alpha, mode='L').filter(ImageFilter.GaussianBlur(radius=0.7))
    img_rgba.putalpha(alpha_img)
    return img_rgba

def add_listening_aura(sprite: Image.Image) -> Image.Image:
    """Ajoute une lueur émeraude d'écoute bienveillante."""
    w, h = sprite.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Ondes sonores douces autour de la tête
    draw.ellipse([int(w * 0.22), int(h * 0.10), int(w * 0.78), int(h * 0.65)], outline=(52, 211, 153, 110), width=2)
    draw.ellipse([int(w * 0.18), int(h * 0.06), int(w * 0.82), int(h * 0.70)], outline=(16, 185, 129, 60), width=2)
    
    # Étoiles de brillance dans le regard
    cx_l, cy_l = int(w * 0.51), int(h * 0.42)
    cx_r, cy_r = int(w * 0.68), int(h * 0.41)
    draw.ellipse([cx_l - 3, cy_l - 3, cx_l + 3, cy_l + 3], fill=(254, 240, 138, 220))
    draw.ellipse([cx_r - 3, cy_r - 3, cx_r + 3, cy_r + 3], fill=(254, 240, 138, 220))
    
    return Image.alpha_composite(sprite, overlay)

def add_work_hud(sprite: Image.Image) -> Image.Image:
    """Ajoute un viseur holographique Franxx futuriste (Mode travail / analyse)."""
    w, h = sprite.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Réticule holographique cyan & rouge style cockpit Franxx
    y_eye = int(h * 0.42)
    draw.line([(int(w * 0.35), y_eye), (int(w * 0.80), y_eye)], fill=(6, 182, 212, 160), width=2)
    draw.ellipse([int(w * 0.45), y_eye - 18, int(w * 0.58), y_eye + 18], outline=(6, 182, 212, 140), width=1)
    draw.ellipse([int(w * 0.62), y_eye - 18, int(w * 0.75), y_eye + 18], outline=(6, 182, 212, 140), width=1)
    draw.arc([int(w * 0.30), int(h * 0.15), int(w * 0.75), int(h * 0.55)], start=200, end=340, fill=(239, 68, 68, 160), width=2)
    
    return Image.alpha_composite(sprite, overlay)

def generate_all_zero_two_assets(force: bool = False):
    """Génère tous les sprites HD à partir des illustrations anime de studio si nécessaire."""
    outfits = ["franxx", "school", "hoodie"]
    states = ["idle", "blink", "talk_open", "talk_closed", "listen", "work"]

    if not force:
        all_exist = all((ASSETS_DIR / f"nora_{o}_{s}.png").exists() for o in outfits for s in states)
        if all_exist and (ASSETS_DIR / "nora_idle.png").exists() and (ASSETS_DIR / "nora.ico").exists():
            return

    backup_and_localize_sources()

    for outfit in outfits:
        # Charger les sources de l'outfit
        src_idle_file = SOURCE_DIR / f"{outfit}_idle.jpg"
        src_blink_file = SOURCE_DIR / f"{outfit}_blink.jpg"
        src_talk_file = SOURCE_DIR / f"{outfit}_talk.jpg"

        # Repli si pas de talk spécifique
        if not src_talk_file.exists():
            src_talk_file = src_idle_file

        raw_idle = Image.open(src_idle_file if src_idle_file.exists() else HD_SOURCES[f"{outfit}_idle"])
        raw_blink = Image.open(src_blink_file if src_blink_file.exists() else HD_SOURCES[f"{outfit}_blink"])
        raw_talk = Image.open(src_talk_file if src_talk_file.exists() else src_idle_file)

        # Extraction transparente
        trans_idle = remove_background_hd(raw_idle).resize(SPRITE_SIZE, Image.Resampling.LANCZOS)
        trans_blink = remove_background_hd(raw_blink).resize(SPRITE_SIZE, Image.Resampling.LANCZOS)
        trans_talk_open = remove_background_hd(raw_talk).resize(SPRITE_SIZE, Image.Resampling.LANCZOS)
        
        # talk_closed : fondu naturel
        trans_talk_closed = Image.blend(trans_idle, trans_talk_open, alpha=0.35)

        # listen et work avec auras cyber Franxx
        trans_listen = add_listening_aura(trans_idle)
        trans_work = add_work_hud(trans_idle)

        sprites_map = {
            "idle": trans_idle,
            "blink": trans_blink,
            "talk_open": trans_talk_open,
            "talk_closed": trans_talk_closed,
            "listen": trans_listen,
            "work": trans_work
        }

        for st, img_obj in sprites_map.items():
            out_file = ASSETS_DIR / f"nora_{outfit}_{st}.png"
            img_obj.save(out_file, "PNG")

    # Mettre à jour les fichiers actifs par défaut
    import memory_manager
    active_outfit = memory_manager.get_current_outfit()
    set_active_outfit(active_outfit)

    # Mettre à jour l'icône .ico de Nora
    from setup_shortcuts import ensure_nora_icon
    ensure_nora_icon()
    print("✔ Tous les sprites HD Studio Anime générés avec succès !")

def set_active_outfit(outfit: str):
    """Copie les fichiers de la tenue choisie vers les noms nora_*.png actifs."""
    if outfit not in ["franxx", "school", "hoodie", "cyberpunk", "commander"]:
        outfit = "franxx"
    states = ["idle", "idle_standing", "blink", "talk_open", "talk_closed", "listen", "work"]
    for st in states:
        src = ASSETS_DIR / outfit / f"{st}.png"
        if not src.exists():
            src = ASSETS_DIR / f"nora_{outfit}_{st}.png"
        dst = ASSETS_DIR / f"nora_{st}.png"
        if src.exists():
            shutil.copyfile(str(src), str(dst))

    # Assurer que nora_idle.png pointe vers idle_standing.png si présent
    idle_src = ASSETS_DIR / outfit / "idle_standing.png"
    if not idle_src.exists():
        idle_src = ASSETS_DIR / outfit / "idle.png"
    if idle_src.exists():
        shutil.copyfile(str(idle_src), str(ASSETS_DIR / "nora_idle.png"))

    # Dupliquer talk_open en nora_talk.png
    talk_open = ASSETS_DIR / outfit / "talk_open.png"
    if not talk_open.exists():
        talk_open = ASSETS_DIR / "nora_talk_open.png"
    talk_dst = ASSETS_DIR / "nora_talk.png"
    if talk_open.exists():
        shutil.copyfile(str(talk_open), str(talk_dst))

if __name__ == "__main__":
    generate_all_zero_two_assets()
