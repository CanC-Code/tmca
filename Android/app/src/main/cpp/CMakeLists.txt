cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# 1. Broaden the search to include .c and .cpp files in the project's root src directory
# Paths are relative to 'Android/app/src/main/cpp/' where this file is located.
# The project root is four levels up (../../../../)
file(GLOB_RECURSE ENGINE_SOURCES 
    "../../../../src/*.c"
    "../../../../src/*.cpp"
)

# 2. Add the native JNI wrapper and all discovered engine files
add_library(minish_ndk SHARED 
    native-lib.cpp 
    ${ENGINE_SOURCES}
)

# 3. Explicitly add include directories so the compiler can find headers
# Added both 'src' for general implementation and 'include' for definitions
target_include_directories(minish_ndk PRIVATE 
    ../../../../src
    ../../../../include
    . 
)

# 4. Link Android specific libraries
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
)
