cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# -------------------------------------------------------------------------
# 1. Path Calculation & Standards
# -------------------------------------------------------------------------
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../")
set(ASSET_OUT_DIR "${PROJECT_ROOT}/include/assets")

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)

file(MAKE_DIRECTORY ${ASSET_OUT_DIR})

# -------------------------------------------------------------------------
# 2. Build Host Tools
# -------------------------------------------------------------------------
if(NOT CMAKE_CROSSCOMPILING)
    add_subdirectory("${PROJECT_ROOT}/tools/src/asset_processor" "${CMAKE_CURRENT_BINARY_DIR}/asset_processor_build")

    # Define the generated files explicitly
    set(GENERATED_ASSET_HEADERS 
        "${ASSET_OUT_DIR}/map_offsets.h" 
        "${ASSET_OUT_DIR}/gfx_offsets.h"
    )

    add_custom_command(
        OUTPUT ${GENERATED_ASSET_HEADERS}
        COMMAND asset_processor --input "${PROJECT_ROOT}/assets" --output "${ASSET_OUT_DIR}"
        DEPENDS asset_processor
        COMMENT "Generating GBA asset offset headers..."
        VERBATIM
    )

    add_custom_target(generate_assets_headers DEPENDS ${GENERATED_ASSET_HEADERS})
endif()

# -------------------------------------------------------------------------
# 3. Android Library Target
# -------------------------------------------------------------------------
add_library(minish_ndk SHARED native-lib.cpp)

# Collect all sources - Ensure we don't miss any subdirectories
file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
)
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# -------------------------------------------------------------------------
# 4. Mandatory Compatibility Flags & Include Resolution
# -------------------------------------------------------------------------
target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    "${ASSET_OUT_DIR}"
    . 
)

target_compile_options(minish_ndk PRIVATE 
    -fpack-struct=4          
    -Wno-error=address-of-packed-member
    -fms-extensions          
    -D_64_BIT                
    -DANDROID_PORT           
)

# -------------------------------------------------------------------------
# 5. Dependency Surgery (Fixes Race Condition)
# -------------------------------------------------------------------------
# This forces the NDK to wait for the asset_processor to finish 
# before a single .c file is compiled.
if(TARGET generate_assets_headers)
    add_dependencies(minish_ndk generate_assets_headers)
    
    # Tell CMake that EVERY source file depends on the generated headers
    set_source_files_properties(${ENGINE_SOURCES} PROPERTIES 
        OBJECT_DEPENDS "${ASSET_OUT_DIR}/map_offsets.h"
    )
endif()

# -------------------------------------------------------------------------
# 6. Linking System Libraries
# -------------------------------------------------------------------------
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
