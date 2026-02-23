# Use a specific list of sources instead of GLOB to ensure build consistency
set(ASSET_PROCESSOR_SOURCES
    main.cpp
    offsets.cpp
    util.cpp
    # Sub-component processors
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

# Include both the tool root and the assets subfolder for headers
target_include_directories(asset_processor PRIVATE 
    .
    assets
)

# Linking dependencies
target_link_libraries(asset_processor PRIVATE 
    project_settings
    fmt::fmt 
    nlohmann_json::nlohmann_json 
    filesystem 
    util
)

# Standard installation to bin directory
install(TARGETS asset_processor RUNTIME DESTINATION bin)
