cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# 1. Path Calculation
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../")
set(ASSET_OUT_DIR "${PROJECT_ROOT}/include/assets")
file(MAKE_DIRECTORY ${ASSET_OUT_DIR})

# 2. Build Host Tools (ONLY if not cross-compiling for Android)
# This prevents the NDK from trying to build PC tools with a phone compiler
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

# 3. Android Library Target
add_library(minish_ndk SHARED native-lib.cpp)

file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
)
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# 4. Mandatory Compatibility Flags (The "Surgery")
target_compile_options(minish_ndk PRIVATE 
    -fpack-struct=4          # Fixes structure size mismatch
    -Wno-error=address-of-packed-member
    -fms-extensions          # Fixes illegal lvalue casts in engine files
    -D_64_BIT                # Signals code to use 64-bit safe logic
)

target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    . 
)

# 5. Dependency Sync
if(TARGET generate_assets_headers)
    add_dependencies(minish_ndk generate_assets_headers)
endif()

# 6. Linking Android System Libraries
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
