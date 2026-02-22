cmake_minimum_required(VERSION 3.22.1)
project("minish_ndk")

# Add the tmc source files you reviewed earlier
file(GLOB_RECURSE GAME_SOURCES 
    "../../../../tmca/src/*.c"
)

add_library(minish_ndk SHARED 
    native-lib.cpp 
    ${GAME_SOURCES}
)

target_link_libraries(minish_ndk log android)

