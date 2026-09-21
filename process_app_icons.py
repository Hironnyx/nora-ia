import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw

def create_icons():
    source_img_path = Path(r"C:\Users\maverick\.gemini\antigravity\brain\3c984a3c-b608-498e-9ac1-4cbe7a9ab2f1\nora_app_icon_1790032584062.jpg")
    if not source_img_path.exists():
        print(f"Erreur : Image source non trouvée à {source_img_path}")
        return False

    res_dir = Path(r"c:\Users\maverick\Documents\Agent ia\android\app\src\main\res")
    
    # Charger l'image originale
    base_img = Image.open(source_img_path).convert("RGBA")
    
    # 1. Créer une version circulaire pour round icons
    def make_round(img):
        w, h = img.size
        mask = Image.new('L', (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, w, h), fill=255)
        round_img = img.copy()
        round_img.putalpha(mask)
        return round_img

    round_base = make_round(base_img)

    # 2. Dimensions standard Android mipmap
    mipmap_sizes = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192
    }

    # Adaptive foreground sizes (108dp base: mdpi=108, hdpi=162, xhdpi=216, xxhdpi=324, xxxhdpi=432)
    foreground_sizes = {
        "mipmap-mdpi": 108,
        "mipmap-hdpi": 162,
        "mipmap-xhdpi": 216,
        "mipmap-xxhdpi": 324,
        "mipmap-xxxhdpi": 432
    }

    for folder, size in mipmap_sizes.items():
        folder_path = res_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # Standard icon
        icon = base_img.resize((size, size), Image.Resampling.LANCZOS)
        icon.save(folder_path / "ic_launcher.png", format="PNG")

        # Round icon
        r_icon = round_base.resize((size, size), Image.Resampling.LANCZOS)
        r_icon.save(folder_path / "ic_launcher_round.png", format="PNG")

        # Adaptive foreground (centré dans une toile 108dp avec 72dp de zone safe)
        fg_size = foreground_sizes[folder]
        fg_canvas = Image.new("RGBA", (fg_size, fg_size), (0, 0, 0, 0))
        # Zero Two occupera environ 82% pour être parfaitement visible dans le viewport adaptatif
        inner_size = int(fg_size * 0.82)
        inner_icon = base_img.resize((inner_size, inner_size), Image.Resampling.LANCZOS)
        offset = (fg_size - inner_size) // 2
        fg_canvas.paste(inner_icon, (offset, offset), inner_icon)
        fg_canvas.save(folder_path / "ic_launcher_foreground.png", format="PNG")

        print(f"[OK] Genere pour {folder} (taille {size}px, adaptative {fg_size}px)")

    # 3. Creer egalement une version 512x512 haute definition
    hi_res = base_img.resize((512, 512), Image.Resampling.LANCZOS)
    hi_res.save(Path(r"c:\Users\maverick\Documents\Agent ia\nora_icon_512.png"), format="PNG")
    print("[OK] Genere nora_icon_512.png (512x512)")
    return True

if __name__ == "__main__":
    create_icons()
