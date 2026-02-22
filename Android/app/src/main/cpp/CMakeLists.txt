cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# 1. Broaden the search to include .cpp files and verify the path
# If your engine is in the root 'src' folder, ensure this path is correct 
# relative to 'Android/app/src/main/cpp/'
file(GLOB_RECURSE ENGINE_SOURCES 
    "../../../../src/*.c"
    "../../../../src/*.cpp"
    "../../../../tmca/src/*.c"
    "../../../../tmca/src/*.cpp"
)

# 2. Add the native JNI wrapper and all discovered engine files
add_library(minish_ndk SHARED 
    native-lib.cpp 
    ${ENGINE_SOURCES}
)

# 3. Explicitly add include directories so the compiler can find your headers (.h)
# This prevents "file not found" errors during the compilation phase
target_include_directories(minish_ndk PRIVATE 
    ../../../../src
    ../../../../tmca/src
    . 
)

# 4. Link Android specific libraries
target_link_libraries(minish_ndk 
    log 
    android 
    jnigraphics
)
