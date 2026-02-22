cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# Automatically include all engine source files
file(GLOB_RECURSE ENGINE_SOURCES 
    "../../../../tmca/src/*.c"
)

add_library(minish_ndk SHARED 
    native-lib.cpp 
    ${ENGINE_SOURCES}
)

# Link Android specific libraries for Bitmap handling and Logging
target_link_libraries(minish_ndk log android jnigraphics)
