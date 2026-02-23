#ifndef ANDROID_COMPAT_H
#define ANDROID_COMPAT_H

#include <stdint.h>
#include <stddef.h>

// 1. Handle Pointer-Width Integers
// ptr_t is used for active calculations on the 64-bit host.
typedef uintptr_t ptr_t; 

// 2. Pointer Compression (The "Gold" Fix)
// GBA_PTR(type) ensures that pointers stored inside structs take up 
// only 4 bytes (uint32_t) on Android, preventing struct inflation.
#ifdef __ANDROID__
    #define PACKED __attribute__((packed, aligned(1), __may_alias__))
    #define GBA_PTR(type) uint32_t
#else
    #define PACKED 
    #define GBA_PTR(type) type*
#endif

// 3. Fix for 'illegal lvalue cast'
// Standardizes pointer arithmetic to be 64-bit safe.
#define ADVANCE_PTR(ptr, bytes) (ptr = (void*)((uintptr_t)(ptr) + (bytes)))

// 4. Standard GBA Types
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t  u8;
typedef int32_t  s32;
typedef int16_t  s16;
typedef int8_t   s8;

#endif // ANDROID_COMPAT_H
