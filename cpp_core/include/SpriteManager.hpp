#pragma once
#ifndef SPRITE_MANAGER_HPP
#define SPRITE_MANAGER_HPP

#include <string>
#include <unordered_map>
#include <memory>
#include <vector>
#include "NoraEngine.hpp"

namespace Nora {

struct ImageData {
    int width = 0;
    int height = 0;
    int channels = 4;
    std::vector<unsigned char> pixels; // Format RGBA 32-bit
    bool isValid = false;
};

class SpriteManager {
public:
    static SpriteManager& Instance();

    bool PreloadAllSprites(const std::string& assetsBaseDir);
    const ImageData* GetSprite(Outfit outfit, State state, int frame = 1, int direction = 1);
    
    size_t GetTotalCachedSprites() const { return m_cache.size(); }
    void ClearCache();

private:
    SpriteManager() = default;
    ~SpriteManager() = default;

    std::string OutfitToString(Outfit o) const;
    std::string StateToString(State s, int frame = 1) const;
    std::string BuildKey(Outfit o, State s, int frame, int dir) const;

    bool LoadPngFile(const std::string& filePath, ImageData& outData);
    void FlipHorizontal(const ImageData& src, ImageData& dst);

    std::unordered_map<std::string, ImageData> m_cache;
};

} // namespace Nora

#endif // SPRITE_MANAGER_HPP
