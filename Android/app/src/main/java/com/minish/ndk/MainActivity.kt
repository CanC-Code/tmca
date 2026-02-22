package com.minish.ndk

import android.app.Activity
import android.content.Intent
import android.graphics.Bitmap
import android.os.Bundle
import android.view.Choreographer
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import java.nio.ByteBuffer

class MainActivity : AppCompatActivity(), SurfaceHolder.Callback, Choreographer.FrameCallback {

    private lateinit var surfaceView: SurfaceView
    private var gameBitmap = Bitmap.createBitmap(240, 160, Bitmap.Config.RGB_565)
    private var isEngineRunning = false

    companion object {
        init {
            System.loadLibrary("minish_ndk")
        }
    }

    private external fun initGameWithRom(fd: Int): Boolean
    private external fun onFrameTick()
    private external fun getVideoBuffer(): ByteBuffer

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        surfaceView = SurfaceView(this)
        surfaceView.holder.addCallback(this)
        setContentView(surfaceView)
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
                if (pfd != null) {
                    if (initGameWithRom(pfd.fd)) {
                        isEngineRunning = true
                        Choreographer.getInstance().postFrameCallback(this)
                    } else {
                        Toast.makeText(this, "Invalid ROM provided", Toast.LENGTH_LONG).show()
                    }
                }
            }
        }
    }

    override fun doFrame(frameTimeNanos: Long) {
        if (!isEngineRunning) return
        onFrameTick()
        val holder = surfaceView.holder
        if (holder.surface.isValid) {
            val canvas = holder.lockCanvas()
            canvas?.let {
                gameBitmap.copyPixelsFromBuffer(getVideoBuffer())
                it.drawBitmap(gameBitmap, null, it.clipBounds, null)
                holder.unlockCanvasAndPost(it)
            }
        }
        Choreographer.getInstance().postFrameCallback(this)
    }

    override fun surfaceCreated(holder: SurfaceHolder) {}
    override fun surfaceChanged(holder: SurfaceHolder, f: Int, w: Int, h: Int) {}
    override fun surfaceDestroyed(holder: SurfaceHolder) { isEngineRunning = false }
}
