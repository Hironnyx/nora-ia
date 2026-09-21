package com.example.nora.audio

import android.media.AudioAttributes
import android.media.MediaPlayer
import android.util.Log

class NoraAudioPlayer(
    private val onPlaybackStarted: () -> Unit = {},
    private val onPlaybackFinished: () -> Unit = {}
) {
    private var mediaPlayer: MediaPlayer? = null

    fun playStream(url: String) {
        stop()
        try {
            mediaPlayer = MediaPlayer().apply {
                setAudioAttributes(
                    AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .setUsage(AudioAttributes.USAGE_ASSISTANT)
                        .build()
                )
                setDataSource(url)
                setOnPreparedListener { mp ->
                    mp.start()
                    onPlaybackStarted()
                }
                setOnCompletionListener {
                    onPlaybackFinished()
                    release()
                    mediaPlayer = null
                }
                setOnErrorListener { _, what, extra ->
                    Log.e("NoraAudioPlayer", "Erreur lecture audio: what=$what, extra=$extra")
                    onPlaybackFinished()
                    true
                }
                prepareAsync()
            }
        } catch (e: Exception) {
            Log.e("NoraAudioPlayer", "Exception lancement audio", e)
            onPlaybackFinished()
        }
    }

    fun stop() {
        try {
            mediaPlayer?.let {
                if (it.isPlaying) {
                    it.stop()
                }
                it.release()
            }
        } catch (e: Exception) {
            // Ignorer
        } finally {
            mediaPlayer = null
            onPlaybackFinished()
        }
    }
}
