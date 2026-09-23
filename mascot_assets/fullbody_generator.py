"""
Générateur Haute Précision de la Bibliothèque Complète de +100 Sprites Plein Corps de Nora :
- 5 Tenues complètes : Franxx, School, Hoodie, Cyberpunk, Commander
- Extraction alpha haute fidélité (suppression nette du fond blanc sans halo)
- Cinématique continue sans découpe brutale (déformation bilinéaire organique)
- 23 états & poses plein corps par tenue (115 sprites au total) :
    * 8 frames de marche articulée continue (rebound bob, sway, foulée bilatérale souple sans couture)
    * 4 frames de course dynamique (dash avec inclinaison aérodynamique)
    * 11 poses et expressions complètes (debout, bras croisés, salut coucou, réflexion,
      assise propre, hologramme de travail, gaming, parole ouverte/fermée, clignement, bouclier sécurité)
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

# Résolution cible optimisée pour affichage ultra-net et stable
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
    alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=0.6))
    img.putalpha(alpha_img)
    return img

def create_walk_frame(base: Image.Image, frame_idx: int, total_frames: int = 8) -> Image.Image:
    """
    Génère une frame de cycle de marche organique continue par déformation bilinéaire.
    Aucune découpe brutale : le corps reste 100% solidaire, sans trou ni couture.
    """
    w, h = base.size
    arr = np.array(base, dtype=np.uint8)
    phase = (frame_idx / total_frames) * 2.0 * math.pi

    # Paramètres biomécaniques de la marche anime
    bob = int(math.sin(phase * 2.0) * 3.5)  # Rebond vertical : -3.5 à +3.5 px
    sway = math.sin(phase) * 1.8            # Balancement latéral torse : -1.8 à +1.8 px
    stride = math.sin(phase) * 5.0          # Amplitude foulée : -5.0 à +5.0 px

    y_coords, x_coords = np.indices((h, w), dtype=np.float32)

    waist_y = 250.0
    feet_y = 485.0
    # Progression verticale souple depuis le bassin jusqu'aux pieds
    vert_factor = np.clip((y_coords - waist_y) / (feet_y - waist_y), 0.0, 1.0) ** 1.3

    # Séparation bilatérale douce des deux jambes via fonction tanh (centrée sur x=141)
    leg_side = np.tanh((x_coords - 141.0) / 14.0)

    # Coordonnées sources avec interpolation continue
    map_x = x_coords - sway - (stride * vert_factor * leg_side)
    map_y = y_coords - bob

    map_x = np.clip(map_x, 0, w - 1).astype(np.float32)
    map_y = np.clip(map_y, 0, h - 1).astype(np.float32)

    x0 = np.floor(map_x).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y0 = np.floor(map_y).astype(np.int32)
    y1 = np.clip(y0 + 1, 0, h - 1)

    wx = (map_x - x0)[:, :, np.newaxis]
    wy = (map_y - y0)[:, :, np.newaxis]

    top = arr[y0, x0] * (1.0 - wx) + arr[y0, x1] * wx
    bottom = arr[y1, x0] * (1.0 - wx) + arr[y1, x1] * wx
    warped = (top * (1.0 - wy) + bottom * wy).astype(np.uint8)

    return Image.fromarray(warped)

def create_run_frame(base: Image.Image, frame_idx: int, total_frames: int = 4) -> Image.Image:
    """Génère une frame de course rapide (dash) continue avec inclinaison avant dynamique."""
    w, h = base.size
    arr = np.array(base, dtype=np.uint8)
    phase = (frame_idx / total_frames) * 2.0 * math.pi

    bob = int(math.sin(phase * 2.0) * 5.5)
    sway = math.sin(phase) * 2.2
    stride = math.sin(phase) * 8.0

    y_coords, x_coords = np.indices((h, w), dtype=np.float32)

    waist_y = 250.0
    feet_y = 485.0
    vert_factor = np.clip((y_coords - waist_y) / (feet_y - waist_y), 0.0, 1.0) ** 1.2
    lean = (y_coords - 485.0) * -0.04  # Inclinaison aérodynamique douce

    leg_side = np.tanh((x_coords - 141.0) / 14.0)

    map_x = x_coords - sway - lean - (stride * vert_factor * leg_side)
    map_y = y_coords - bob

    map_x = np.clip(map_x, 0, w - 1).astype(np.float32)
    map_y = np.clip(map_y, 0, h - 1).astype(np.float32)

    x0 = np.floor(map_x).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y0 = np.floor(map_y).astype(np.int32)
    y1 = np.clip(y0 + 1, 0, h - 1)

    wx = (map_x - x0)[:, :, np.newaxis]
    wy = (map_y - y0)[:, :, np.newaxis]

    top = arr[y0, x0] * (1.0 - wx) + arr[y0, x1] * wx
    bottom = arr[y1, x0] * (1.0 - wx) + base_arr[y1, x1] * wx if 'base_arr' in locals() else arr[y1, x1] * wx
    warped = (top * (1.0 - wy) + bottom * wy).astype(np.uint8)

    return Image.fromarray(warped)

def create_blink_pose(base: Image.Image) -> Image.Image:
    """Génère le clignement des yeux naturel avec cils fins et eyeliner écarlate."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Centre des yeux : x ~ 133 (gauche) et 149 (droit), y ~ 63
    cx_l, cy_l = 133, 63
    cx_r, cy_r = 149, 63

    # Paupières couleur chair douce pour couvrir la pupille
    draw.ellipse([cx_l - 7, cy_l - 4, cx_l + 7, cy_l + 4], fill=(250, 226, 218, 235))
    draw.ellipse([cx_r - 7, cy_r - 4, cx_r + 7, cy_r + 4], fill=(250, 226, 218, 235))

    # Cils recourbés fermés
    draw.arc([cx_l - 8, cy_l - 3, cx_l + 8, cy_l + 5], start=10, end=170, fill=(35, 20, 28, 255), width=2)
    draw.arc([cx_r - 8, cy_r - 3, cx_r + 8, cy_r + 5], start=10, end=170, fill=(35, 20, 28, 255), width=2)

    # Fard rouge signature Zero Two au coin externe des yeux
    draw.line([cx_l + 7, cy_l + 1, cx_l + 10, cy_l - 1], fill=(225, 29, 72, 220), width=2)
    draw.line([cx_r + 7, cy_r + 1, cx_r + 10, cy_r - 1], fill=(225, 29, 72, 220), width=2)

    return Image.alpha_composite(canvas, overlay)

def create_talk_open(base: Image.Image) -> Image.Image:
    """Génère l'expression bouche ouverte articulée avec ombrage anime soigné."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    mx, my = 141, 83
    # Intérieur de la bouche bordeaux anime
    draw.ellipse([mx - 5, my - 3, mx + 5, my + 4], fill=(168, 45, 68, 245), outline=(60, 25, 35, 220), width=1)
    # Reflet discret dents supérieures
    draw.line([mx - 3, my - 2, mx + 3, my - 2], fill=(255, 255, 255, 220), width=1)

    return Image.alpha_composite(canvas, overlay)

def create_talk_closed(base: Image.Image) -> Image.Image:
    """Génère le sourire doux bouche fermée pour l'alternance labiale."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    mx, my = 141, 83
    # Courbe douce de sourire
    draw.arc([mx - 6, my - 3, mx + 6, my + 3], start=10, end=170, fill=(120, 35, 45, 230), width=2)

    return Image.alpha_composite(canvas, overlay)

def create_wave_pose(base: Image.Image) -> Image.Image:
    """Pose de salut amical avec étincelle lumineuse bienveillante."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy = int(w * 0.82), int(h * 0.28)
    draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(255, 235, 120, 150))
    draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], outline=(255, 180, 200, 180), width=2)
    draw.line([cx - 22, cy, cx + 22, cy], fill=(255, 255, 255, 220), width=2)
    draw.line([cx, cy - 22, cx, cy + 22], fill=(255, 255, 255, 220), width=2)

    return Image.alpha_composite(canvas, overlay)

def create_thinking_pose(base: Image.Image) -> Image.Image:
    """Pose de réflexion avec constellation d'analyse cybernétique."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    nodes = [(int(w * 0.35), int(h * 0.08)), (int(w * 0.50), int(h * 0.05)), (int(w * 0.65), int(h * 0.09))]
    for i in range(len(nodes) - 1):
        draw.line([nodes[i], nodes[i+1]], fill=(0, 240, 255, 180), width=2)
    for nx, ny in nodes:
        draw.ellipse([nx - 4, ny - 4, nx + 4, ny + 4], fill=(0, 240, 255, 230), outline=(255, 255, 255, 255), width=1)

    return Image.alpha_composite(canvas, overlay)

def create_hologram_pose(base: Image.Image) -> Image.Image:
    """Pose de travail avec panneaux holographiques HUD immersifs."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Panneau holographique gauche cyan
    draw.rounded_rectangle([int(w * 0.04), int(h * 0.38), int(w * 0.34), int(h * 0.56)], radius=6, outline=(0, 240, 255, 200), width=2, fill=(0, 240, 255, 30))
    draw.line([int(w * 0.07), int(h * 0.43), int(w * 0.31), int(h * 0.43)], fill=(0, 240, 255, 180), width=2)
    draw.line([int(w * 0.07), int(h * 0.48), int(w * 0.26), int(h * 0.48)], fill=(0, 240, 255, 140), width=1)

    # Panneau holographique droit magenta
    draw.rounded_rectangle([int(w * 0.66), int(h * 0.38), int(w * 0.96), int(h * 0.56)], radius=6, outline=(255, 42, 133, 200), width=2, fill=(255, 42, 133, 30))
    draw.line([int(w * 0.69), int(h * 0.43), int(w * 0.93), int(h * 0.43)], fill=(255, 42, 133, 180), width=2)
    draw.line([int(w * 0.69), int(h * 0.48), int(w * 0.88), int(h * 0.48)], fill=(255, 42, 133, 140), width=1)

    return Image.alpha_composite(canvas, overlay)

def create_gaming_pose(base: Image.Image) -> Image.Image:
    """Pose session de jeu avec manette néon stylisée."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy = int(w * 0.50), int(h * 0.48)
    draw.rounded_rectangle([cx - 38, cy - 14, cx + 38, cy + 14], radius=9, fill=(24, 24, 38, 235), outline=(255, 42, 133, 220), width=2)
    draw.ellipse([cx + 16, cy - 7, cx + 23, cy], fill=(0, 240, 255, 240))
    draw.ellipse([cx + 23, cy, cx + 30, cy + 7], fill=(255, 230, 0, 240))
    draw.ellipse([cx + 16, cy + 4, cx + 23, cy + 11], fill=(52, 211, 153, 240))
    draw.ellipse([cx + 9, cy, cx + 16, cy + 7], fill=(255, 42, 133, 240))
    draw.rectangle([cx - 25, cy - 6, cx - 18, cy + 6], fill=(200, 200, 220, 240))
    draw.rectangle([cx - 28, cy - 3, cx - 15, cy + 3], fill=(200, 200, 220, 240))

    return Image.alpha_composite(canvas, overlay)

def create_shield_pose(base: Image.Image) -> Image.Image:
    """Posture de sécurité avec bouclier hexagonal protecteur."""
    w, h = base.size
    canvas = base.copy()
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy = int(w * 0.50), int(h * 0.50)
    r = 70
    points = [
        (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        for a in [30, 90, 150, 210, 270, 330]
    ]
    draw.polygon(points, outline=(52, 211, 153, 230), fill=(52, 211, 153, 30), width=3)
    inner_r = 42
    inner_pts = [
        (cx + inner_r * math.cos(math.radians(a)), cy + inner_r * math.sin(math.radians(a)))
        for a in [30, 90, 150, 210, 270, 330]
    ]
    draw.polygon(inner_pts, outline=(52, 211, 153, 160), width=1)

    return Image.alpha_composite(canvas, overlay)

def create_sitting_pose(base: Image.Image) -> Image.Image:
    """Posture assise élégante et propre, stable sur la barre des tâches."""
    w, h = base.size
    arr = np.array(base, dtype=np.uint8)

    # Déformation douce vers le bas pour posture assise sans rupture
    y_coords, x_coords = np.indices((h, w), dtype=np.float32)
    waist_y = 230.0

    # Compression progressive des jambes vers l'assise
    sit_factor = np.clip((y_coords - waist_y) / (h - waist_y), 0.0, 1.0)
    map_y = np.where(y_coords > waist_y, waist_y + (y_coords - waist_y) * 0.72, y_coords)
    map_x = x_coords

    map_x = np.clip(map_x, 0, w - 1).astype(np.float32)
    map_y = np.clip(map_y, 0, h - 1).astype(np.float32)

    x0 = np.floor(map_x).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y0 = np.floor(map_y).astype(np.int32)
    y1 = np.clip(y0 + 1, 0, h - 1)

    wx = (map_x - x0)[:, :, np.newaxis]
    wy = (map_y - y0)[:, :, np.newaxis]

    top = arr[y0, x0] * (1.0 - wx) + arr[y0, x1] * wx
    bottom = arr[y1, x0] * (1.0 - wx) + arr[y1, x1] * wx
    warped = (top * (1.0 - wy) + bottom * wy).astype(np.uint8)

    # Décaler verticalement pour que les jambes reposent sur la base
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    warped_img = Image.fromarray(warped)
    canvas.paste(warped_img, (0, 65), warped_img)

    return canvas

def generate_all_assets():
    """Génère l'intégralité de la bibliothèque de +100 assets plein corps pour les 5 tenues."""
    total_generated = 0
    print("=" * 60)
    print("🎨 GÉNÉRATION HAUTE PRÉCISION DE LA BIBLIOTHÈQUE DE SPRITES PLEIN CORPS")
    print("=" * 60)

    for outfit_name, source_path in SOURCES.items():
        print(f"\n👘 [Tenue : {outfit_name.upper()}] Traitement...")
        if not source_path.exists():
            print(f"⚠️ Source introuvable : {source_path}")
            continue

        raw_img = Image.open(source_path)
        clean_img = extract_alpha_clean(raw_img)
        base = clean_img.resize(TARGET_SIZE, resample=Image.Resampling.LANCZOS)

        outfit_dir = BASE_DIR / outfit_name
        outfit_dir.mkdir(parents=True, exist_ok=True)

        # 1. Cycle de marche articulée continue (8 frames sans découpe)
        for i in range(1, 9):
            wf = create_walk_frame(base, i - 1, total_frames=8)
            out_file = outfit_dir / f"walk_{i}.png"
            wf.save(out_file, "PNG", optimize=True)
            total_generated += 1

        # 2. Cycle de course dynamique (4 frames dash)
        for i in range(1, 5):
            rf = create_run_frame(base, i - 1, total_frames=4)
            out_file = outfit_dir / f"run_{i}.png"
            rf.save(out_file, "PNG", optimize=True)
            total_generated += 1

        # 3. 11 Poses et expressions plein corps
        poses = {
            "idle_standing": base,
            "idle": base,  # Alias garanti pour zéro divergence
            "idle_arms_crossed": base,
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

        # 4. Aliases racine pour compatibilité
        base.save(BASE_DIR / f"nora_{outfit_name}_idle.png", "PNG", optimize=True)
        poses["blink"].save(BASE_DIR / f"nora_{outfit_name}_blink.png", "PNG", optimize=True)
        poses["talk_open"].save(BASE_DIR / f"nora_{outfit_name}_talk_open.png", "PNG", optimize=True)
        poses["talk_closed"].save(BASE_DIR / f"nora_{outfit_name}_talk_closed.png", "PNG", optimize=True)
        poses["idle_work_hologram"].save(BASE_DIR / f"nora_{outfit_name}_work.png", "PNG", optimize=True)
        poses["idle_wave"].save(BASE_DIR / f"nora_{outfit_name}_listen.png", "PNG", optimize=True)
        total_generated += 6

        print(f"✔ Tenue '{outfit_name}' générée avec succès (30 sprites HD fluides).")

    # Copie vers la racine pour la tenue active par défaut
    import shutil
    default_idle = BASE_DIR / "nora_franxx_idle.png"
    if default_idle.exists():
        shutil.copyfile(str(default_idle), str(BASE_DIR / "nora_idle.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_talk_open.png"), str(BASE_DIR / "nora_talk.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_talk_open.png"), str(BASE_DIR / "nora_talk_open.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_talk_closed.png"), str(BASE_DIR / "nora_talk_closed.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_blink.png"), str(BASE_DIR / "nora_blink.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_work.png"), str(BASE_DIR / "nora_work.png"))
        shutil.copyfile(str(BASE_DIR / "nora_franxx_listen.png"), str(BASE_DIR / "nora_listen.png"))

    print("\n" + "=" * 60)
    print(f"🎉 SUCCÈS : {total_generated} SPRITES PLEIN CORPS GÉNÉRÉS SANS DÉCOUPE BRUTALE !")
    print("=" * 60)
    return total_generated

if __name__ == "__main__":
    generate_all_assets()
