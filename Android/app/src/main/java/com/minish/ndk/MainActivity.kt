package com.minish.ndk

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    companion object {
        init {
            System.loadLibrary("minish_ndk")
        }
    }

    private external fun initGameWithRom(fd: Int)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        pickRom()
    }

    private fun pickRom() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "application/octet-stream" // Generic for .gba
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
                }
            }
        }
    }
}
