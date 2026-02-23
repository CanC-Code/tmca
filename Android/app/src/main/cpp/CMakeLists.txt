cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# -------------------------------------------------------------------------
# 1. Path & Environment Setup
# -------------------------------------------------------------------------
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../")
set(ASSET_OUT_DIR "${PROJECT_ROOT}/include/assets")

# Ensure the asset output directory exists
file(MAKE_DIRECTORY ${ASSET_OUT_DIR})

# -------------------------------------------------------------------------
# 2. Phase One: Build the Host Tools (Asset Processor)
# -------------------------------------------------------------------------
# We must compile the asset_processor using the HOST compiler (your PC), 
# not the Android NDK compiler, to generate headers during the build.
# -------------------------------------------------------------------------
add_subdirectory("${PROJECT_ROOT}/tools/src/asset_processor" "${CMAKE_CURRENT_BINARY_DIR}/asset_processor_build")

# -------------------------------------------------------------------------
# 3. Phase Two: Generate Missing Headers (The "Offsets" Fix)
# -------------------------------------------------------------------------
# This addresses: 'assets/map_offsets.h' and 'assets/gfx_offsets.h' not found.
# -------------------------------------------------------------------------
add_custom_command(
    OUTPUT "${ASSET_OUT_DIR}/map_offsets.h" "${ASSET_OUT_DIR}/gfx_offsets.h"
    COMMAND asset_processor --input "${PROJECT_ROOT}/assets" --output "${ASSET_OUT_DIR}"
    DEPENDS asset_processor
    COMMENT "Running runtime asset processor to generate offset headers..."
)

# -------------------------------------------------------------------------
# 4. Phase Three: Android Library Compilation
# -------------------------------------------------------------------------
add_library(minish_ndk SHARED native-lib.cpp)

# Collect all engine sources
file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
)

# Filter out potential conflicts or assembly files if necessary
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# -------------------------------------------------------------------------
# 5. Phase Four: Architecture Adaptation (The "Static Assert" Fix)
# -------------------------------------------------------------------------
# To fix the 'static_assert' failures and 'illegal lvalue cast', we need
# specific compiler flags to force 32-bit alignment and allow legacy C patterns.
# -------------------------------------------------------------------------
target_compile_options(minish_ndk PRIVATE 
    -fpack-struct=4          # Force 4-byte alignment (GBA style) to satisfy static_asserts
    -Wno-error=address-of-packed-member
    -fms-extensions          # Allows some non-standard C pointer arithmetic
    -D_64_BIT                # Define to help headers adapt to arm64
)

target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    . 
)

# Ensure headers are generated BEFORE we try to compile caveBorderMapData.c
add_custom_target(generate_assets_headers DEPENDS "${ASSET_OUT_DIR}/map_offsets.h")
add_dependencies(minish_ndk generate_assets_headers)

# -------------------------------------------------------------------------
# 6. Linking
# -------------------------------------------------------------------------
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
