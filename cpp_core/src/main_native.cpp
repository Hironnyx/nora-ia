#include "NoraEngine.hpp"
#include <iostream>
#include <filesystem>

namespace fs = std::filesystem;

int main(int argc, char* argv[]) {
    std::cout << "=========================================================\n";
    std::cout << "✨ NORA COPILOTE - MOTEUR NATIF C++20 HAUTE PERFORMANCE ✨\n";
    std::cout << "=========================================================\n";

    fs::path currentPath = fs::current_path();
    fs::path assetsPath = currentPath / "mascot_assets";
    if (!fs::exists(assetsPath)) {
        assetsPath = currentPath.parent_path() / "mascot_assets";
    }

    Nora::NoraEngine& engine = Nora::NoraEngine::Instance();
    if (!engine.Initialize(assetsPath.string())) {
        std::cerr << "Erreur: Impossible d'initialiser NoraEngine.\n";
        return 1;
    }

    std::cout << "✔ Moteur C++ initialisé avec succès.\n";
    std::cout << "✔ Appuyez sur Ctrl+C ou fermez l'application pour quitter.\n";

    // Lance la boucle 60 FPS
    engine.RunMainLoop();

    engine.Shutdown();
    return 0;
}
