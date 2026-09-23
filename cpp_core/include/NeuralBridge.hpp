#pragma once
#ifndef NEURAL_BRIDGE_HPP
#define NEURAL_BRIDGE_HPP

#include <string>
#include <functional>
#include <vector>
#include <memory>
#include <thread>
#include <atomic>

namespace Nora {

struct NeuralResponse {
    bool success = false;
    std::string agentName;
    std::string textResponse;
    int consensusScore = 100;
    std::vector<std::string> toolsExecuted;
};

class NeuralBridge {
public:
    static NeuralBridge& Instance();

    bool Connect(int port = 8000);
    void Disconnect();

    NeuralResponse SendMission(const std::string& userPrompt);
    void TriggerVoice(const std::string& speechText);
    void FetchTelemetry(std::function<void(float cpu, float ram, float gpu)> callback);

private:
    NeuralBridge() = default;
    ~NeuralBridge() = default;

    std::atomic<bool> m_connected{false};
    int m_serverPort = 8000;
};

} // namespace Nora

#endif // NEURAL_BRIDGE_HPP
