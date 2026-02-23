cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# -------------------------------------------------------------------------
# 1. Path & Environment Setup
# -------------------------------------------------------------------------
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../")
set(ASSET_OUT_DIR "${PROJECT_ROOT}/include/assets")

# Ensure the asset output directory exists so the Android build can find it
file(MAKE_DIRECTORY ${ASSET_OUT_DIR})

# -------------------------------------------------------------------------
# 2. Phase One: Build the Host Tools (Asset Processor)
# -------------------------------------------------------------------------
# We wrap this in a check for CMAKE_CROSSCOMPILING. 
# The asset_processor must be built with a HOST compiler (Linux/Mac/Windows), 
# not the Android NDK compiler, to generate headers during the build.
# -------------------------------------------------------------------------
if(NOT CMAKE_CROSSCOMPILING)
    add_subdirectory("${PROJECT_ROOT}/tools/src/asset_processor" "${CMAKE_CURRENT_BINARY_DIR}/asset_processor_build")

    # Define the generation command to produce required headers
    add_custom_command(
        OUTPUT "${ASSET_OUT_DIR}/map_offsets.h" "${ASSET_OUT_DIR}/gfx_offsets.h"
        COMMAND asset_processor --input "${PROJECT_ROOT}/assets" --output "${ASSET_OUT_DIR}"
        DEPENDS asset_processor
        COMMENT "Running runtime asset processor to generate offset headers..."
    )
    
    # Create a target for the headers
    add_custom_target(generate_assets_headers DEPENDS "${ASSET_OUT_DIR}/map_offsets.h")
endif()

# -------------------------------------------------------------------------
# 3. Phase Two: Android Library Compilation
# -------------------------------------------------------------------------
add_library(minish_ndk SHARED native-lib.cpp)

# Collect all engine sources
file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
)
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# -------------------------------------------------------------------------
# 4. Phase Three: Architecture & Compatibility Fixes
# -------------------------------------------------------------------------
# 
# -fpack-struct=4: Fixes static_asserts by forcing 32-bit alignment logic.
# -fms-extensions: Fixes "assignment to cast is illegal" (lvalue cast) errors.
target_compile_options(minish_ndk PRIVATE 
    -fpack-struct=4          
    -Wno-error=address-of-packed-member
    -fms-extensions          
    -D_64_BIT                
)

target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    . 
)

# If we are building on the host, ensure headers are generated before the library
if(TARGET generate_assets_headers)
    add_dependencies(minish_ndk generate_assets_headers)
endif()

# -------------------------------------------------------------------------
# 5. Linking
# -------------------------------------------------------------------------
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
