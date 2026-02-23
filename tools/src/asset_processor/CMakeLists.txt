cmake_minimum_required(VERSION 3.22.1)
project(asset_processor)

# Handle external dependencies via FetchContent
include(FetchContent)

FetchContent_Declare(
  fmt
  GIT_REPOSITORY https://github.com/fmtlib/fmt.git
  GIT_TAG 10.1.1
)
FetchContent_MakeAvailable(fmt)

FetchContent_Declare(
  nlohmann_json
  URL https://github.com/nlohmann/json/releases/download/v3.11.2/json.tar.xz
)
FetchContent_MakeAvailable(nlohmann_json)

# Use explicit sources for stability
set(ASSET_PROCESSOR_SOURCES
    main.cpp
    offsets.cpp
    util.cpp
    assets/aif.cpp
    assets/animation.cpp
    assets/asset.cpp
    assets/dungeonmap.cpp
    assets/frameobjlists.cpp
    assets/gfx.cpp
    assets/macroasm.cpp
    assets/map.cpp
    assets/midi.cpp
    assets/palette.cpp
    assets/spriteframe.cpp
    assets/subtileset.cpp
)

add_executable(asset_processor ${ASSET_PROCESSOR_SOURCES})

target_include_directories(asset_processor PRIVATE . assets)

# Link dependencies, including the newly fetched fmt and json
target_link_libraries(asset_processor PRIVATE 
    fmt::fmt 
    nlohmann_json::nlohmann_json 
    filesystem 
    util
)

install(TARGETS asset_processor RUNTIME DESTINATION bin)
