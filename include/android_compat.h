#ifndef ANDROID_COMPAT_H
#define ANDROID_COMPAT_H

#include <stdint.h>
#include <stddef.h>

// 1. Handle Pointer-Width Integers
// On arm64, pointers are 64-bit. uintptr_t ensures we don't truncate 
// addresses when performing the arithmetic used in the original engine.
typedef uintptr_t ptr_t; 

// 2. Absolute Force Packing
// We use aligned(1) to prevent "Tail Padding". 
// This ensures that sizeof(Entity) is exactly 0x44 and sizeof(Room) is 0xB0,
// matching the original GBA memory layout exactly.
#ifdef __ANDROID__
    #define PACKED __attribute__((packed, aligned(1), __may_alias__))
#else
    #define PACKED 
#endif

// 3. Fix for 'illegal lvalue cast'
// Standardizes pointer arithmetic to be 64-bit safe.
#define ADVANCE_PTR(ptr, bytes) (ptr = (void*)((uintptr_t)(ptr) + (bytes)))

#endif // ANDROID_COMPAT_H
