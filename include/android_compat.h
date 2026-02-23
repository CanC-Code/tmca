#ifndef ANDROID_COMPAT_H
#define ANDROID_COMPAT_H

#include <stdint.h>
#include <stddef.h>

// 1. Width-Agnostic Types
// ptr_t/addr_t scale to 64-bit on Android, preventing "loses precision" errors.
typedef uintptr_t ptr_t; 
typedef uintptr_t addr_t;

// 2. Pointer Compression & Structural Integrity
// GBA_PTR(type) forces 4-byte storage inside structs to satisfy static_asserts.
// PACKED with aligned(1) prevents the compiler from adding 64-bit tail padding.
#ifdef __ANDROID__
    #define PACKED __attribute__((packed, aligned(1), __may_alias__))
    #define GBA_PTR(type) uint32_t
#else
    #define PACKED 
    #define GBA_PTR(type) type*
#endif

// 3. Pointer Translation Macros
// Use these when moving data between compressed GBA_PTRs and active 64-bit RAM.
#define FROM_GBA_PTR(base, offset) ((void*)((uintptr_t)(base) + (uintptr_t)(offset)))
#define TO_GBA_PTR(base, ptr)      ((uint32_t)((uintptr_t)(ptr) - (uintptr_t)(base)))

// 4. Safe Arithmetic
// Standardizes pointer movement to avoid "illegal lvalue cast" errors.
#define ADVANCE_PTR(ptr, bytes) (ptr = (void*)((uintptr_t)(ptr) + (uintptr_t)(bytes)))

// 5. Standard GBA Types
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t  u8;
typedef int32_t  s32;
typedef int16_t  s16;
typedef int8_t   s8;

#endif // ANDROID_COMPAT_H
