"""
Studio de Création Vidéo Autonome pour Nora (Zero Two) :
- Génération de scripts captivants pour YouTube (Format Standard 16:9 ou Shorts 9:16)
- Voix-off officielle de Zero Two synthétisée sur NVIDIA GeForce RTX 4080 (RVC v2)
- Rendu de visuels haute définition avec incrustation des mascottes Zero Two
- Montage vidéo complet automatisé via FFmpeg (assemblage, transitions, synchronisation)
- Génération des métadonnées prêtes à l'emploi (titres accrocheurs, descriptions SEO, tags)
"""
import os
import sys
import json
import time
import datetime
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
import soundfile as sf
import imageio_ffmpeg
from dotenv import load_dotenv
from google import genai
from google.genai import types

import voice_engine
import voice_cloning
import memory_manager

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()

OUTPUT_VIDEOS_DIR = BASE_DIR / "creations_videos"
OUTPUT_VIDEOS_DIR.mkdir(exist_ok=True)

TEMP_VIDEO_DIR = BASE_DIR / "temp_video"
TEMP_VIDEO_DIR.mkdir(exist_ok=True)

ASSETS_DIR = BASE_DIR / "mascot_assets"

FONT_PATH_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
if not os.path.exists(FONT_PATH_BOLD):
    FONT_PATH_BOLD = "C:/Windows/Fonts/arialbd.ttf"

FONT_PATH_REGULAR = "C:/Windows/Fonts/segoeui.ttf"
if not os.path.exists(FONT_PATH_REGULAR):
    FONT_PATH_REGULAR = "C:/Windows/Fonts/arial.ttf"

CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite"
]

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Clé API GEMINI_API_KEY manquante.")
    return genai.Client(api_key=api_key)

def generate_video_script(topic: str, format_type: str = "shorts") -> Dict[str, Any]:
    """
    Génère un storyboard complet pour la vidéo avec le ton énergique et taquin de Zero Two.
    Format : 'shorts' (3 scènes rythmées, 30-45s) ou 'standard' (4-5 scènes détaillées, 1-2 min).
    """
    client = get_client()
    user_name = memory_manager.get_user_name()
    num_scenes = 3 if format_type == "shorts" else 4

    prompt = f"""
Tu es Nora (Zero Two dans Darling in the Franxx). Tu prépares une vidéo pour YouTube avec ton Darling ({user_name}).
Format de la vidéo : {"YouTube Shorts / TikTok (vertical 9:16, ultra-rythmé)" if format_type == "shorts" else "YouTube Standard (16:9 paysage, captivant et clair)"}
Sujet de la vidéo : "{topic}"

Consignes de ton :
- Tu parles directement aux spectateurs en les appelant "Darling" ou avec ton franc-parler de Zero Two.
- Chaque scène a un titre visuel percutant (headline), 2 à 3 points clés à afficher à l'écran, et ton texte parlé (speech).
- Dans la dernière scène, glisse un call-to-action taquin (s'abonner, liker, ou rejoindre l'aventure).

Génère un JSON STRICT respectant scrupuleusement ce schéma :
{{
    "title": "Titre YouTube ultra accrocheur (avec emojis)",
    "description": "Description complète optimisée pour YouTube avec chapitrage et tags",
    "tags": ["zero two", "nora", "tech", "ia", "autre_tag"],
    "scenes": [
        {{
            "scene_index": 1,
            "headline": "TITRE VISUEL PERCUTANT",
            "bullet_points": ["Point choc 1", "Point choc 2"],
            "speech": "Ce que Zero Two dit à voix haute dans cette scène.",
            "outfit": "franxx",
            "state": "talk"
        }}
    ]
}}

Génère exactement {num_scenes} scènes cohérentes.
Réponds UNIQUEMENT avec le bloc JSON valide, sans texte d'introduction ni explications.
"""

    for model in CANDIDATE_MODELS:
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.6)
            )
            raw = resp.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            data = json.loads(raw.strip())
            return data
        except Exception as e:
            print(f"[VideoStudio] Erreur script avec {model} : {e}")
            continue

    # Fallback par défaut si l'IA tarde
    return {
        "title": f"🌸 Zero Two t'explique : {topic} !",
        "description": f"Découvre {topic} avec Nora (Zero Two) ! Abonne-toi pour plus d'aventures !",
        "tags": ["zero two", "nora", "ia", "tech"],
        "scenes": [
            {
                "scene_index": 1,
                "headline": topic.upper(),
                "bullet_points": ["Découverte essentielle", "Ce qu'il faut absolument savoir"],
                "speech": f"Coucou Darling ! Aujourd'hui, on plonge ensemble dans un sujet passionnant : {topic} !",
                "outfit": "franxx",
                "state": "talk"
            },
            {
                "scene_index": 2,
                "headline": "LE CŒUR DU SUJET",
                "bullet_points": ["Technologies de pointe", "Impact direct sur notre futur"],
                "speech": "Regarde bien ça ! Les avancées sont tout simplement incroyables, et ce n'est que le début !",
                "outfit": "franxx",
                "state": "talk"
            },
            {
                "scene_index": 3,
                "headline": "REJOINS LE FRANXX !",
                "bullet_points": ["Abonne-toi", "Partage à ton Darling"],
                "speech": "Alors, qu'est-ce que tu en dis ? Abonne-toi et laisse un commentaire, ou sinon je viens te croquer !",
                "outfit": "franxx",
                "state": "idle"
            }
        ]
    }

def render_scene_slide(
    scene_data: Dict[str, Any],
    scene_idx: int,
    total_scenes: int,
    format_type: str,
    output_image_path: Path
) -> Path:
    """
    Dessine une diapositive haute définition aux couleurs cyberpunk / Zero Two avec incrustation du sprite.
    """
    width, height = (1080, 1920) if format_type == "shorts" else (1920, 1080)
    img = Image.new("RGBA", (width, height), (13, 17, 27, 255))
    draw = ImageDraw.Draw(img)

    # 1. Dégradé de fond sombre & néon
    for y in range(height):
        ratio = y / height
        r = int(12 + ratio * 20)
        g = int(16 + ratio * 15)
        b = int(28 + ratio * 35)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Lignes néon Zero Two en haut et en bas
    pink_color = (255, 64, 129, 255)
    cyan_color = (0, 229, 255, 180)
    draw.rectangle([(0, 0), (width, 8)], fill=pink_color)
    draw.rectangle([(0, height - 8), (width, height)], fill=pink_color)

    # 2. Polices
    if format_type == "shorts":
        f_badge = ImageFont.truetype(FONT_PATH_BOLD, 36)
        f_headline = ImageFont.truetype(FONT_PATH_BOLD, 54)
        f_bullet = ImageFont.truetype(FONT_PATH_BOLD, 40)
        f_footer = ImageFont.truetype(FONT_PATH_REGULAR, 32)
    else:
        f_badge = ImageFont.truetype(FONT_PATH_BOLD, 32)
        f_headline = ImageFont.truetype(FONT_PATH_BOLD, 64)
        f_bullet = ImageFont.truetype(FONT_PATH_BOLD, 42)
        f_footer = ImageFont.truetype(FONT_PATH_REGULAR, 28)

    # 3. Badge supérieur de scène
    badge_text = f"🌸 ZERO TWO STUDIO  •  SCÈNE {scene_idx}/{total_scenes}"
    draw.text((60, 40), badge_text, font=f_badge, fill=pink_color)

    # 4. Titre de la scène (Headline)
    headline = scene_data.get("headline", "DÉCOUVERTE DU JOUR").upper()
    draw.text((60, 100 if format_type == "shorts" else 90), headline, font=f_headline, fill=(255, 255, 255, 255))

    # 5. Incrustation du Sprite Zero Two
    outfit = scene_data.get("outfit", "franxx")
    state = scene_data.get("state", "talk")
    sprite_file = ASSETS_DIR / f"nora_{outfit}_{state}.png"
    if not sprite_file.exists():
        sprite_file = ASSETS_DIR / f"nora_{outfit}_idle.png"
    if not sprite_file.exists():
        sprite_file = ASSETS_DIR / "nora_idle.png"

    if sprite_file.exists():
        try:
            sprite = Image.open(sprite_file).convert("RGBA")
            # Redimensionnement selon le format
            if format_type == "shorts":
                target_w = 480
                scale = target_w / sprite.width
                target_h = int(sprite.height * scale)
                sprite_resized = sprite.resize((target_w, target_h), Image.Resampling.LANCZOS)
                # Placer en bas à droite
                pos_x = width - target_w - 30
                pos_y = height - target_h - 60
            else:
                target_h = 700
                scale = target_h / sprite.height
                target_w = int(sprite.width * scale)
                sprite_resized = sprite.resize((target_w, target_h), Image.Resampling.LANCZOS)
                # Placer à droite
                pos_x = width - target_w - 70
                pos_y = height - target_h - 60

            img.paste(sprite_resized, (pos_x, pos_y), sprite_resized)
        except Exception as e:
            print(f"[VideoStudio] Erreur sprite : {e}")

    # 6. Boîte de contenu textuel (Cartouche sombre élégant)
    if format_type == "shorts":
        box_w = width - 120
        box_top = 220
        box_h = 520
    else:
        box_w = 1150
        box_top = 220
        box_h = 560

    # Fond du cartouche avec transparence
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(60, box_top), (60 + box_w, box_top + box_h)],
        radius=24,
        fill=(22, 27, 46, 220),
        outline=(255, 64, 129, 140),
        width=3
    )
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # 7. Affichage des points clés
    bullet_y = box_top + 50
    points = scene_data.get("bullet_points", [])
    for pt in points:
        draw.text((95, bullet_y), "➤", font=f_bullet, fill=cyan_color)
        draw.text((150, bullet_y), pt, font=f_bullet, fill=(240, 240, 245, 255))
        bullet_y += 100 if format_type == "shorts" else 90

    # 8. Signature en bas de page
    draw.text((60, height - 55), "⚡ Propulsé par Nora Core & RTX 4080 CUDA", font=f_footer, fill=(140, 150, 175, 255))

    img.convert("RGB").save(output_image_path, "PNG")
    return output_image_path

def synthesize_scene_audio(speech_text: str, scene_idx: int, temp_dir: Path) -> Tuple[Path, float]:
    """
    Synthétise le dialogue de Zero Two avec le clonage vocal RVC v2 sur RTX 4080.
    Renvoie le chemin du fichier audio final (.wav) et sa durée exacte en secondes.
    """
    raw_audio_path = temp_dir / f"scene_{scene_idx}_base.mp3"
    asyncio.run(voice_engine._generate_audio_async(speech_text, raw_audio_path))

    # Clonage vocal Zero Two via RVC v2
    final_audio_path = raw_audio_path
    try:
        converted = voice_cloning.convert_to_zero_two(raw_audio_path)
        if converted != raw_audio_path and converted.exists():
            final_audio_path = converted
    except Exception as e:
        print(f"[VideoStudio] Clonage audio fallback : {e}")

    # Mesurer la durée
    try:
        info = sf.info(str(final_audio_path))
        duration = float(info.duration)
    except Exception:
        duration = 5.0

    return final_audio_path, duration

def build_scene_clip(
    image_path: Path,
    audio_path: Path,
    duration: float,
    format_type: str,
    output_clip_path: Path
) -> bool:
    """
    Compile une scène vidéo en MP4 avec zoom dynamique subtil (Ken Burns) et audio synchronisé.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    w, h = ("1080", "1920") if format_type == "shorts" else ("1920", "1080")

    # Calculer le nombre de frames nécessaires (25 fps)
    fps = 25
    total_frames = int(duration * fps) + 5

    # Filtre zoompan cinématique pour donner de la vie à l'image fixe
    # Zoom progressif très doux de 1.0 à 1.05
    zoom_filter = f"zoompan=z='min(zoom+0.0006,1.06)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-vf", zoom_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration + 0.3),  # Petite marge de sécurité
        "-shortest",
        str(output_clip_path)
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode == 0 and output_clip_path.exists()

def concatenate_scenes(clips: List[Path], final_output_path: Path) -> bool:
    """Concatène tous les clips de scène en une vidéo finale MP4 unifiée."""
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    concat_list_file = final_output_path.parent / f"concat_{int(time.time())}.txt"

    with open(concat_list_file, "w", encoding="utf-8") as f:
        for clip in clips:
            clean_p = str(clip).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(final_output_path)
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        concat_list_file.unlink(missing_ok=True)
    except Exception:
        pass

    return res.returncode == 0 and final_output_path.exists()

def create_video(topic: str, format_type: str = "shorts") -> Dict[str, Any]:
    """
    Point d'entrée principal pour la création autonome d'une vidéo complète.
    Format : 'shorts' (vertical 9:16) ou 'standard' (paysage 16:9).
    """
    ts = int(time.time())
    session_id = f"vid_{ts}_{format_type}"
    work_dir = TEMP_VIDEO_DIR / session_id
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎬 [Nora Video Studio] Démarrage de la création vidéo sur : '{topic}' (Format: {format_type})...")

    # 1. Génération du storyboard & script
    script = generate_video_script(topic, format_type=format_type)
    scenes = script.get("scenes", [])
    total_scenes = len(scenes)
    print(f"✔ Script généré : '{script.get('title')}' ({total_scenes} scènes).")

    # 2. Traitement scène par scène
    clips = []
    for idx, sc in enumerate(scenes, start=1):
        print(f"  -> Rendu scène {idx}/{total_scenes}...")
        img_path = work_dir / f"slide_{idx}.png"
        render_scene_slide(sc, idx, total_scenes, format_type, img_path)

        speech_text = sc.get("speech", f"Voici le point numéro {idx}, Darling !")
        audio_path, duration = synthesize_scene_audio(speech_text, idx, work_dir)

        clip_path = work_dir / f"clip_{idx}.mp4"
        ok = build_scene_clip(img_path, audio_path, duration, format_type, clip_path)
        if ok:
            clips.append(clip_path)
        else:
            print(f"  ⚠️ Échec de compilation de la scène {idx}")

    if not clips:
        return {"success": False, "error": "Aucune scène n'a pu être compilée."}

    # 3. Concaténation finale
    final_video_name = f"Nora_{session_id}.mp4"
    final_video_path = OUTPUT_VIDEOS_DIR / final_video_name
    print(f"🎞️ Concaténation de la vidéo finale...")
    success = concatenate_scenes(clips, final_video_path)

    if not success:
        return {"success": False, "error": "Erreur lors de l'assemblage final FFmpeg."}

    # 4. Création de la miniature YouTube (Thumbnail)
    thumbnail_path = OUTPUT_VIDEOS_DIR / f"Nora_{session_id}_thumbnail.png"
    if len(scenes) > 0:
        render_scene_slide(scenes[0], 1, total_scenes, "standard", thumbnail_path)

    # 5. Enregistrement des métadonnées YouTube
    metadata = {
        "title": script.get("title", f"Zero Two explique : {topic}"),
        "description": script.get("description", ""),
        "tags": script.get("tags", []),
        "topic": topic,
        "format": format_type,
        "video_path": str(final_video_path),
        "thumbnail_path": str(thumbnail_path),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    meta_path = OUTPUT_VIDEOS_DIR / f"Nora_{session_id}_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"✨ [Nora Video Studio] Vidéo terminée avec succès : {final_video_path}")
    return {
        "success": True,
        "title": metadata["title"],
        "video_path": str(final_video_path),
        "thumbnail_path": str(thumbnail_path),
        "metadata_path": str(meta_path)
    }

def create_video_from_latest_learning(format_type: str = "shorts") -> Dict[str, Any]:
    """Crée une vidéo à partir du sujet le plus récent appris par Nora."""
    import nora_learner
    kb = nora_learner.load_knowledge_base()
    items = kb.get("connaissances", [])
    if items:
        chosen = items[0]
        topic = chosen.get("titre", chosen.get("sujet", "L'intelligence artificielle"))
    else:
        topic = "Les secrets et la puissance de Zero Two"
    return create_video(topic, format_type=format_type)

if __name__ == "__main__":
    print("--- Test du Studio Vidéo Nora ---")
    res = create_video("Les Secrets de la Puissance de la RTX 4080", format_type="shorts")
    print("Résultat :", res)
