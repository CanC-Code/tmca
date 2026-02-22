cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# 1. Define the root of the project relative to this file
set(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../")

# 2. Explicitly add the core engine files. 
# We start with main.c because it contains main_init and main_step.
add_library(minish_ndk SHARED 
    native-lib.cpp 
    "${PROJECT_ROOT}/src/main.c"
    # If main.c depends on other files, add them here or use the glob below
)

# 3. Now try to gather the rest of the engine
file(GLOB_RECURSE ENGINE_SOURCES 
    "${PROJECT_ROOT}/src/*.c"
    "${PROJECT_ROOT}/src/*.cpp"
)
target_sources(minish_ndk PRIVATE ${ENGINE_SOURCES})

# 4. Fix Include Paths
# Your structure shows headers in /include and /src
target_include_directories(minish_ndk PRIVATE 
    "${PROJECT_ROOT}/include"
    "${PROJECT_ROOT}/src"
    . 
)

# 5. Link Libraries
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
    atomic
    m
)
