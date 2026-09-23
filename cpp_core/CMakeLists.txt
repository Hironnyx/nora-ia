cmake_minimum_required(VERSION 3.20)
project(NoraNativeCore VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

file(GLOB_RECURSE SOURCES "src/*.cpp")
file(GLOB_RECURSE HEADERS "include/*.hpp")

add_executable(nora_native ${SOURCES} ${HEADERS})

if (WIN32)
    target_link_libraries(nora_native PRIVATE
        gdiplus
        user32
        gdi32
        wininet
    )
    if (MSVC)
        target_compile_options(nora_native PRIVATE /W4 /O2 /permissive-)
    else()
        target_compile_options(nora_native PRIVATE -Wall -Wextra -O3)
    endif()
endif()

message(STATUS "Configured NoraNativeCore with C++20")
