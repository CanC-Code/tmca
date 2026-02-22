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

class MainActivity : AppCompatActivity(), SurfaceHolder.Callback, Choreographer.FrameCallback {

    private lateinit var surfaceView: SurfaceView
    private lateinit var gameBitmap: Bitmap
    private var isEngineRunning = false

    companion object {
        init {
            System.loadLibrary("minish_ndk")
        }
    }

    private external fun initGameWithRom(fd: Int)
    private external fun onFrameTick()
    private external fun copyFrameToBitmap(bitmap: Bitmap)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        surfaceView = SurfaceView(this)
        surfaceView.holder.addCallback(this)
        setContentView(surfaceView)

        // GBA native resolution
        gameBitmap = Bitmap.createBitmap(240, 160, Bitmap.Config.RGB_565)
        pickRom()
    }

    private fun pickRom() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
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
                    isEngineRunning = true
                    Choreographer.getInstance().postFrameCallback(this)
                }
            }
        }
    }

    override fun doFrame(frameTimeNanos: Long) {
        if (!isEngineRunning) return
        
        onFrameTick()
        renderToSurface()
        
        Choreographer.getInstance().postFrameCallback(this)
    }

    private fun renderToSurface() {
        val holder = surfaceView.holder
        if (holder.surface.isValid) {
            val canvas = holder.lockCanvas()
            if (canvas != null) {
                copyFrameToBitmap(gameBitmap)
                canvas.drawBitmap(gameBitmap, null, canvas.clipBounds, null)
                holder.unlockCanvasAndPost(canvas)
            }
        }
    }

    override fun surfaceCreated(holder: SurfaceHolder) {}
    override fun surfaceChanged(holder: SurfaceHolder, f: Int, w: Int, h: Int) {}
    override fun surfaceDestroyed(holder: SurfaceHolder) { isEngineRunning = false }
}
