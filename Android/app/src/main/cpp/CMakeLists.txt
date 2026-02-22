cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# 1. Path Calculation
# From: Android/app/src/main/cpp/
# Step 1 (..): Android/app/src/main/
# Step 2 (..): Android/app/src/
# Step 3 (..): Android/app/
# Step 4 (..): Android/
# Step 5 (..): [ROOT]
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../")

# 2. Add the library
# We explicitly include native-lib.cpp and point to the root src for engine files
add_library(minish_ndk SHARED 
    native-lib.cpp
)

# 3. Use GLOB_RECURSE with the verified ROOT path
file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
)

# Add the discovered sources to the target
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# 4. Include Directories
# We need the 'include' folder and the 'src' folder for headers
target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    . 
)

# 5. Required Android Libraries
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
