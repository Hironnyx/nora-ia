package com.example.nora.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

class NoraNotificationManager(private val context: Context) {

    companion object {
        const val CHANNEL_ID = "nora_health_channel"
        const val CHANNEL_NAME = "Nora - Santé & Bien-Être"
    }

    init {
        createChannel()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val importance = NotificationManager.IMPORTANCE_DEFAULT
            val channel = NotificationChannel(CHANNEL_ID, CHANNEL_NAME, importance).apply {
                description = "Rappels d'hydratation, suivi des pas et alertes santé de Nora"
            }
            val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
            nm?.createNotificationChannel(channel)
        }
    }

    fun sendNoraNotification(title: String, message: String, notificationId: Int = 101) {
        try {
            val builder = NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(message)
                .setStyle(NotificationCompat.BigTextStyle().bigText(message))
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                .setAutoCancel(true)

            val nm = NotificationManagerCompat.from(context)
            nm.notify(notificationId, builder.build())
        } catch (e: SecurityException) {
            // Permission POST_NOTIFICATIONS non accordée par l'utilisateur
            e.printStackTrace()
        }
    }

    fun sendWaterReminder(currentGlasses: Int) {
        sendNoraNotification(
            "💧 Rappel Hydratation Nora",
            "Monsieur Maverick, pensez à vous hydrater. Vous en êtes à $currentGlasses/8 verres aujourd'hui. Prenez soin de vous. 🌸",
            102
        )
    }

    fun sendStepGoalCongratulations(steps: Int) {
        sendNoraNotification(
            "🎉 Objectif de Pas Validé !",
            "Félicitations Maverick ! Vous avez atteint $steps pas aujourd'hui ! C'est une excellente performance. 🚀",
            103
        )
    }
}
