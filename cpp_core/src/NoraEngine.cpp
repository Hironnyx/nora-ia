#include "NoraEngine.hpp"
#include "SpriteManager.hpp"
#include "LayeredRenderer.hpp"
#include "NativeHotkeys.hpp"
#include "NeuralBridge.hpp"
#include <iostream>
#include <cmath>

namespace Nora {

NoraEngine& NoraEngine::Instance() {
    static NoraEngine instance;
    return instance;
}

NoraEngine::NoraEngine() {}

NoraEngine::~NoraEngine() {
    Shutdown();
}

bool NoraEngine::Initialize(const std::string& assetsPath) {
    std::cout << "====================================================\n";
    std::cout << "🚀 DÉMARRAGE DU MOTEUR C++ HAUTE PERFORMANCE NORA\n";
    std::cout << "====================================================\n";
    m_assetsPath = assetsPath;

    // 1. Préchargement en mémoire de tous les sprites plein corps
    if (!SpriteManager::Instance().PreloadAllSprites(assetsPath)) {
        std::cerr << "[C++ NoraEngine] Avertissement: Certains sprites n'ont pas pu être chargés.\n";
    }

    // 2. Initialisation de la fenêtre de rendu plein corps transparente (280x500)
    if (!LayeredRenderer::Instance().CreateMascotWindow(m_config.screenX, m_config.screenY, m_config.spriteWidth, m_config.spriteHeight)) {
        std::cerr << "[C++ NoraEngine] Échec d'initialisation de la fenêtre de rendu.\n";
        return false;
    }

    // 3. Activation du raccourci natif global
    NativeHotkeys::Instance().StartListening([this]() {
        std::cout << "[C++ NoraEngine] Raccourci Ctrl+Alt+N détecté ! Affichage cockpit QG.\n";
        SetState(State::IdleWave);
    });

    // 4. Connexion au bus neuronal
    NeuralBridge::Instance().Connect(8000);

    m_running.store(true);
    return true;
}

void NoraEngine::Shutdown() {
    if (m_running.load()) {
        m_running.store(false);
        NativeHotkeys::Instance().StopListening();
        NeuralBridge::Instance().Disconnect();
        LayeredRenderer::Instance().DestroyMascotWindow();
        if (m_workerThread.joinable()) {
            m_workerThread.join();
        }
        std::cout << "[C++ NoraEngine] Moteur arrêté proprement.\n";
    }
}

void NoraEngine::SetOutfit(Outfit outfit) {
    std::lock_guard<std::mutex> lock(m_engineMutex);
    m_config.currentOutfit = outfit;
}

void NoraEngine::SetState(State state) {
    std::lock_guard<std::mutex> lock(m_engineMutex);
    m_config.currentState = state;
}

void NoraEngine::SetDirection(int direction) {
    std::lock_guard<std::mutex> lock(m_engineMutex);
    m_config.facingDirection = (direction >= 0 ? 1 : -1);
}

void NoraEngine::StartWalk(int targetX, int speed) {
    m_walkTargetX = targetX;
    m_walkSpeed = speed > 0 ? speed : 3;
    m_isWalking.store(true);
    SetState(State::Walk);
    SetDirection(targetX > m_config.screenX ? 1 : -1);
}

void NoraEngine::StopWalk() {
    m_isWalking.store(false);
    SetState(State::IdleStanding);
}

void NoraEngine::AnimationTick() {
    std::lock_guard<std::mutex> lock(m_engineMutex);

    if (m_isWalking.load()) {
        int dx = m_walkTargetX - m_config.screenX;
        if (std::abs(dx) <= m_walkSpeed + 2) {
            m_config.screenX = m_walkTargetX;
            StopWalk();
        } else {
            int step = (dx > 0 ? m_walkSpeed : -m_walkSpeed);
            m_config.screenX += step;
            m_walkFrameIndex = (m_walkFrameIndex % 8) + 1;
        }
        LayeredRenderer::Instance().MoveWindowTo(m_config.screenX, m_config.screenY);
    }

    const ImageData* sprite = SpriteManager::Instance().GetSprite(
        m_config.currentOutfit,
        m_config.currentState,
        m_walkFrameIndex,
        m_config.facingDirection
    );

    if (sprite) {
        LayeredRenderer::Instance().RenderFrame(sprite, m_config.screenX, m_config.screenY, m_config.opacity);
    }
}

void NoraEngine::RunMainLoop() {
    std::cout << "[C++ NoraEngine] Boucle principale 60 FPS active.\n";
    auto lastTick = std::chrono::steady_clock::now();

    while (m_running.load()) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - lastTick).count();

        if (elapsed >= 16) { // ~60 FPS
            AnimationTick();
            lastTick = now;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
}

void NoraEngine::RequestExit() {
    m_running.store(false);
}

} // namespace Nora
