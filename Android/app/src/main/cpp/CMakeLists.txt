cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# -------------------------------------------------------------------------
# 1. Path Calculation
# -------------------------------------------------------------------------
# Navigates to the project root where 'src', 'include', and 'tools' live.
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../")
set(ASSET_OUT_DIR "${PROJECT_ROOT}/include/assets")

# Ensure the asset output directory exists so the Android build can find it.
file(MAKE_DIRECTORY ${ASSET_OUT_DIR})

# -------------------------------------------------------------------------
# 2. Build Host Tools (ONLY if not cross-compiling for Android)
# -------------------------------------------------------------------------
# This prevents the NDK from trying to build PC tools (asset_processor) 
# with the phone's Clang compiler.
# -------------------------------------------------------------------------
if(NOT CMAKE_CROSSCOMPILING)
    add_subdirectory("${PROJECT_ROOT}/tools/src/asset_processor" "${CMAKE_CURRENT_BINARY_DIR}/asset_processor_build")

    add_custom_command(
        OUTPUT "${ASSET_OUT_DIR}/map_offsets.h" "${ASSET_OUT_DIR}/gfx_offsets.h"
        COMMAND asset_processor --input "${PROJECT_ROOT}/assets" --output "${ASSET_OUT_DIR}"
        DEPENDS asset_processor
        COMMENT "Generating GBA asset offset headers for the Android build..."
    )

    add_custom_target(generate_assets_headers DEPENDS "${ASSET_OUT_DIR}/map_offsets.h")
endif()

# -------------------------------------------------------------------------
# 3. Android Library Target
# -------------------------------------------------------------------------
add_library(minish_ndk SHARED native-lib.cpp)

# Recursively collect all engine source files.
file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
)
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# -------------------------------------------------------------------------
# 4. Mandatory Compatibility Flags (The "Surgery")
# -------------------------------------------------------------------------
# These flags are non-negotiable for porting 32-bit heritage code to 64-bit.
# -------------------------------------------------------------------------
target_compile_options(minish_ndk PRIVATE 
    -fpack-struct=4          # CRITICAL: Forces 4-byte alignment to fix static_assert failures.
    -Wno-error=address-of-packed-member
    -fms-extensions          # CRITICAL: Allows legacy pointer arithmetic (fixes lvalue casts).
    -D_64_BIT                # Signals code to use 64-bit safe logic paths.
)

target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    . 
)

# -------------------------------------------------------------------------
# 5. Dependency Sync
# -------------------------------------------------------------------------
# Ensure the assets are processed BEFORE the engine tries to compile files
# that depend on 'map_offsets.h'.
# -------------------------------------------------------------------------
if(TARGET generate_assets_headers)
    add_dependencies(minish_ndk generate_assets_headers)
endif()

# -------------------------------------------------------------------------
# 6. Linking Android System Libraries
# -------------------------------------------------------------------------
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
