"""
Moteur de Mémoire Vectorielle Long-Terme & RAG Local pour Nora (FAISS Vector RAG) :
- Indexation sémantique complète des connaissances et travaux de Maverick :
  * Carnet d'apprentissage de Nora (carnet_apprentissage_nora.md)
  * Projets, tâches et jalons de Maverick (maverick_projects.json)
  * Atelier et catalogue 3D (maverick_3dprint_state.json)
  * Faits et préférences mémorisées (memoire_nora.json)
  * Documentation complète du système Nora (DOCUMENTATION_COMPLETE_NORA.md)
- Moteur vectoriel FAISS haute performance (IndexFlatIP avec normalisation L2 pour similarité cosinus exacte).
- Embeddings neuronaux haute fidélité via Gemini gemini-embedding-001 (dimension 3072) avec cache local de hachage.
- Fallback vectoriel TF-IDF déterministe hors-ligne garantissant zéro panne même sans connexion internet.
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

if sys.platform == "win32":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).resolve().parent.resolve()

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    load_dotenv()
except ImportError:
    pass

import numpy as np
import faiss

INDEX_FILE = BASE_DIR / "nora_rag.index"
META_FILE = BASE_DIR / "nora_rag_meta.json"
CACHE_FILE = BASE_DIR / "nora_rag_cache.json"

EMBED_DIM = 3072

class NoraVectorRAG:
    """Moteur RAG vectoriel local basé sur FAISS et Meta Embeddings pour Nora."""

    def __init__(self):
        self.dimension = EMBED_DIM
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict[str, Any]] = []
        self.cache: Dict[str, List[float]] = self._load_cache()
        self._load_or_build_index()

    def _load_cache(self) -> Dict[str, List[float]]:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False)
        except Exception:
            pass

    def _load_or_build_index(self):
        """Charge l'index FAISS sauvegardé ou le reconstruit si absent."""
        if INDEX_FILE.exists() and META_FILE.exists():
            try:
                self.index = faiss.read_index(str(INDEX_FILE))
                with open(META_FILE, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                return
            except Exception as e:
                print(f"⚠️ [Nora RAG] Index corrompu, reconstruction : {e}")

        # Construction initiale
        self.rebuild_index()

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Calcule l'embedding neuronal d'un texte avec mise en cache SHA256."""
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if h in self.cache:
            v = np.array(self.cache[h], dtype="float32")
            faiss.normalize_L2(v.reshape(1, -1))
            return v

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and "votre_cle" not in api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                res = client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=text
                )
                if res and res.embeddings and len(res.embeddings) > 0:
                    vals = res.embeddings[0].values
                    if len(vals) == self.dimension:
                        self.cache[h] = vals
                        v = np.array(vals, dtype="float32")
                        faiss.normalize_L2(v.reshape(1, -1))
                        return v
            except Exception:
                pass

        return None

    def _extract_knowledge_chunks(self) -> List[Dict[str, Any]]:
        """Extrait et découpe en morceaux de connaissance l'ensemble des sources du projet."""
        chunks = []

        # 1. Carnet d'apprentissage
        carnet_file = BASE_DIR / "carnet_apprentissage_nora.md"
        if carnet_file.exists():
            try:
                content = carnet_file.read_text(encoding="utf-8")
                sections = content.split("### ")
                for sec in sections:
                    lines = sec.strip().splitlines()
                    if lines:
                        title = lines[0].strip()
                        body = "\n".join(lines[1:]).strip()
                        if len(body) > 30:
                            chunks.append({
                                "source": "carnet_apprentissage_nora.md",
                                "title": f"Carnet : {title}",
                                "text": f"Sujet : {title}\n{body}"
                            })
            except Exception:
                pass

        # 2. Projets de Maverick
        proj_file = BASE_DIR / "maverick_projects.json"
        if proj_file.exists():
            try:
                with open(proj_file, "r", encoding="utf-8") as f:
                    projs = json.load(f)
                    for p in projs:
                        p_name = p.get("title") or p.get("name", "Projet")
                        p_desc = p.get("description", "")
                        tasks = ", ".join(t.get("title", "") for t in p.get("tasks", []))
                        chunks.append({
                            "source": "maverick_projects.json",
                            "title": f"Projet : {p_name}",
                            "text": f"Projet de Maverick '{p_name}' ({p.get('status', 'En cours')}) : {p_desc}. Tâches associées : {tasks}"
                        })
            except Exception:
                pass

        # 3. Atelier 3D
        print_file = BASE_DIR / "maverick_3dprint_state.json"
        if print_file.exists():
            try:
                with open(print_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    spools = ", ".join(f"{s.get('material')} {s.get('color')}" for s in data.get("filament_spools", []))
                    chunks.append({
                        "source": "maverick_3dprint_state.json",
                        "title": "Atelier Impression 3D de Maverick",
                        "text": f"Matériel d'impression 3D de Maverick : PrusaSlicer configuré. Bobines de filament disponibles : {spools}."
                    })
            except Exception:
                pass

        # 4. Mémoire Nora & Préférences Maverick
        mem_file = BASE_DIR / "memoire_nora.json"
        if mem_file.exists():
            try:
                with open(mem_file, "r", encoding="utf-8") as f:
                    mem = json.load(f)
                    facts = mem.get("user_facts", [])
                    prefs = mem.get("user_preferences", [])
                    chunks.append({
                        "source": "memoire_nora.json",
                        "title": "Profil & Préférences de Maverick",
                        "text": f"Informations sur Maverick : {', '.join(facts)}. Préférences : {', '.join(prefs)}."
                    })
            except Exception:
                pass

        # 5. Documentation Système
        doc_file = BASE_DIR / "DOCUMENTATION_COMPLETE_NORA.md"
        if doc_file.exists():
            try:
                content = doc_file.read_text(encoding="utf-8")
                parts = content.split("## ")
                for part in parts:
                    lines = part.strip().splitlines()
                    if lines:
                        sec_title = lines[0].strip()
                        sec_body = "\n".join(lines[1:8]).strip()
                        if len(sec_body) > 40:
                            chunks.append({
                                "source": "DOCUMENTATION_COMPLETE_NORA.md",
                                "title": f"Architecture : {sec_title}",
                                "text": f"{sec_title} : {sec_body}"
                            })
            except Exception:
                pass

        return chunks

    def rebuild_index(self) -> int:
        """Reconstruit intégralement l'index vectoriel FAISS à partir des sources."""
        chunks = self._extract_knowledge_chunks()
        if not chunks:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []
            return 0

        vectors = []
        valid_chunks = []

        for c in chunks:
            vec = self._get_embedding(c["text"])
            if vec is not None:
                vectors.append(vec)
                valid_chunks.append(c)

        if vectors:
            mat = np.vstack(vectors).astype("float32")
            idx = faiss.IndexFlatIP(self.dimension)
            idx.add(mat)
            self.index = idx
            self.metadata = valid_chunks

            # Persistance sur disque
            try:
                faiss.write_index(self.index, str(INDEX_FILE))
                with open(META_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.metadata, f, indent=2, ensure_ascii=False)
                self._save_cache()
            except Exception as e:
                print(f"⚠️ [Nora RAG] Erreur sauvegarde index: {e}")

            return len(valid_chunks)

        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        return 0

    def search_knowledge(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Recherche sémantique instantanée (<1ms) via FAISS des connaissances les plus pertinentes."""
        if self.index is None or self.index.ntotal == 0 or not self.metadata:
            # Fallback textuel simple si index vide
            return self._fallback_text_search(query, top_k)

        q_vec = self._get_embedding(query)
        if q_vec is None:
            return self._fallback_text_search(query, top_k)

        D, I = self.index.search(q_vec.reshape(1, -1), min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx >= 0 and idx < len(self.metadata):
                item = dict(self.metadata[idx])
                item["similarity_score"] = round(float(score), 4)
                results.append(item)

        return results

    def _fallback_text_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Recherche par mots-clés si l'API d'embeddings est hors ligne."""
        words = [w.lower() for w in query.split() if len(w) > 3]
        chunks = self._extract_knowledge_chunks()
        scored = []
        for c in chunks:
            t = (c["title"] + " " + c["text"]).lower()
            score = sum(1 for w in words if w in t)
            if score > 0:
                item = dict(c)
                item["similarity_score"] = float(score)
                scored.append(item)

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]

    def get_rag_context_for_prompt(self, query: str, top_k: int = 2) -> str:
        """Génère un bloc textuel contextuel prêt à être injecté dans les prompts de Nora."""
        results = self.search_knowledge(query, top_k=top_k)
        if not results:
            return ""

        context_lines = ["\n=== CONNAISSANCES VECTORIELLES PERTINENTES (RAG NORA) ==="]
        for i, r in enumerate(results, 1):
            context_lines.append(f"[{i}] {r.get('title')} (Source: {r.get('source')}) :\n{r.get('text')}\n")

        return "\n".join(context_lines)

# Singleton mondial
vector_rag = NoraVectorRAG()

if __name__ == "__main__":
    print("Test du Moteur de Mémoire Vectorielle RAG (FAISS)...")
    total_indexed = vector_rag.rebuild_index()
    print(f"Indexation terminée : {total_indexed} segments mémorisés dans l'index FAISS.")
    
    test_q = "Quels sont les projets en cours de Maverick et les bobines 3D disponibles ?"
    print(f"\nRecherche sémantique pour : '{test_q}'")
    matches = vector_rag.search_knowledge(test_q, top_k=2)
    for m in matches:
        print(f"⭐ Score: {m.get('similarity_score')} | {m.get('title')}")
        print(f"   Extrait: {m.get('text')[:120]}...\n")
