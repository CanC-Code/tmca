#include <jni.h>
#include <unistd.h>
#include <android/log.h>
#include <android/bitmap.h>
#include <sys/mman.h>
#include <vector>
#include <string>
#include <cstring>
#include <fcntl.h>
#include <sys/stat.h>

#define LOG_TAG "MinishNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// The extern "C" block ensures the C++ linker can see the C symbols from the engine
extern "C" {
    #include "global.h"
    #include "android_compat.h"

    // 1. Define the Global Anchor declared in android_compat.h
    uint8_t* gRomBaseAddress = nullptr;
    size_t gRomSize = 0;

    // Engine Entry Points
    void main_init(void);
    void main_step(void);

    // Virtual Hardware Memory
    uint16_t g_vram[240 * 160];
    uint16_t g_io_regs[0x10000 / 2];

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_initGameWithRom(JNIEnv* env, jobject thiz, jint fd, jstring internalPath) {
        // 2. Map the ROM file directly into memory
        struct stat st;
        if (fstat(fd, &st) < 0) {
            LOGE("Failed to stat ROM file descriptor");
            return;
        }
        gRomSize = st.st_size;

        // mmap allows us to treat the file on disk as a massive array in RAM
        gRomBaseAddress = (uint8_t*)mmap(nullptr, gRomSize, PROT_READ, MAP_PRIVATE, fd, 0);
        
        if (gRomBaseAddress == MAP_FAILED) {
            LOGE("Memory mapping failed!");
            return;
        }

        // 3. Verify ROM Integrity (Minish Cap USA/EU check)
        char gameCode[5] = {0};
        std::memcpy(gameCode, gRomBaseAddress + 0xAC, 4);

        if (std::string(gameCode).find("BZL") != 0) {
            LOGE("Invalid ROM! Found Game Code: %s", gameCode);
            munmap(gRomBaseAddress, gRomSize);
            return;
        }

        LOGI("ROM Mapped at %p. Code: %s. Size: %zu bytes", gRomBaseAddress, gameCode, gRomSize);

        // 4. Initialize the engine
        // Now when the engine accesses a GBA_PTR, RESOLVE_ROM_PTR will add the 
        // offset to gRomBaseAddress instantly.
        main_init();
    }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_onFrameTick(JNIEnv* env, jobject thiz) {
        if (gRomBaseAddress != nullptr) {
            main_step();
        }
    }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_copyFrameToBitmap(JNIEnv* env, jobject thiz, jobject bitmap) {
        void* pixels;
        if (AndroidBitmap_lockPixels(env, bitmap, &pixels) >= 0) {
            std::memcpy(pixels, g_vram, 240 * 160 * 2);
            AndroidBitmap_unlockPixels(env, bitmap);
        }
    }

    // Clean up when the activity is destroyed
    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_cleanup(JNIEnv* env, jobject thiz) {
        if (gRomBaseAddress != nullptr && gRomBaseAddress != MAP_FAILED) {
            munmap(gRomBaseAddress, gRomSize);
            gRomBaseAddress = nullptr;
        }
    }
}
