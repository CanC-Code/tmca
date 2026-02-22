#include <jni.h>
#include <unistd.h>
#include <android/log.h>
#include <android/bitmap.h>
#include <vector>
#include <string>
#include "assets.h"

#define LOG_TAG "MinishNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Virtual Hardware State
uint16_t g_vram[240 * 160];
uint16_t g_io_regs[0x10000 / 2];

extern "C" {
    void main_init(void);
    void main_step(void);

    // Patched header support
    uint16_t* get_virtual_reg() { return g_io_regs; }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_initGameWithRom(JNIEnv* env, jobject thiz, jint fd) {
        char code[5] = {0};
        lseek(fd, 0xAC, SEEK_SET);
        read(fd, code, 4);

        if (std::string(code).find("BZL") == 0) {
            LOGI("Valid Minish Cap ROM: %s", code);
            // Extraction Loop using assets.h metadata
            for (int i = 0; i < ASSET_COUNT; i++) {
                lseek(fd, g_AssetTable[i].offset, SEEK_SET);
                // Here you'd store to internal app storage
            }
            main_init();
        }
    }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_onFrameTick(JNIEnv* env, jobject thiz) {
        main_step();
    }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_copyFrameToBitmap(JNIEnv* env, jobject thiz, jobject bitmap) {
        void* pixels;
        if (AndroidBitmap_lockPixels(env, bitmap, &pixels) >= 0) {
            memcpy(pixels, g_vram, sizeof(g_vram));
            AndroidBitmap_unlockPixels(env, bitmap);
        }
    }
}
