#include <jni.h>
#include <unistd.h>
#include <android/log.h>
#include <vector>
#include <string>
#include "assets.h"

#define LOG_TAG "MinishNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Global Hardware Simulation
uint16_t g_vram[240 * 160];
uint8_t  g_virtual_ram[0x040000]; // Simulated IWRAM/EWRAM

extern "C" {
    void main_init(void);
    void main_step(void);
    
    // Bridge for the patched GBA headers
    uint16_t* get_virtual_reg() { return (uint16_t*)g_virtual_ram; }

    JNIEXPORT jboolean JNICALL
    Java_com_minish_ndk_MainActivity_initGameWithRom(JNIEnv* env, jobject thiz, jint fd) {
        char code[4];
        lseek(fd, 0xAC, SEEK_SET);
        read(fd, code, 4);

        if (strncmp(code, "BZL", 3) != 0) return JNI_FALSE;

        LOGI("Extracting assets for Minish Cap...");
        for (int i = 0; i < ASSET_COUNT; i++) {
            lseek(fd, g_AssetTable[i].offset, SEEK_SET);
            // In a production build, you would use mmap or a custom 
            // asset manager to load these into engine-accessible memory.
        }

        main_init();
        return JNI_TRUE;
    }

    JNIEXPORT void JNICALL
    Java_com_minish_ndk_MainActivity_onFrameTick(JNIEnv* env, jobject thiz) {
        main_step();
    }

    JNIEXPORT jobject JNICALL
    Java_com_minish_ndk_MainActivity_getVideoBuffer(JNIEnv* env, jobject thiz) {
        return env->NewDirectByteBuffer(g_vram, sizeof(g_vram));
    }
}
