#include "LayeredRenderer.hpp"
#include <iostream>

#ifdef _WIN32

namespace Nora {

LRESULT CALLBACK MascotWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_NCHITTEST:
            return HTCAPTION; // Permet de glisser-déposer la mascotte naturellement
        case WM_RBUTTONUP: {
            POINT pt;
            GetCursorPos(&pt);
            // Déclencheur menu contextuel natif
            return 0;
        }
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

LayeredRenderer& LayeredRenderer::Instance() {
    static LayeredRenderer instance;
    return instance;
}

LayeredRenderer::LayeredRenderer() {
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    Gdiplus::GdiplusStartup(&m_gdiplusToken, &gdiplusStartupInput, NULL);

    m_blend.BlendOp = AC_SRC_OVER;
    m_blend.BlendFlags = 0;
    m_blend.SourceConstantAlpha = 255;
    m_blend.AlphaFormat = AC_SRC_ALPHA;
}

LayeredRenderer::~LayeredRenderer() {
    DestroyMascotWindow();
    if (m_gdiplusToken) {
        Gdiplus::GdiplusShutdown(m_gdiplusToken);
    }
}

bool LayeredRenderer::CreateMascotWindow(int x, int y, int width, int height) {
    m_width = width;
    m_height = height;

    HINSTANCE hInstance = GetModuleHandleW(NULL);
    WNDCLASSEXW wc{};
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = MascotWndProc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.lpszClassName = L"NoraNativeMascotClass";

    RegisterClassExW(&wc);

    m_hwnd = CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_TOPMOST,
        wc.lpszClassName,
        L"Nora Desktop Pet",
        WS_POPUP,
        x, y, width, height,
        NULL, NULL, hInstance, NULL
    );

    if (!m_hwnd) {
        std::cerr << "[C++ LayeredRenderer] Erreur création fenêtre Win32.\n";
        return false;
    }

    m_hdcScreen = GetDC(NULL);
    m_hdcMem = CreateCompatibleDC(m_hdcScreen);

    BITMAPINFO bmi{};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height; // Top-down
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    m_hBitmap = CreateDIBSection(m_hdcMem, &bmi, DIB_RGB_COLORS, &m_pvBits, NULL, 0);
    SelectObject(m_hdcMem, m_hBitmap);

    ShowWindow(m_hwnd, SW_SHOW);
    UpdateWindow(m_hwnd);

    std::cout << "[C++ LayeredRenderer] ✔ Fenêtre transparente Win32 créée (" << width << "x" << height << ") à (" << x << ", " << y << ").\n";
    return true;
}

void LayeredRenderer::DestroyMascotWindow() {
    if (m_hBitmap) {
        DeleteObject(m_hBitmap);
        m_hBitmap = nullptr;
    }
    if (m_hdcMem) {
        DeleteDC(m_hdcMem);
        m_hdcMem = nullptr;
    }
    if (m_hdcScreen) {
        ReleaseDC(NULL, m_hdcScreen);
        m_hdcScreen = nullptr;
    }
    if (m_hwnd) {
        DestroyWindow(m_hwnd);
        m_hwnd = nullptr;
    }
}

void LayeredRenderer::RenderFrame(const ImageData* sprite, int x, int y, float opacity) {
    if (!m_hwnd || !m_hdcMem || !m_pvBits) return;

    POINT ptSrc = { 0, 0 };
    POINT ptDst = { x, y };
    SIZE size = { m_width, m_height };

    m_blend.SourceConstantAlpha = static_cast<BYTE>(opacity * 255.0f);

    UpdateLayeredWindow(
        m_hwnd,
        m_hdcScreen,
        &ptDst,
        &size,
        m_hdcMem,
        &ptSrc,
        0,
        &m_blend,
        ULW_ALPHA
    );
}

void LayeredRenderer::MoveWindowTo(int x, int y) {
    if (!m_hwnd) return;
    SetWindowPos(m_hwnd, HWND_TOPMOST, x, y, m_width, m_height, SWP_NOSIZE | SWP_NOACTIVATE);
}

void LayeredRenderer::SetAlwaysOnTop(bool top) {
    if (!m_hwnd) return;
    SetWindowPos(m_hwnd, top ? HWND_TOPMOST : HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
}

} // namespace Nora

#else

namespace Nora {
// Fallback multiplateforme
LayeredRenderer& LayeredRenderer::Instance() { static LayeredRenderer i; return i; }
LayeredRenderer::LayeredRenderer() {}
LayeredRenderer::~LayeredRenderer() {}
bool LayeredRenderer::CreateMascotWindow(int, int, int, int) { return true; }
void LayeredRenderer::DestroyMascotWindow() {}
void LayeredRenderer::RenderFrame(const ImageData*, int, int, float) {}
void LayeredRenderer::MoveWindowTo(int, int) {}
void LayeredRenderer::SetAlwaysOnTop(bool) {}
}

#endif
