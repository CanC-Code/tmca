#ifndef ANDROID_COMPAT_H
#define ANDROID_COMPAT_H

#include <stdint.h>
#include <stddef.h>

// 1. Handle Pointer-Width Integers
// The original code uses 'u32' to store addresses. 
// On arm64, a pointer is 64-bit. We use uintptr_t to ensure safety.
typedef uintptr_t ptr_t; 

// 2. Force alignment/packing for 64-bit targets
// This helps fix the 'static_assert' failures by telling the 
// Android compiler to mimic GBA's 32-bit packing rules.
#ifdef __ANDROID__
    #define PACKED __attribute__((packed, aligned(4)))
#else
    #define PACKED 
#endif

// 3. Fix for 'illegal lvalue cast'
// Instead of (u8*)d += 8, we will use a macro for safe arithmetic
#define ADVANCE_PTR(ptr, bytes) (ptr = (void*)((uintptr_t)(ptr) + (bytes)))

#endif // ANDROID_COMPAT_H
