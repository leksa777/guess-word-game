cmake_minimum_required(VERSION 3.16)
project(game_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(game_core SHARED
    GameEngine.cpp
    bridge.cpp
)

target_include_directories(game_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

if (MSVC)
    target_compile_options(game_core PRIVATE /W4 /permissive-)
else()
    target_compile_options(game_core PRIVATE -Wall -Wextra -pedantic)
endif()

