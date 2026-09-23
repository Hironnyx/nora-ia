#pragma once
#ifndef LAYERED_RENDERER_HPP
#define LAYERED_RENDERER_HPP

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <gdiplus.h>
#endif

#include <string>
#include <memory>
#include "NoraEngine.hpp"
#include "SpriteManager.hpp"

namespace Nora {

class LayeredRenderer {
public:
    static LayeredRenderer& Instance();

    bool CreateMascotWindow(int x, int y, int width, int height);
    void DestroyMascotWindow();

    void RenderFrame(const ImageData* sprite, int x, int y, float opacity = 1.0f);
    void MoveWindowTo(int x, int y);
    void SetAlwaysOnTop(bool top);

#ifdef _WIN32
    HWND GetHwnd() const { return m_hwnd; }
#endif

private:
    LayeredRenderer();
    ~LayeredRenderer();

#ifdef _WIN32
    HWND m_hwnd = nullptr;
    ULONG_PTR m_gdiplusToken = 0;
    BLENDFUNCTION m_blend{};
    HDC m_hdcScreen = nullptr;
    HDC m_hdcMem = nullptr;
    HBITMAP m_hBitmap = nullptr;
    void* m_pvBits = nullptr;
    int m_width = 280;
    int m_height = 500;
#endif
};

} // namespace Nora

#endif // LAYERED_RENDERER_HPP
