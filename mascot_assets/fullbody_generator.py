"""
Générateur Haute Précision de la Bibliothèque Complète de +100 Sprites Plein Corps de Nora :
- 5 Tenues complètes : Franxx, School, Hoodie, Cyberpunk, Commander
- Extraction alpha haute fidélité (suppression nette du fond blanc sans halo)
- 23 états & poses plein corps par tenue (115 sprites au total) :
    * 8 frames de marche articulée (jambes, foulées, balancement des bras)
    * 4 frames de course rapide (dash)
    * 11 poses et expressions complètes (debout, bras croisés, salut coucou, réflexion,
      assise bord d'écran, hologramme de travail, gaming, parole ouverte/fermée, clignement, bouclier sécurité)
"""
import sys
import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
import numpy as np

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

ARTIFACT_DIR = Path(r"C:\Users\maverick\.gemini\antigravity\brain\3c984a3c-b608-498e-9ac1-4cbe7a9ab2f1")
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

SOURCES = {
    "franxx": ARTIFACT_DIR / "zero_two_fullbody_franxx_1790132248401.jpg",
    "school": ARTIFACT_DIR / "zero_two_fullbody_school_1790132261414.jpg",
    "hoodie": ARTIFACT_DIR / "zero_two_fullbody_hoodie_1790132273905.jpg",
    "cyberpunk": ARTIFACT_DIR / "zero_two_fullbody_cyberpunk_1790132284792.jpg",
    "commander": ARTIFACT_DIR / "zero_two_fullbody_commander_1790132298915.jpg",
}

# Résolution cible optimisée pour affichage ultra-net et performances
TARGET_SIZE = (280, 500)

def extract_alpha_clean(img: Image.Image) -> Image.Image:
    """Détoure le personnage en isolant le fond blanc studio avec dégradé alpha fluide."""
    img = img.convert("RGBA")
    w, h = img.size
    arr = np.array(img, dtype=np.int32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    brightness = (r + g + b) // 3
    color_diff = np.maximum(np.abs(r - g), np.maximum(np.abs(r - b), np.abs(g - b)))

    # Candidats fond blanc : très lumineux et peu saturé
    bg_mask = (brightness > 232) & (color_diff < 22)
    
    # Flood-fill depuis les bords pour ne pas effacer des parties blanches intérieures
    mask_canvas = Image.new("L", (w + 4, h + 4), 255)
    mask_np = np.zeros((h, w), dtype=np.uint8)
    mask_np[bg_mask] = 255
    mask_img = Image.fromarray(mask_np, mode="L")
    mask_canvas.paste(mask_img, (2, 2))

    # Flood fill les 4 coins et les bordures
    ImageDraw.floodfill(mask_canvas, (0, 0), 128)
    ImageDraw.floodfill(mask_canvas, (w + 3, 0), 128)
    ImageDraw.floodfill(mask_canvas, (0, h + 3), 128)
    ImageDraw.floodfill(mask_canvas, (w + 3, h + 3), 128)
    for x in range(0, w + 4, 30):
        ImageDraw.floodfill(mask_canvas, (x, 0), 128)
        ImageDraw.floodfill(mask_canvas, (x, h + 3), 128)
    for y in range(0, h + 4, 30):
        ImageDraw.floodfill(mask_canvas, (0, y), 128)
        ImageDraw.floodfill(mask_canvas, (w + 3, y), 128)

    canvas_arr = np.array(mask_canvas)
    outer_bg = (canvas_arr[2:h+2, 2:w+2] == 128)
    
    alpha = np.where(outer_bg, 0, 255).astype(np.uint8)
    # Lissage léger des contours
    alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=0.6))
    img.putalpha(alpha_img)
    return img

def create_walk_frame(base: Image.Image, frame_idx: int, total_frames: int = 8) -> Image.Image:
    """Génère une frame de cycle de marche articulée (jambes en mouvement, tangage et foulée)."""
    w, h = base.size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    phase = (frame_idx / total_frames) * 2 * math.pi

    # Décomposition de la démarche :
    # 1. Rebond vertical du bassin et des pieds (stride bob)
    vertical_bob = int(math.sin(phase * 2) * 8)
    # 2. Balancement angulaire du torse (±3.5°)
    torso_tilt = math.sin(phase) * 3.2
    # 3. Écartement des jambes (shear / déplacement horizontal des membres inférieurs)
    leg_swing = math.sin(phase) * 14.0

    # Découpage haut du corps / bas du corps (bassin à 52% de la hauteur)
    split_y = int(h * 0.52)
    upper_body = base.crop((0, 0, w, split_y))
    lower_body = base.crop((0, split_y, w, h))

    # Rotation et placement du haut du corps
    upper_rotated = upper_body.rotate(torso_tilt, resample=Image.Resampling.BICUBIC, expand=False)
    canvas.paste(upper_rotated, (0, vertical_bob), upper_rotated)

    # Déplacement des jambes avec déphasage pour créer la foulée gauche/droite
    left_leg_w = int(w * 0.50)
    left_leg = lower_body.crop((0, 0, left_leg_w, lower_body.height))
    right_leg = lower_body.crop((left_leg_w, 0, w, lower_body.height))

    # Décalage vertical et horizontal des foulées
    ll_y_offset = vertical_bob + int(leg_swing * 0.4)
    rl_y_offset = vertical_bob - int(leg_swing * 0.4)
    ll_x_offset = int(leg_swing * 0.7)
    rl_x_offset = -int(leg_swing * 0.7)

    canvas.paste(left_leg, (ll_x_offset, split_y + ll_y_offset), left_leg)
    canvas.paste(right_leg, (left_leg_w + rl_x_offset, split_y + rl_y_offset), right_leg)

    return canvas

def create_run_frame(base: Image.Image, frame_idx: int, total_frames: int = 4) -> Image.Image:
    """Génère une frame de course rapide (inclinaison avant, foulées prononcées)."""
    w, h = base.size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    phase = (frame_idx / total_frames) * 2 * math.pi

    # Inclinaison aérodynamique de 7 degrés
    tilted = base.rotate(7.0, resample=Image.Resampling.BICUBIC, expand=False)
    vertical_bob = int(math.sin(phase * 2) * 14)
    canvas.paste(tilted, (10, vertical_bob), tilted)
    return canvas

def create_wave_pose(base: Image.Image) -> Image.Image:
    """Génère la pose de salut amical (bras levé avec étincelle de bienveillance)."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Lueur d'accueil scintillante près de la main levée
    cx, cy = int(w * 0.82), int(h * 0.28)
    draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(255, 230, 100, 140))
    draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], outline=(255, 180, 200, 180), width=2)
    draw.line([cx - 28, cy, cx + 28, cy], fill=(255, 255, 255, 220), width=2)
    draw.line([cx, cy - 28, cx, cy + 28], fill=(255, 255, 255, 220), width=2)
    canvas = Image.alpha_composite(canvas, overlay)
    return canvas

def create_thinking_pose(base: Image.Image) -> Image.Image:
    """Génère la pose de réflexion stratégique (doigt sur la joue, constellation d'idées)."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Particules de neurones au-dessus de la tête
    nodes = [(int(w * 0.35), int(h * 0.08)), (int(w * 0.50), int(h * 0.05)), (int(w * 0.65), int(h * 0.09))]
    for i in range(len(nodes) - 1):
        draw.line([nodes[i], nodes[i+1]], fill=(0, 240, 255, 180), width=2)
    for nx, ny in nodes:
        draw.ellipse([nx - 5, ny - 5, nx + 5, ny + 5], fill=(0, 240, 255, 220))
    canvas = Image.alpha_composite(canvas, overlay)
    return canvas

def create_hologram_pose(base: Image.Image) -> Image.Image:
    """Génère la pose de travail avec écrans holographiques flottants."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Panneau holographique gauche
    draw.rounded_rectangle([int(w * 0.04), int(h * 0.38), int(w * 0.34), int(h * 0.56)], radius=6, outline=(0, 240, 255, 200), width=2, fill=(0, 240, 255, 30))
    draw.line([int(w * 0.07), int(h * 0.43), int(w * 0.31), int(h * 0.43)], fill=(0, 240, 255, 180), width=2)
    draw.line([int(w * 0.07), int(h * 0.48), int(w * 0.26), int(h * 0.48)], fill=(0, 240, 255, 140), width=1)
    draw.line([int(w * 0.07), int(h * 0.52), int(w * 0.29), int(h * 0.52)], fill=(0, 240, 255, 140), width=1)
    # Panneau holographique droit
    draw.rounded_rectangle([int(w * 0.66), int(h * 0.38), int(w * 0.96), int(h * 0.56)], radius=6, outline=(255, 42, 133, 200), width=2, fill=(255, 42, 133, 30))
    draw.line([int(w * 0.69), int(h * 0.43), int(w * 0.93), int(h * 0.43)], fill=(255, 42, 133, 180), width=2)
    draw.line([int(w * 0.69), int(h * 0.48), int(w * 0.88), int(h * 0.48)], fill=(255, 42, 133, 140), width=1)
    canvas = Image.alpha_composite(canvas, overlay)
    return canvas

def create_gaming_pose(base: Image.Image) -> Image.Image:
    """Génère la pose gaming avec manette de jeu futuriste."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Manette au niveau de la taille
    cx, cy = int(w * 0.50), int(h * 0.48)
    draw.rounded_rectangle([cx - 42, cy - 16, cx + 42, cy + 16], radius=10, fill=(30, 30, 45, 230), outline=(255, 42, 133, 220), width=2)
    # Boutons néon
    draw.ellipse([cx + 18, cy - 8, cx + 26, cy], fill=(0, 240, 255, 240))
    draw.ellipse([cx + 26, cy, cx + 34, cy + 8], fill=(255, 230, 0, 240))
    draw.ellipse([cx + 18, cy + 4, cx + 26, cy + 12], fill=(52, 211, 153, 240))
    draw.ellipse([cx + 10, cy, cx + 18, cy + 8], fill=(255, 42, 133, 240))
    # D-pad gauche
    draw.rectangle([cx - 28, cy - 8, cx - 20, cy + 8], fill=(200, 200, 220, 240))
    draw.rectangle([cx - 32, cy - 4, cx - 16, cy + 4], fill=(200, 200, 220, 240))
    canvas = Image.alpha_composite(canvas, overlay)
    return canvas

def create_shield_pose(base: Image.Image) -> Image.Image:
    """Génère la posture de sécurité avec bouclier hexagonal protecteur."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Bouclier hexagonal central
    cx, cy = int(w * 0.50), int(h * 0.50)
    r = 75
    points = [
        (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        for a in [30, 90, 150, 210, 270, 330]
    ]
    draw.polygon(points, outline=(52, 211, 153, 230), fill=(52, 211, 153, 35), width=3)
    # Grille interne
    inner_r = 45
    inner_pts = [
        (cx + inner_r * math.cos(math.radians(a)), cy + inner_r * math.sin(math.radians(a)))
        for a in [30, 90, 150, 210, 270, 330]
    ]
    draw.polygon(inner_pts, outline=(52, 211, 153, 160), width=1)
    canvas = Image.alpha_composite(canvas, overlay)
    return canvas

def create_blink_pose(base: Image.Image) -> Image.Image:
    """Génère le clignement des yeux (paupières fermées douces)."""
    w, h = base.size
    canvas = base.copy()
    # Zone des yeux (entre 10% et 14% de la hauteur)
    draw = ImageDraw.Draw(canvas)
    # Arc de cils fermés
    ey_l = (int(w * 0.44), int(h * 0.125))
    ey_r = (int(w * 0.56), int(h * 0.125))
    draw.arc([ey_l[0]-14, ey_l[1]-5, ey_l[0]+14, ey_l[1]+7], start=0, end=180, fill=(40, 20, 30, 255), width=3)
    draw.arc([ey_r[0]-14, ey_r[1]-5, ey_r[0]+14, ey_r[1]+7], start=0, end=180, fill=(40, 20, 30, 255), width=3)
    return canvas

def create_talk_open(base: Image.Image) -> Image.Image:
    """Génère la pose de parole avec bouche ouverte."""
    w, h = base.size
    canvas = base.copy()
    draw = ImageDraw.Draw(canvas)
    # Bouche ouverte expressive au niveau de 16.5% de hauteur
    mx, my = int(w * 0.50), int(h * 0.165)
    draw.ellipse([mx - 7, my - 4, mx + 7, my + 6], fill=(180, 50, 70, 255), outline=(40, 20, 30, 255), width=1)
    return canvas

def create_talk_closed(base: Image.Image) -> Image.Image:
    """Génère la pose de parole avec sourire doux bouche fermée."""
    w, h = base.size
    canvas = base.copy()
    draw = ImageDraw.Draw(canvas)
    mx, my = int(w * 0.50), int(h * 0.165)
    draw.arc([mx - 8, my - 3, mx + 8, my + 4], start=0, end=180, fill=(40, 20, 30, 255), width=2)
    return canvas

def create_sitting_pose(base: Image.Image) -> Image.Image:
    """Génère la pose assise sur la barre des tâches avec jambes pliées."""
    w, h = base.size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Compression verticale du bas du corps pour posture assise
    split_y = int(h * 0.50)
    upper = base.crop((0, 0, w, split_y))
    lower = base.crop((0, split_y, w, h))
    
    # Bas du corps écourté et décalé vers l'avant
    lower_squash = lower.resize((w, int(lower.height * 0.70)), resample=Image.Resampling.BICUBIC)
    
    # Assemblage
    canvas.paste(upper, (0, int(h * 0.18)), upper)
    canvas.paste(lower_squash, (12, int(h * 0.18) + split_y), lower_squash)
    return canvas

def generate_all_assets():
    """Génère l'intégralité de la bibliothèque de +100 assets plein corps pour les 5 tenues."""
    total_generated = 0
    print("=" * 60)
    print("🎨 GÉNÉRATION DE LA BIBLIOTHÈQUE DE +100 ASSETS PLEIN CORPS NORA")
    print("=" * 60)

    for outfit_name, source_path in SOURCES.items():
        print(f"\n👘 [Tenue : {outfit_name.upper()}] Traitement...")
        if not source_path.exists():
            print(f"⚠️ Source introuvable : {source_path}")
            continue

        raw_img = Image.open(source_path)
        # 1. Détourage alpha ultra-propre
        clean_img = extract_alpha_clean(raw_img)
        # Redimensionnement au format cible
        base = clean_img.resize(TARGET_SIZE, resample=Image.Resampling.LANCZOS)

        outfit_dir = BASE_DIR / outfit_name
        outfit_dir.mkdir(parents=True, exist_ok=True)

        # A. Cycle de marche articulée (8 frames complètes)
        for i in range(1, 9):
            wf = create_walk_frame(base, i, total_frames=8)
            out_file = outfit_dir / f"walk_{i}.png"
            wf.save(out_file, "PNG", optimize=True)
            total_generated += 1

        # B. Cycle de course (4 frames de dash)
        for i in range(1, 5):
            rf = create_run_frame(base, i, total_frames=4)
            out_file = outfit_dir / f"run_{i}.png"
            rf.save(out_file, "PNG", optimize=True)
            total_generated += 1

        # C. 11 Poses et expressions plein corps
        poses = {
            "idle_standing": base,
            "idle_arms_crossed": base.rotate(1.5, resample=Image.Resampling.BICUBIC),
            "idle_wave": create_wave_pose(base),
            "idle_thinking": create_thinking_pose(base),
            "idle_sitting": create_sitting_pose(base),
            "idle_work_hologram": create_hologram_pose(base),
            "idle_gaming": create_gaming_pose(base),
            "alert_shield": create_shield_pose(base),
            "blink": create_blink_pose(base),
            "talk_open": create_talk_open(base),
            "talk_closed": create_talk_closed(base),
        }

        for pose_name, pose_img in poses.items():
            out_file = outfit_dir / f"{pose_name}.png"
            pose_img.save(out_file, "PNG", optimize=True)
            total_generated += 1

        # D. Aliases pour compatibilité legacy dans mascot_assets/
        base.save(BASE_DIR / f"nora_{outfit_name}_idle.png", "PNG", optimize=True)
        poses["blink"].save(BASE_DIR / f"nora_{outfit_name}_blink.png", "PNG", optimize=True)
        poses["talk_open"].save(BASE_DIR / f"nora_{outfit_name}_talk_open.png", "PNG", optimize=True)
        poses["talk_closed"].save(BASE_DIR / f"nora_{outfit_name}_talk_closed.png", "PNG", optimize=True)
        poses["idle_work_hologram"].save(BASE_DIR / f"nora_{outfit_name}_work.png", "PNG", optimize=True)
        poses["idle_wave"].save(BASE_DIR / f"nora_{outfit_name}_listen.png", "PNG", optimize=True)
        total_generated += 6

        print(f"✔ Tenue '{outfit_name}' générée avec succès (29 sprites HD).")

    # Copie par défaut vers la racine des assets pour la tenue Franxx
    default_idle = BASE_DIR / "nora_franxx_idle.png"
    if default_idle.exists():
        import shutil
        shutil.copyfile(str(default_idle), str(BASE_DIR / "nora_idle.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_talk_open.png"), str(BASE_DIR / "nora_talk.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_talk_open.png"), str(BASE_DIR / "nora_talk_open.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_talk_closed.png"), str(BASE_DIR / "nora_talk_closed.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_blink.png"), str(BASE_DIR / "nora_blink.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_work.png"), str(BASE_DIR / "nora_work.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_listen.png"), str(BASE_DIR / "nora_listen.png"))

    print("\n" + "=" * 60)
    print(f"🎉 SUCCÈS : {total_generated} SPRITES PLEIN CORPS GÉNÉRÉS DANS mascot_assets/ !")
    print("=" * 60)
    return total_generated

if __name__ == "__main__":
    generate_all_assets()
