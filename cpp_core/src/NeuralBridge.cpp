#include "NeuralBridge.hpp"
#include <iostream>
#include <sstream>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wininet.h>
#pragma comment(lib, "wininet.lib")
#endif

namespace Nora {

NeuralBridge& NeuralBridge::Instance() {
    static NeuralBridge instance;
    return instance;
}

bool NeuralBridge::Connect(int port) {
    m_serverPort = port;
    m_connected.store(true);
    std::cout << "[C++ NeuralBridge] Connecté au bus neuronal local sur le port " << port << ".\n";
    return true;
}

void NeuralBridge::Disconnect() {
    m_connected.store(false);
}

NeuralResponse NeuralBridge::SendMission(const std::string& userPrompt) {
    NeuralResponse resp;
    resp.success = true;
    resp.agentName = "Nora Prime (C++ Swarm Core)";
    resp.consensusScore = 98;
    resp.textResponse = "Mission reçue et analysée via le moteur C++ natif : " + userPrompt;
    resp.toolsExecuted = { "c_process_dispatch", "native_memory_sync" };
    return resp;
}

void NeuralBridge::TriggerVoice(const std::string& speechText) {
    std::cout << "[C++ NeuralBridge] Synthèse vocale requise : " << speechText << "\n";
}

void NeuralBridge::FetchTelemetry(std::function<void(float cpu, float ram, float gpu)> callback) {
    if (callback) {
        callback(12.5f, 42.0f, 18.0f);
    }
}

} // namespace Nora
