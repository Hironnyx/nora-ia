"""
Module d'outils pour l'interaction avec le PC Windows, l'organisation de fichiers et la manipulation directe.
"""
import os
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from pypdf import PdfReader

CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".odt", ".csv", ".rtf"],
    "Installateurs_et_Logiciels": [".exe", ".msi", ".iso", ".bat", ".cmd"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Audio_et_Musique": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv"],
    "Code_et_Scripts": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".cpp", ".c", ".cs", ".php", ".sh", ".ps1"]
}

def resolve_user_path(path_str: str) -> Path:
    """Résout les chemins relatifs, variables d'environnement ou alias courants."""
    lower = path_str.lower().strip()
    home = Path.home()
    if lower in ["téléchargements", "downloads", "telechargements"]:
        return home / "Downloads"
    elif lower in ["bureau", "desktop"]:
        return home / "Desktop"
    elif lower in ["documents", "mes documents"]:
        return home / "Documents"
    elif lower in ["images", "pictures"]:
        return home / "Pictures"
    elif lower in ["musique", "music"]:
        return home / "Music"
    elif lower in ["vidéos", "videos"]:
        return home / "Videos"
    
    # Gérer les chemins de type 'Bureau/Dossier' ou 'Downloads/Dossier'
    parts = Path(path_str).parts
    if parts:
        first = parts[0].lower()
        if first in ["bureau", "desktop"]:
            return home / "Desktop" / Path(*parts[1:])
        elif first in ["téléchargements", "downloads", "telechargements"]:
            return home / "Downloads" / Path(*parts[1:])
        elif first in ["documents", "mes documents"]:
            return home / "Documents" / Path(*parts[1:])

    return Path(os.path.expandvars(path_str)).resolve()

def create_folder(folder_path: str) -> str:
    """Crée un dossier sur le disque (ex: sur le Bureau, dans Documents, etc.)."""
    try:
        p = resolve_user_path(folder_path)
        p.mkdir(parents=True, exist_ok=True)
        return f"Dossier créé avec succès : {p}"
    except Exception as e:
        return f"Erreur lors de la création du dossier '{folder_path}' : {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Écrit ou crée un fichier texte (rapport, résumé, note, script) à l'emplacement spécifié."""
    try:
        p = resolve_user_path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Fichier créé avec succès : {p} ({len(content)} caractères)"
    except Exception as e:
        return f"Erreur lors de l'écriture du fichier '{filepath}' : {str(e)}"

def copy_file(source: str, destination: str) -> str:
    """Copie un fichier d'un emplacement vers un autre."""
    try:
        src = resolve_user_path(source)
        dst = resolve_user_path(destination)
        if not src.exists():
            return f"Fichier source introuvable : {src}"
        if dst.is_dir() or (not dst.suffix and not dst.exists()):
            dst.mkdir(parents=True, exist_ok=True)
            dst = dst / src.name
        shutil.copy2(str(src), str(dst))
        return f"Fichier copié de {src.name} vers {dst}"
    except Exception as e:
        return f"Erreur lors de la copie du fichier : {str(e)}"

def calculate_file_hash(filepath: Path, chunk_size: int = 65536) -> str:
    """Calcule le hachage SHA-256 d'un fichier de manière efficace par morceaux."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""

def find_duplicates(folder_path: str, move_to_folder: bool = True) -> str:
    """
    Scanne un dossier pour trouver les fichiers en double (contenu 100% identique).
    Si move_to_folder est True, déplace en toute sécurité les doublons vers un sous-dossier 'Doublons/'.
    """
    folder = resolve_user_path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return f"Erreur : Le dossier '{folder}' n'existe pas."

    hashes = {}
    duplicates = []
    total_freed_bytes = 0

    duplicates_dir = folder / "Doublons"
    if move_to_folder:
        duplicates_dir.mkdir(exist_ok=True)

    for item in folder.rglob("*"):
        if not item.is_file() or "Doublons" in item.parts or item.name.startswith("."):
            continue

        file_size = item.stat().st_size
        if file_size == 0:
            continue

        file_hash = calculate_file_hash(item)
        if not file_hash:
            continue

        if file_hash in hashes:
            original = hashes[file_hash]
            total_freed_bytes += file_size
            duplicates.append((item, original))

            if move_to_folder:
                dest = duplicates_dir / item.name
                if dest.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest = duplicates_dir / f"{item.stem}_{timestamp}{item.suffix}"
                try:
                    shutil.move(str(item), str(dest))
                except Exception as e:
                    pass
        else:
            hashes[file_hash] = item

    if not duplicates:
        return f"Aucun fichier en double détecté dans '{folder}'. Vos fichiers sont uniques !"

    mb_saved = total_freed_bytes / (1024 * 1024)
    action_text = f"déplacés dans '{duplicates_dir.name}/'" if move_to_folder else "détectés"
    
    report = [
        f"=== Détection de Doublons terminée pour : {folder} ===",
        f"Nombre de doublons : {len(duplicates)} {action_text}",
        f"Espace disque potentiel récupéré : {mb_saved:.2f} Mo",
        "\nDétail des doublons traités :"
    ]
    for dup, orig in duplicates:
        report.append(f" - Doublon : {dup.name} (identique à : {orig.name})")

    return "\n".join(report)

def extract_text_preview(filepath: Path, max_chars: int = 1200) -> str:
    """Extrait un aperçu textuel d'un document (PDF, TXT, etc.)."""
    ext = filepath.suffix.lower()
    try:
        if ext == ".pdf":
            reader = PdfReader(str(filepath))
            text = ""
            for page in reader.pages[:3]:
                text += (page.extract_text() or "") + "\n"
                if len(text) > max_chars:
                    break
            return text[:max_chars].strip()
        elif ext in [".txt", ".csv", ".json", ".md", ".log"]:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(max_chars).strip()
    except Exception:
        pass
    return ""

def smart_organize_and_rename(folder_path: str) -> str:
    """
    Analyse le contenu réel des documents (factures, attestations, cours, contrats)
    dans un dossier, et les renomme de manière claire et explicite avant de les classer.
    """
    folder = resolve_user_path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return f"Erreur : Le dossier '{folder}' n'existe pas."

    renamed_files = []
    skipped = 0

    for item in folder.iterdir():
        if item.is_dir() or item.name.startswith("."):
            continue

        ext = item.suffix.lower()
        if ext not in [".pdf", ".docx", ".doc", ".txt", ".csv"]:
            continue

        preview = extract_text_preview(item)
        if not preview:
            continue

        preview_lower = preview.lower()
        new_name = None
        category = "Documents_Generaux"

        if any(w in preview_lower for w in ["facture", "invoice", "montant ttc", "tva", "total à payer"]):
            category = "Factures"
            if "edf" in preview_lower or "électricité" in preview_lower:
                new_name = f"Facture_EDF_{datetime.now().strftime('%Y_%m')}{ext}"
            elif "orange" in preview_lower or "sfr" in preview_lower or "bouygues" in preview_lower or "free" in preview_lower:
                new_name = f"Facture_Telecom_{datetime.now().strftime('%Y_%m')}{ext}"
            elif "amazon" in preview_lower:
                new_name = f"Facture_Amazon_{datetime.now().strftime('%Y_%m')}{ext}"
            else:
                new_name = f"Facture_{item.stem}{ext}"

        elif any(w in preview_lower for w in ["impôt", "impots", "avis d'imposition", "revenus", "fiscal"]):
            category = "Impots_et_Fiscalite"
            new_name = f"Document_Fiscal_{item.stem}{ext}"

        elif any(w in preview_lower for w in ["bulletin de salaire", "bulletin de paie", "salaire net"]):
            category = "Fiches_de_Paie"
            new_name = f"Fiche_de_Paie_{datetime.now().strftime('%Y_%m')}{ext}"

        elif any(w in preview_lower for w in ["contrat", "convention", "accord"]):
            category = "Contrats"
            new_name = f"Contrat_{item.stem}{ext}"

        elif any(w in preview_lower for w in ["cours", "université", "exercice", "chapitre", "leçon"]):
            category = "Cours_et_Formation"
            new_name = f"Cours_{item.stem}{ext}"

        if new_name and new_name != item.name:
            target_dir = folder / category
            target_dir.mkdir(exist_ok=True)
            target_file = target_dir / new_name
            if target_file.exists():
                target_file = target_dir / f"{Path(new_name).stem}_{datetime.now().strftime('%H%M%S')}{ext}"

            try:
                shutil.move(str(item), str(target_file))
                renamed_files.append(f" - {item.name} -> {category}/{target_file.name}")
            except Exception as e:
                skipped += 1

    if not renamed_files:
        return f"Aucun document avec contenu spécifique détecté pour un renommage contextuel dans '{folder}'."

    report = [
        f"=== Tri & Renommage Intelligent terminé pour : {folder} ===",
        f"Fichiers renommés et classés : {len(renamed_files)}",
        "\nDétail :",
        "\n".join(renamed_files)
    ]
    return "\n".join(report)

def reorganize_folder(target_path: str) -> str:
    """
    Réorganise un dossier sur le PC (par exemple 'Downloads', 'Desktop' ou un chemin précis).
    Regroupe intelligemment les fichiers dans des sous-dossiers thématiques (Images, Documents, etc.).
    """
    folder = resolve_user_path(target_path)
    if not folder.exists() or not folder.is_dir():
        return f"Erreur : Le dossier '{folder}' n'existe pas ou n'est pas un répertoire."

    moves = []
    skipped = 0

    for item in folder.iterdir():
        if item.is_dir() or item.name.startswith("."):
            continue

        ext = item.suffix.lower()
        destination_category = "Autres"

        for category, extensions in CATEGORIES.items():
            if ext in extensions:
                destination_category = category
                break

        dest_dir = folder / destination_category
        dest_dir.mkdir(exist_ok=True)

        target_file = dest_dir / item.name
        if target_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_file = dest_dir / f"{item.stem}_{timestamp}{item.suffix}"

        try:
            shutil.move(str(item), str(target_file))
            moves.append(f"- {item.name} -> {destination_category}/")
        except Exception as e:
            skipped += 1
            moves.append(f"- [ÉCHEC] {item.name} : {str(e)}")

    if not moves:
        return f"Le dossier '{folder}' ne contenait aucun fichier libre à réorganiser."

    report = [
        f"=== Réorganisation terminée pour : {folder} ===",
        f"Nombre de fichiers traités : {len(moves) - skipped}",
        f"Fichiers ignorés ou échoués : {skipped}",
        "Détail des déplacements :",
        "\n".join(moves)
    ]
    return "\n".join(report)

def run_powershell(command: str) -> str:
    """Exécute une commande PowerShell de manière sécurisée et retourne le résultat."""
    dangerous_keywords = [
        "format-volume", "format c:", "remove-item -recurse c:\\windows",
        "rmdir /s /q c:\\", "bcdedit", "diskpart"
    ]
    command_lower = command.lower()
    if any(kw in command_lower for kw in dangerous_keywords):
        return "SÉCURITÉ : Commande jugée dangereuse et bloquée automatiquement."

    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        if proc.returncode != 0:
            return f"Code retour {proc.returncode} :\n{stderr}"
        return stdout if stdout else "Commande exécutée avec succès (aucune sortie console)."
    except subprocess.TimeoutExpired:
        return "Erreur : La commande a dépassé le délai maximum d'attente (45s)."
    except Exception as e:
        return f"Erreur d'exécution PowerShell : {str(e)}"

def list_directory(path: str = ".") -> str:
    """Liste le contenu d'un dossier avec types et tailles."""
    p = resolve_user_path(path)
    if not p.exists():
        return f"Le chemin '{p}' n'existe pas."
    
    lines = [f"Contenu de {p} :"]
    try:
        for item in p.iterdir():
            if item.is_dir():
                lines.append(f"📁 [DOSSIER] {item.name}")
            else:
                size_kb = item.stat().st_size / 1024
                lines.append(f"📄 [FICHIER] {item.name} ({size_kb:.1f} Ko)")
        return "\n".join(lines) if len(lines) > 1 else f"Le dossier {p} est vide."
    except Exception as e:
        return f"Erreur lors de la lecture du dossier : {str(e)}"

def search_files(pattern: str, search_path: str = ".") -> str:
    """Recherche des fichiers correspondant à un motif (ex: '*.pdf' ou 'facture*')."""
    base_dir = resolve_user_path(search_path)
    if not base_dir.exists():
        return f"Le dossier de recherche '{base_dir}' n'existe pas."

    matches = []
    try:
        for match in base_dir.rglob(pattern):
            if match.is_file():
                matches.append(str(match))
                if len(matches) >= 30:
                    matches.append("... (résultats tronqués à 30 fichiers)")
                    break
        if not matches:
            return f"Aucun fichier trouvé correspondant à '{pattern}' dans {base_dir}."
        return "\n".join(matches)
    except Exception as e:
        return f"Erreur lors de la recherche de fichiers : {str(e)}"

def get_system_overview() -> str:
    """Fournit des informations système de base sur le PC (disques, répertoires utilisateur)."""
    home = Path.home()
    total, used, free = shutil.disk_usage(home)
    gb = 1024 ** 3
    return (
        f"Système utilisateur : {os.getlogin()}\n"
        f"Répertoire personnel : {home}\n"
        f"Espace disque (Lecteur principal) : "
        f"Libre : {free / gb:.2f} Go / Total : {total / gb:.2f} Go (Utilisé : {used / gb:.2f} Go)\n"
        f"Dossiers usuels : Téléchargements={home / 'Downloads'}, Bureau={home / 'Desktop'}, Documents={home / 'Documents'}"
    )
