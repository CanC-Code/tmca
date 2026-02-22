#include <jni.h>
#include <string>
#include <unistd.h>
#include <android/log.h>
#include <fcntl.h>
#include <vector>
#include "assets.h" 

#define LOG_TAG "MinishNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Global state for the Virtual GBA hardware
uint16_t g_vram_buffer[240 * 160];
uint16_t g_virtual_regs[0x10000]; // Fake IO Register space

extern "C" {
    // Signatures from the patched tmca/src/main.c
    void main_init(void);
    void main_step(void);

    // This is called by the patched GBA headers in include/gba/io_reg.h
    uint16_t* get_virtual_reg() {
        return g_virtual_regs;
    }

    // This bridges the engine's tile/palette data to our Android buffer
    void UpdateVideo(uint16_t* buffer) {
        // In a full implementation, this would iterate through the game's 
        // internal OAM and Background layers and compose them into 'buffer'.
        // For now, we'll keep it as a placeholder to allow the build to pass.
    }
}

void ExtractAssets(int fd) {
    LOGI("Starting extraction of %d assets...", ASSET_COUNT);
    for (int i = 0; i < ASSET_COUNT; i++) {
        AssetMetadata asset = g_AssetTable[i];
        if (lseek(fd, asset.offset, SEEK_SET) == -1) continue;
        
        std::vector<char> buffer(asset.size);
        read(fd, buffer.data(), asset.size);
    }
    LOGI("Extraction complete.");
}

extern "C" {

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_initGameWithRom(JNIEnv* env, jobject thiz, jint fd) {
        char gameCode[5] = {0};
        lseek(fd, 0xAC, SEEK_SET);
        if (read(fd, gameCode, 4) != 4) return;

        if (std::string(gameCode).find("BZL") != 0) {
            LOGE("Validation Failed: %s", gameCode);
            return;
        }

        LOGI("ROM Validated: %s. Initializing...", gameCode);
        ExtractAssets(fd);
        
        // Uncomment once prepare_source.py has run on the runner
        // main_init(); 
    }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_onFrameTick(JNIEnv* env, jobject thiz) {
        // main_step();
        UpdateVideo(g_vram_buffer);
    }

    // Changed jpointer to jlong for standard JNI compatibility
    JNIEXPORT jlong JNICALL
    Java_com_minish_ndk_MainActivity_getVideoBuffer(JNIEnv* env, jobject thiz) {
        return (jlong)g_vram_buffer;
    }
}
