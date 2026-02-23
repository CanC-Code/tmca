cmake_minimum_required(VERSION 3.22.1)
project(asset_processor)

# 1. Handle External Dependencies
# Downloads dependencies at configure time to fix "Target not found" errors
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

# 2. Explicit Source Management
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

# 3. Build the Executable
add_executable(asset_processor ${ASSET_PROCESSOR_SOURCES})

# Include local directories for header resolution
target_include_directories(asset_processor PRIVATE 
    . 
    assets
)

# 4. Linking
target_link_libraries(asset_processor PRIVATE 
    fmt::fmt 
    nlohmann_json::nlohmann_json 
    stdc++fs 
    util
)

# 5. Deployment
install(TARGETS asset_processor RUNTIME DESTINATION bin)
