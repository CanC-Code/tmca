#include <jni.h>
#include <unistd.h>
#include <android/log.h>
#include <android/bitmap.h>
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
    #include "assets.h"

    // Engine Entry Points
    void main_init(void);
    void main_step(void);

    // Virtual Hardware Memory
    // Note: These must be accessible to the C engine files as well
    uint16_t g_vram[240 * 160];
    uint16_t g_io_regs[0x10000 / 2];

    uint16_t* get_virtual_reg() { return g_io_regs; }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_initGameWithRom(JNIEnv* env, jobject thiz, jint fd, jstring internalPath) {
        const char* path = env->GetStringUTFChars(internalPath, nullptr);
        std::string baseDir(path);
        env->ReleaseStringUTFChars(internalPath, path);

        char gameCode[5] = {0};
        lseek(fd, 0xAC, SEEK_SET);
        if (read(fd, gameCode, 4) != 4) return;

        // BZLE is the game code for Minish Cap (USA)
        if (std::string(gameCode).find("BZL") != 0) {
            LOGE("Invalid ROM! Found: %s", gameCode);
            return;
        }

        LOGI("ROM Verified: %s. Extracting %d assets to %s", gameCode, ASSET_COUNT, baseDir.c_str());
        
        for (int i = 0; i < ASSET_COUNT; i++) {
            AssetMetadata asset = g_AssetTable[i];
            
            lseek(fd, asset.offset, SEEK_SET);
            std::vector<char> buffer(asset.size);
            if (read(fd, buffer.data(), asset.size) == asset.size) {
                std::string outPath = baseDir + "/" + asset.name;
                
                // Ensure directory existence could be added here if names involve subfolders
                int outFd = open(outPath.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0666);
                if (outFd != -1) {
                    write(outFd, buffer.data(), asset.size);
                    close(outFd);
                }
            }
        }

        // Initialize the patched 64-bit engine
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
            // Copy the virtual VRAM buffer to the Android Bitmap
            std::memcpy(pixels, g_vram, 240 * 160 * 2);
            AndroidBitmap_unlockPixels(env, bitmap);
        }
    }
}
