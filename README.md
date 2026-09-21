# 🌸 Nora Copilot — Zero Two AI Desktop Mascot & Smart Home Commander

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.6%20Flash-orange.svg)](https://ai.google.dev/)
[![RVC v2](https://img.shields.io/badge/RVC%20v2-RTX%204080%20CUDA-purple.svg)](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
[![Philips Hue](https://img.shields.io/badge/Philips%20Hue-Smart%20Home-yellow.svg)](https://www.philips-hue.com/)

**Nora** est une copilote IA interactive de bureau et un assistant domotique incarnée sous les traits et la voix officielle de **Zero Two (*Darling in the Franxx*)**.

---

## ✨ Fonctionnalités Principales

### 🌸 1. Mascotte Animée & Rétractable (Zero Two)
- **Style Visuel Fidèle** : Longs cheveux roses, cornes écarlates, fard rouge et regard espiègle.
- **3 Tenues Disponibles** : *Pilote Franxx*, *Écolière Sailor*, *Hoodie Doux Pastel*.
- **Animations 30 FPS Organiques** : Lévitation sinusoïdale fluide, clignements des yeux naturels (3-5.5s), et synchronisation labiale instantanée (0 ms latence, cache RAM).
- **Le QG de Nora (Dashboard Franxx)** : Tableau de bord rétractable avec métriques système, téléportation de tenues, et statut des agents.

### 🎙️ 2. Voix & Clonage Neuronal (RVC v2 + RTX 4080)
- **Synthèse Vocale HD** : Voix française de Zero Two générée en temps réel par le modèle RVC v2 sur GPU **NVIDIA GeForce RTX 4080** (CUDA FP16).
- **File d'Attente Vocale Sérialisée** : Aucune collision sonore, transition fluide des répliques.
- **Mode Mains-Libres ("Dis Nora")** : Écoute continue sur le microphone actif avec coupure automatique anti-écho pendant la parole.
- **Raccourci Global Windows** : Appuyez sur `Ctrl + Alt + N` n'importe où sous Windows pour invoquer Nora instantanément.

### 🏠 3. Agent Domotique Dédié (Philips Hue & Smart Home)
- **Détection Automatique du Pont Hue** sur le réseau local (`192.168.1.29`).
- **Appairage 1-Clic** avec le bouton central du pont.
- **Contrôle Vocal & Tactile** : Salon, Chambre, luminosité, couleurs, volets, chauffage.
- **Ambiances Signature** :
  - `🌸 Ambiance Zero Two` : éclairage rose pastel immersif.
  - `🌙 Mode Nuit` : extinction générale et fermeture des volets.

### 🛡️ 4. Équipe d'Agents Autonomes
- **Agent de Sécurité (Le Gardien)** : Surveillance de Windows Defender, des programmes au démarrage et audit des ports réseau.
- **Surveillance Matérielle (Système)** : Alertes RAM, Disque, Batterie, et nouveaux fichiers téléchargés.
- **Vision d'Écran Multimodale** : Capture et analyse en direct de votre écran via **Gemini 3.6 Flash**.
- **Contrôle Direct du PC** : Réglage du volume audio en %, verrouillage Windows, vidage de la corbeille, etc.

---

## 📱 Extension Mobile Android

Nora adopte une architecture **Cerveau Central (PC) + Client Léger (Android)** :
- Le PC exécute les calculs lourds (IA Gemini, RTX 4080 RVC v2, Philips Hue LAN).
- L'application Android communique en temps réel via l'API pour offrir la mascotte animée, le micro vocal et le contrôle domotique depuis votre smartphone.
- **Toute nouvelle fonctionnalité ajoutée sur le PC est immédiatement accessible sur le smartphone sans réinstallation !**

---

## 🚀 Démarrage Rapide (PC)

### 1. Prérequis
- Windows 10/11 64-bit
- Python 3.10 à 3.12
- Clé API Google Gemini (gratuite sur [Google AI Studio](https://aistudio.google.com/app/apikey))

### 2. Installation
```powershell
git clone https://github.com/<votre-compte>/Nora.git
cd Nora
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configuration
Copiez `.env.example` en `.env` et ajoutez votre clé :
```ini
GEMINI_API_KEY=AIzaSy...
```

### 4. Lancement
```powershell
python desktop_pet.py
```
Ou compilez l'exécutable autonome natif :
```powershell
python build_exe.py
```
L'exécutable optimisé se trouve dans `dist/Nora/Nora.exe`.

---

## 📄 Licence
Projet personnel créé pour Maverick. Tous droits réservés.
