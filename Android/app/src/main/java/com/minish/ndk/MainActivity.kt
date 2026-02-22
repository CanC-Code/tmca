package com.minish.ndk

import android.app.Activity
import android.content.Intent
import android.graphics.Bitmap
import android.os.Bundle
import android.view.Choreographer
import android.view.SurfaceHolder
import android.view.SurfaceView
import androidx.appcompat.app.AppCompatActivity
import java.nio.ByteBuffer
import java.nio.ByteOrder

class MainActivity : AppCompatActivity(), SurfaceHolder.Callback, Choreographer.FrameCallback {

    private lateinit var surfaceView: SurfaceView
    private lateinit var gameBitmap: Bitmap
    private lateinit var pixelBuffer: ByteBuffer
    private var isEngineRunning = false

    companion object {
        init {
            System.loadLibrary("minish_ndk")
        }
    }

    // Native Interface
    private external fun initGameWithRom(fd: Int)
    private external fun onFrameTick()
    private external fun getVideoBuffer(): Long // Returns memory address of g_vram_buffer

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Setup SurfaceView for the game screen
        surfaceView = SurfaceView(this)
        surfaceView.holder.addCallback(this)
        setContentView(surfaceView)

        // Initialize the Bitmap at GBA Resolution
        gameBitmap = Bitmap.createBitmap(240, 160, Bitmap.Config.RGB_565)
        
        pickRom()
    }

    private fun pickRom() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*" // Use generic type to ensure .gba files appear
        }
        startActivityForResult(intent, 1001)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 1001 && resultCode == Activity.RESULT_OK) {
            data?.data?.let { uri ->
                val pfd = contentResolver.openFileDescriptor(uri, "r")
                pfd?.let {
                    initGameWithRom(it.fd)
                    setupNativeBuffer()
                    isEngineRunning = true
                    Choreographer.getInstance().postFrameCallback(this)
                }
            }
        }
    }

    private fun setupNativeBuffer() {
        val address = getVideoBuffer()
        // Map the native g_vram_buffer to a Java ByteBuffer (240 * 160 * 2 bytes for RGB565)
        pixelBuffer = ByteBuffer.allocateDirect(240 * 160 * 2).apply {
            order(ByteOrder.nativeOrder())
        }
        // In a more advanced version, we would use a DirectByteBuffer 
        // to point exactly at the native C++ address.
    }

    override fun doFrame(frameTimeNanos: Long) {
        if (!isEngineRunning) return

        // 1. Trigger the native engine logic
        onFrameTick()

        // 2. Render the buffer to the screen
        renderFrame()

        // 3. Request next frame
        Choreographer.getInstance().postFrameCallback(this)
    }

    private fun renderFrame() {
        val holder = surfaceView.holder
        if (holder.surface.isValid) {
            val canvas = holder.lockCanvas()
            if (canvas != null) {
                // Transfer native pixels to Bitmap
                gameBitmap.copyPixelsFromBuffer(pixelBuffer)
                
                // Scale the 240x160 bitmap to fit the phone screen
                canvas.drawBitmap(gameBitmap, null, canvas.clipBounds, null)
                holder.unlockCanvasAndPost(canvas)
            }
        }
    }

    // SurfaceHolder Callbacks
    override fun surfaceCreated(holder: SurfaceHolder) {}
    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {}
    override fun surfaceDestroyed(holder: SurfaceHolder) { isEngineRunning = false }
}
