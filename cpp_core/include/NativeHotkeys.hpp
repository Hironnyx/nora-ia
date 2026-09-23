#pragma once
#ifndef NATIVE_HOTKEYS_HPP
#define NATIVE_HOTKEYS_HPP

#include <functional>
#include <atomic>
#include <thread>

namespace Nora {

class NativeHotkeys {
public:
    static NativeHotkeys& Instance();

    bool StartListening(std::function<void()> onTrigger);
    void StopListening();

private:
    NativeHotkeys();
    ~NativeHotkeys();

    std::atomic<bool> m_listening{false};
    std::thread m_listenerThread;
    std::function<void()> m_callback;
};

} // namespace Nora

#endif // NATIVE_HOTKEYS_HPP
