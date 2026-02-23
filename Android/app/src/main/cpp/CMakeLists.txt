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

# -------------------------------------------------------------------------
# 2. Android Library Target
# -------------------------------------------------------------------------
add_library(minish_ndk SHARED native-lib.cpp)

# REVISION: Include sound and data directories found in your directory structure
file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
    "${PROJECT_ROOT}/sound/*.c"   # Added: Original GBA Sound Engine
    "${PROJECT_ROOT}/data/*.c"    # Added: Hardcoded tables and data constants
)
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# -------------------------------------------------------------------------
# 3. Include Resolution
# -------------------------------------------------------------------------
target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    "${PROJECT_ROOT}/sound"       # Added: For m4a.h and sound headers
    "${ASSET_OUT_DIR}"
    . 
)

# -------------------------------------------------------------------------
# 4. Mandatory Compatibility Flags
# -------------------------------------------------------------------------
target_compile_options(minish_ndk PRIVATE 
    -fpack-struct=4          
    -Wno-error=address-of-packed-member
    -fms-extensions          
    -D_64_BIT                
    -DANDROID_PORT           
    -O2                       # Added: Recommended for sound engine performance
)

# -------------------------------------------------------------------------
# 5. Linking System Libraries
# -------------------------------------------------------------------------
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
