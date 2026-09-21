package com.example.nora.device

import android.content.Context
import android.content.Intent
import android.hardware.camera2.CameraAccessException
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.media.AudioManager
import android.os.BatteryManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager

class DeviceController(private val context: Context) {

    private val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as? CameraManager
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
    private var isTorchOn = false

    fun isFlashlightOn(): Boolean = isTorchOn

    fun setFlashlight(enabled: Boolean): Boolean {
        if (cameraManager == null) return false
        return try {
            val cameraId = cameraManager.cameraIdList.firstOrNull { id ->
                val characteristics = cameraManager.getCameraCharacteristics(id)
                characteristics.get(CameraCharacteristics.FLASH_INFO_AVAILABLE) == true
            } ?: cameraManager.cameraIdList.firstOrNull() ?: return false

            cameraManager.setTorchMode(cameraId, enabled)
            isTorchOn = enabled
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    fun toggleFlashlight(): Boolean {
        return setFlashlight(!isTorchOn)
    }

    fun setVolumePercent(percent: Int) {
        audioManager?.let { am ->
            val maxVol = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
            val target = ((percent.coerceIn(0, 100) / 100f) * maxVol).toInt()
            am.setStreamVolume(AudioManager.STREAM_MUSIC, target, AudioManager.FLAG_SHOW_UI)
        }
    }

    fun getBatteryLevel(): Int {
        val bm = context.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
        return bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: 80
    }

    fun vibrate(durationMs: Long = 120) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                vm?.defaultVibrator?.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                val v = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                v?.vibrate(durationMs)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun launchApp(appNameOrPackage: String): Boolean {
        val pm = context.packageManager
        val clean = appNameOrPackage.lowercase().trim()

        val knownPackages = mapOf(
            "spotify" to "com.spotify.music",
            "youtube" to "com.google.android.youtube",
            "whatsapp" to "com.whatsapp",
            "maps" to "com.google.android.apps.maps",
            "chrome" to "com.android.chrome",
            "photos" to "com.google.android.apps.photos",
            "netflix" to "com.netflix.mediaclient",
            "instagram" to "com.instagram.android",
            "discord" to "com.discord"
        )

        val targetPkg = knownPackages[clean] ?: clean

        val intent = pm.getLaunchIntentForPackage(targetPkg)
        if (intent != null) {
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            return true
        }

        // Recherche par nom d'application
        val apps = pm.getInstalledApplications(0)
        for (app in apps) {
            val label = pm.getApplicationLabel(app).toString().lowercase()
            if (label.contains(clean)) {
                val foundIntent = pm.getLaunchIntentForPackage(app.packageName)
                if (foundIntent != null) {
                    foundIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    context.startActivity(foundIntent)
                    return true
                }
            }
        }
        return false
    }

    fun executeDeviceCommand(type: String, action: String?, value: Int?): String {
        return when (type) {
            "flashlight" -> {
                val enable = action == "on" || action == "toggle" && !isTorchOn
                val ok = setFlashlight(enable)
                if (ok) "Lampe torche ${if (enable) "allumée" else "éteinte"}" else "Erreur torche"
            }
            "volume" -> {
                val v = value ?: 50
                setVolumePercent(v)
                "Volume du téléphone réglé à $v%"
            }
            "launch_app" -> {
                val pkg = action ?: ""
                val ok = launchApp(pkg)
                if (ok) "Application $pkg ouverte" else "Impossible de trouver $pkg"
            }
            "vibrate" -> {
                vibrate(150)
                "Vibration effectuée"
            }
            else -> "Commande inconnue"
        }
    }
}
