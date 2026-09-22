package com.example.nora.service

import android.app.Notification
import android.app.RemoteInput
import android.content.Intent
import android.os.Bundle
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import java.util.concurrent.ConcurrentHashMap

data class InterceptedMessage(
    val notificationKey: String,
    val packageName: String,
    val appName: String,
    val sender: String,
    val message: String,
    val timestamp: Long,
    val canReply: Boolean
)

class NoraNotificationListenerService : NotificationListenerService() {

    companion object {
        var isServiceConnected: Boolean = false
            private set

        private val _recentMessages = mutableListOf<InterceptedMessage>()
        val recentMessages: List<InterceptedMessage>
            get() = synchronized(_recentMessages) { _recentMessages.toList() }

        private val pendingReplyActions = ConcurrentHashMap<String, Notification.Action>()

        var onMessageReceivedListener: ((InterceptedMessage) -> Unit)? = null

        fun replyToMessage(key: String, replyText: String, context: android.content.Context): Boolean {
            val action = pendingReplyActions[key] ?: return false
            val remoteInputs = action.remoteInputs ?: return false

            val intent = Intent()
            val bundle = Bundle()
            for (ri in remoteInputs) {
                bundle.putCharSequence(ri.resultKey, replyText)
            }
            RemoteInput.addResultsToIntent(remoteInputs, intent, bundle)
            try {
                action.actionIntent.send(context, 0, intent)
                return true
            } catch (e: Exception) {
                e.printStackTrace()
            }
            return false
        }
    }

    override fun onListenerConnected() {
        super.onListenerConnected()
        isServiceConnected = true
    }

    override fun onListenerDisconnected() {
        super.onListenerDisconnected()
        isServiceConnected = false
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        val pkg = sbn.packageName ?: return

        // Filtrer les messageries pertinentes (WhatsApp, Telegram, Signal, SMS, Discord)
        val isMessagingApp = pkg.contains("whatsapp") ||
                pkg.contains("telegram") ||
                pkg.contains("messaging") ||
                pkg.contains("signal") ||
                pkg.contains("mms") ||
                pkg.contains("discord") ||
                pkg.contains("android.apps.messaging")

        if (!isMessagingApp) return

        val extras = sbn.notification.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: ""
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: ""

        if (title.isBlank() || text.isBlank()) return

        // Trouver une action "Répondre" avec RemoteInput
        var replyAction: Notification.Action? = null
        sbn.notification.actions?.forEach { act ->
            if (act.remoteInputs != null && act.remoteInputs.isNotEmpty()) {
                replyAction = act
            }
        }

        val appName = when {
            pkg.contains("whatsapp") -> "WhatsApp"
            pkg.contains("telegram") -> "Telegram"
            pkg.contains("signal") -> "Signal"
            pkg.contains("discord") -> "Discord"
            else -> "SMS / Messages"
        }

        val item = InterceptedMessage(
            notificationKey = sbn.key,
            packageName = pkg,
            appName = appName,
            sender = title,
            message = text,
            timestamp = sbn.postTime,
            canReply = (replyAction != null)
        )

        if (replyAction != null) {
            pendingReplyActions[sbn.key] = replyAction!!
        }

        synchronized(_recentMessages) {
            _recentMessages.add(0, item)
            if (_recentMessages.size > 20) {
                _recentMessages.removeAt(_recentMessages.size - 1)
            }
        }

        onMessageReceivedListener?.invoke(item)
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        super.onNotificationRemoved(sbn)
        if (sbn != null) {
            pendingReplyActions.remove(sbn.key)
        }
    }
}
