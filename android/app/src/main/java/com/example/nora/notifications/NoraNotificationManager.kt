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
                description = "Rappels d'hydratation, suivi des pas et alertes santé de Zero Two"
            }
            val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
            nm?.createNotificationChannel(channel)
        }
    }

    fun sendZeroTwoNotification(title: String, message: String, notificationId: Int = 101) {
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
        sendZeroTwoNotification(
            "💧 Rappel Hydratation Zero Two",
            "Darling, bois une gorgée d'eau fraîche ! Tu en es à $currentGlasses/8 verres aujourd'hui. Prends soin de toi ! 🌸",
            102
        )
    }

    fun sendStepGoalCongratulations(steps: Int) {
        sendZeroTwoNotification(
            "🎉 Objectif de Pas Validé !",
            "Incroyable Darling ! Tu as déjà atteint $steps pas ! Je suis fière de mon pilote ! 🚀",
            103
        )
    }
}
