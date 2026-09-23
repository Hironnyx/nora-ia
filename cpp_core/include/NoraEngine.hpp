#pragma once
#ifndef NORA_ENGINE_HPP
#define NORA_ENGINE_HPP

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <atomic>
#include <mutex>
#include <thread>
#include <chrono>

namespace Nora {

enum class Outfit {
    Franxx,
    School,
    Hoodie,
    Cyberpunk,
    Commander
};

enum class State {
    IdleStanding,
    IdleArmsCrossed,
    IdleWave,
    IdleThinking,
    IdleSitting,
    IdleWorkHologram,
    IdleGaming,
    Walk,
    Run,
    TalkOpen,
    TalkClosed,
    Blink,
    AlertShield
};

struct MascotConfig {
    int screenX = 1400;
    int screenY = 650;
    int spriteWidth = 280;
    int spriteHeight = 500;
    Outfit currentOutfit = Outfit::Franxx;
    State currentState = State::IdleStanding;
    int facingDirection = 1; // 1 = droite, -1 = gauche
    float scale = 1.0f;
    float opacity = 1.0f;
    bool roamingEnabled = true;
};

class NoraEngine {
public:
    static NoraEngine& Instance();

    bool Initialize(const std::string& assetsPath);
    void Shutdown();

    void RunMainLoop();
    void RequestExit();

    // Gestion des tenues et états
    void SetOutfit(Outfit outfit);
    void SetState(State state);
    void SetDirection(int direction); // 1 = right, -1 = left
    void StartWalk(int targetX, int speed = 3);
    void StopWalk();

    // Télémétrie et callbacks
    void RegisterStateCallback(std::function<void(State, Outfit)> callback);
    void DispatchLog(const std::string& log);

    // Getters
    Outfit GetCurrentOutfit() const { return m_config.currentOutfit; }
    State GetCurrentState() const { return m_config.currentState; }
    int GetX() const { return m_config.screenX; }
    int GetY() const { return m_config.screenY; }
    bool IsRunning() const { return m_running.load(); }

private:
    NoraEngine();
    ~NoraEngine();

    NoraEngine(const NoraEngine&) = delete;
    NoraEngine& operator=(const NoraEngine&) = delete;

    void AnimationTick();
    void RoamingTick();

    MascotConfig m_config;
    std::string m_assetsPath;
    std::atomic<bool> m_running{false};
    std::atomic<bool> m_isWalking{false};
    int m_walkTargetX = 0;
    int m_walkSpeed = 3;
    int m_walkFrameIndex = 1;

    std::mutex m_engineMutex;
    std::vector<std::function<void(State, Outfit)>> m_callbacks;
    std::thread m_workerThread;
};

} // namespace Nora

#endif // NORA_ENGINE_HPP
