package com.example.nora.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.TelephonyManager
import com.example.nora.controller.SmsAndContactsManager

class NoraCallReceiver : BroadcastReceiver() {

    companion object {
        var onIncomingCallListener: ((phoneNumber: String, contactName: String) -> Unit)? = null
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == TelephonyManager.ACTION_PHONE_STATE_CHANGED) {
            val state = intent.getStringExtra(TelephonyManager.EXTRA_STATE)
            if (state == TelephonyManager.EXTRA_STATE_RINGING) {
                val incomingNumber = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER) ?: "Numéro masqué"
                val smsManager = SmsAndContactsManager(context)
                val contactName = if (incomingNumber != "Numéro masqué") {
                    smsManager.resolveContactName(incomingNumber)
                } else {
                    "Numéro masqué"
                }
                onIncomingCallListener?.invoke(incomingNumber, contactName)
            }
        }
    }
}
