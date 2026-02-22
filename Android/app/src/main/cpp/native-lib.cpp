#include <jni.h>
#include <unistd.h>
#include <android/log.h>
#include <android/bitmap.h>
#include <vector>
#include <string>
#include <cstring>
#include <fcntl.h>
#include "assets.h"

#define LOG_TAG "MinishNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Virtual Hardware Memory
uint16_t g_vram[240 * 160];
uint16_t g_io_regs[0x10000 / 2];

extern "C" {
    void main_init(void);
    void main_step(void);

    uint16_t* get_virtual_reg() { return g_io_regs; }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_initGameWithRom(JNIEnv* env, jobject thiz, jint fd) {
        char gameCode[5] = {0};
        lseek(fd, 0xAC, SEEK_SET);
        if (read(fd, gameCode, 4) != 4) return;

        if (std::string(gameCode).find("BZL") != 0) {
            LOGE("Invalid ROM! Found: %s", gameCode);
            return;
        }

        LOGI("ROM Verified: %s. Processing %d assets...", gameCode, ASSET_COUNT);
        
        for (int i = 0; i < ASSET_COUNT; i++) {
            AssetMetadata asset = g_AssetTable[i];
            lseek(fd, asset.offset, SEEK_SET);
            
            // To make this functional, you would typically write 'asset.size' bytes 
            // from 'fd' into a new file in the app's internal storage path.
            // Example: write_to_internal_storage(asset.name, fd, asset.size);
        }

        main_init();
    }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_onFrameTick(JNIEnv* env, jobject thiz) {
        main_step();
    }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_copyFrameToBitmap(JNIEnv* env, jobject thiz, jobject bitmap) {
        void* pixels;
        if (AndroidBitmap_lockPixels(env, bitmap, &pixels) >= 0) {
            // GBA is 240x160 RGB565. Direct memory copy to Android Bitmap.
            std::memcpy(pixels, g_vram, 240 * 160 * 2);
            AndroidBitmap_unlockPixels(env, bitmap);
        }
    }
}
