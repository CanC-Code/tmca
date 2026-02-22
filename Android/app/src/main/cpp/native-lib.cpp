#include <jni.h>
#include <unistd.h>
#include <android/log.h>
#include <android/bitmap.h>
#include <vector>
#include <string>
#include <cstring>
#include <fcntl.h>
#include <sys/stat.h>
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
    Java_com_minish_ndk_MainActivity_initGameWithRom(JNIEnv* env, jobject thiz, jint fd, jstring internalPath) {
        const char* path = env->GetStringUTFChars(internalPath, nullptr);
        std::string baseDir(path);
        env->ReleaseStringUTFChars(internalPath, path);

        char gameCode[5] = {0};
        lseek(fd, 0xAC, SEEK_SET);
        if (read(fd, gameCode, 4) != 4) return;

        if (std::string(gameCode).find("BZL") != 0) {
            LOGE("Invalid ROM! Found: %s", gameCode);
            return;
        }

        LOGI("ROM Verified: %s. Extracting %d assets to %s", gameCode, ASSET_COUNT, baseDir.c_str());
        
        for (int i = 0; i < ASSET_COUNT; i++) {
            AssetMetadata asset = g_AssetTable[i];
            
            // 1. Seek ROM
            lseek(fd, asset.offset, SEEK_SET);
            std::vector<char> buffer(asset.size);
            read(fd, buffer.data(), asset.size);

            // 2. Determine output path (mirroring repo structure)
            std::string outPath = baseDir + "/" + asset.name;
            
            // 3. Simple write to internal storage
            int outFd = open(outPath.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0666);
            if (outFd != -1) {
                write(outFd, buffer.data(), asset.size);
                close(outFd);
            }
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
            std::memcpy(pixels, g_vram, 240 * 160 * 2);
            AndroidBitmap_unlockPixels(env, bitmap);
        }
    }
}
