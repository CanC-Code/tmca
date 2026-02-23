#ifndef ANDROID_COMPAT_H
#define ANDROID_COMPAT_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. The ROM "Anchor"
// This holds the real 64-bit address where the APK's ROM is mapped in Android RAM.
// It is defined in native-lib.cpp and used globally.
extern uint8_t* gRomBaseAddress;

// 2. Width-Agnostic Types
typedef uintptr_t ptr_t; 
typedef uintptr_t addr_t;

// 3. Pointer Compression & Structural Integrity
#ifdef __ANDROID__
    #define PACKED __attribute__((packed, aligned(1), __may_alias__))
    // Forces pointers inside structs to stay 4 bytes.
    #define GBA_PTR(type) uint32_t
    
    // Safety Macro: Converts a 32-bit GBA ROM offset to a 64-bit Android pointer.
    // Masks with 0x01FFFFFF to remove the GBA's bank prefix (0x08).
    #define RESOLVE_ROM_PTR(offset) ((void*)(gRomBaseAddress + ((uint32_t)(offset) & 0x01FFFFFF)))
#else
    #define PACKED 
    #define GBA_PTR(type) type*
    #define RESOLVE_ROM_PTR(offset) (offset)
#endif

// 4. Pointer Translation Macros
#define FROM_GBA_PTR(base, offset) ((void*)((uintptr_t)(base) + (uintptr_t)(offset)))
#define TO_GBA_PTR(base, ptr)      ((uint32_t)((uintptr_t)(ptr) - (uintptr_t)(base)))

// 5. Safe Arithmetic
#define ADVANCE_PTR(ptr, bytes) (ptr = (void*)((uintptr_t)(ptr) + (uintptr_t)(bytes)))

// 6. Standard GBA Types
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t  u8;
typedef int32_t  s32;
typedef int16_t  s16;
typedef int8_t   s8;
typedef int32_t  bool32;
typedef uint8_t  bool8;

#define UNUSED __attribute__((unused))

#endif // ANDROID_COMPAT_H
