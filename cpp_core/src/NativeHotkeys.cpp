#include "NativeHotkeys.hpp"
#include <iostream>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

namespace Nora {

NativeHotkeys& NativeHotkeys::Instance() {
    static NativeHotkeys instance;
    return instance;
}

NativeHotkeys::NativeHotkeys() {}

NativeHotkeys::~NativeHotkeys() {
    StopListening();
}

bool NativeHotkeys::StartListening(std::function<void()> onTrigger) {
    if (m_listening.load()) return true;

    m_callback = onTrigger;
    m_listening.store(true);

    m_listenerThread = std::thread([this]() {
        // Enregistre le hotkey Ctrl+Alt+N (MOD_CONTROL | MOD_ALT, 'N' = 0x4E)
        const int HOTKEY_ID = 1002;
        if (!RegisterHotKey(NULL, HOTKEY_ID, MOD_CONTROL | MOD_ALT, 'N')) {
            std::cerr << "[C++ NativeHotkeys] Impossible d'enregistrer Ctrl+Alt+N.\n";
            return;
        }

        std::cout << "[C++ NativeHotkeys] ✔ Raccourci global 'Ctrl+Alt+N' actif (Win32 natif).\n";

        MSG msg;
        while (m_listening.load() && GetMessage(&msg, NULL, 0, 0)) {
            if (msg.message == WM_HOTKEY && msg.wParam == HOTKEY_ID) {
                if (m_callback) {
                    m_callback();
                }
            }
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }

        UnregisterHotKey(NULL, HOTKEY_ID);
    });

    return true;
}

void NativeHotkeys::StopListening() {
    if (m_listening.load()) {
        m_listening.store(false);
        PostQuitMessage(0);
        if (m_listenerThread.joinable()) {
            m_listenerThread.join();
        }
    }
}

} // namespace Nora

#else

namespace Nora {
NativeHotkeys& NativeHotkeys::Instance() { static NativeHotkeys i; return i; }
NativeHotkeys::NativeHotkeys() {}
NativeHotkeys::~NativeHotkeys() {}
bool NativeHotkeys::StartListening(std::function<void()>) { return true; }
void NativeHotkeys::StopListening() {}
}

#endif
