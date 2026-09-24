// nora_core_native.cpp
// Noyau C++ Natif Haute Performance pour Nora OS
// Compilable en DLL native 64-bit sous Windows (MSVC / Clang / MinGW)

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <psapi.h>
#include <dwmapi.h>
#include <cstdint>

#pragma comment(lib, "user32.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "psapi.lib")
#pragma comment(lib, "dwmapi.lib")

extern "C" {

struct NativeSystemStats {
    double cpu_usage_percent;
    uint64_t ram_total_mb;
    uint64_t ram_free_mb;
    uint32_t ram_load_percent;
};

struct NativeWindowInfo {
    HWND hwnd;
    uint32_t pid;
    wchar_t title[256];
    wchar_t process_name[256];
    RECT bounds;
    BOOL is_fullscreen;
};

// 1. Télémétrie Mémoire & Système Ultra-Rapide (< 0.01 ms)
__declspec(dllexport) BOOL GetNativeSystemMemory(NativeSystemStats* out_stats) {
    if (!out_stats) return FALSE;

    MEMORYSTATUSEX mem_status;
    mem_status.dwLength = sizeof(MEMORYSTATUSEX);
    if (GlobalMemoryStatusEx(&mem_status)) {
        out_stats->ram_total_mb = mem_status.ullTotalPhys / (1024 * 1024);
        out_stats->ram_free_mb = mem_status.ullAvailPhys / (1024 * 1024);
        out_stats->ram_load_percent = mem_status.dwMemoryLoad;
        return TRUE;
    }
    return FALSE;
}

// 2. Détection Instantanée de la Fenêtre Active & Bounding Box DWM
__declspec(dllexport) BOOL GetNativeActiveWindow(NativeWindowInfo* out_info) {
    if (!out_info) return FALSE;

    HWND hwnd = GetForegroundWindow();
    if (!hwnd) return FALSE;

    out_info->hwnd = hwnd;
    GetWindowTextW(hwnd, out_info->title, 256);

    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);
    out_info->pid = pid;

    // Récupérer le nom de l'exécutable
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    if (hProcess) {
        GetProcessImageFileNameW(hProcess, out_info->process_name, 256);
        CloseHandle(hProcess);
    } else {
        out_info->process_name[0] = L'\0';
    }

    // Récupérer les dimensions réelles sans ombre DWM
    DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, &out_info->bounds, sizeof(RECT));

    // Détection plein écran
    int screen_w = GetSystemMetrics(SM_CXSCREEN);
    int screen_h = GetSystemMetrics(SM_CYSCREEN);
    int w = out_info->bounds.right - out_info->bounds.left;
    int h = out_info->bounds.bottom - out_info->bounds.top;
    out_info->is_fullscreen = (w >= screen_w && h >= screen_h);

    return TRUE;
}

// 3. Purge Matérielle Native de la RAM (Working Set Purge)
__declspec(dllexport) BOOL NativePurgeWorkingSet() {
    return SetProcessWorkingSetSize(GetCurrentProcess(), (SIZE_T)-1, (SIZE_T)-1);
}

} // extern "C"
