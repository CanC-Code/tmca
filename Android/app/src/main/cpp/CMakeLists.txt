cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# -------------------------------------------------------------------------
# 1. Path Calculation & Standards
# -------------------------------------------------------------------------
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../")
set(ASSET_OUT_DIR "${PROJECT_ROOT}/include/assets")

# Force standards to ensure compatibility with patched source
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)

file(MAKE_DIRECTORY ${ASSET_OUT_DIR})

# -------------------------------------------------------------------------
# 2. Build Host Tools (ONLY if not cross-compiling)
# -------------------------------------------------------------------------
if(NOT CMAKE_CROSSCOMPILING)
    add_subdirectory("${PROJECT_ROOT}/tools/src/asset_processor" "${CMAKE_CURRENT_BINARY_DIR}/asset_processor_build")

    add_custom_command(
        OUTPUT "${ASSET_OUT_DIR}/map_offsets.h" "${ASSET_OUT_DIR}/gfx_offsets.h"
        COMMAND asset_processor --input "${PROJECT_ROOT}/assets" --output "${ASSET_OUT_DIR}"
        DEPENDS asset_processor
        COMMENT "Generating GBA asset offset headers..."
    )

    add_custom_target(generate_assets_headers DEPENDS "${ASSET_OUT_DIR}/map_offsets.h")
endif()

# -------------------------------------------------------------------------
# 3. Android Library Target & Include Resolution
# -------------------------------------------------------------------------
add_library(minish_ndk SHARED native-lib.cpp)

# Recursively collect all engine source files.
file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
)
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# CRITICAL: Explicitly map include directories for the NDK compiler
target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    "${PROJECT_ROOT}/include/assets"
    . 
)

# -------------------------------------------------------------------------
# 4. Mandatory Compatibility Flags (The "Surgery")
# -------------------------------------------------------------------------
target_compile_options(minish_ndk PRIVATE 
    -fpack-struct=4          
    -Wno-error=address-of-packed-member
    -fms-extensions          
    -D_64_BIT                
    -DANDROID_PORT           # Signals code to bypass GBA-specific assembly
)

# -------------------------------------------------------------------------
# 5. Dependency Sync & Linking
# -------------------------------------------------------------------------
if(TARGET generate_assets_headers)
    add_dependencies(minish_ndk generate_assets_headers)
endif()

target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
