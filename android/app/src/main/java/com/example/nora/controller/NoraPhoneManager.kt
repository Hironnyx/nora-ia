package com.example.nora.controller

import android.content.Context
import android.content.pm.PackageManager
import android.telephony.TelephonyManager
import androidx.core.content.ContextCompat

data class IncomingCallInfo(
    val phoneNumber: String,
    val contactName: String,
    val timestamp: Long
)

class NoraPhoneManager(
    private val context: Context,
    private val smsManager: SmsAndContactsManager
) {

    var isStandardisteModeActive: Boolean = true

    fun hasPhoneStatePermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            android.Manifest.permission.READ_PHONE_STATE
        ) == PackageManager.PERMISSION_GRANTED
    }

    /**
     * Génère l'annonce vocale immédiate pour Maverick dès que le téléphone sonne.
     */
    fun getCallAnnouncement(callerNameOrNumber: String): String {
        return "Monsieur Maverick, vous recevez un appel entrant de $callerNameOrNumber."
    }

    /**
     * Discours d'accueil officiel prononcé par Nora lorsqu'elle prend l'appel en tant que standardiste.
     */
    fun getStandardisteGreeting(callerName: String = ""): String {
        val callerNote = if (callerName.isNotBlank() && callerName != "Inconnu") " Bonjour $callerName." else " Bonjour."
        return "$callerNote Vous êtes bien en relation avec le secrétariat personnel de Monsieur Maverick. " +
                "Il est actuellement indisponible et ne peut vous répondre en direct. " +
                "Je suis Nora, son assistante personnelle. Quel est l'objet de votre appel ?"
    }

    /**
     * Message SMS diplomatique et professionnel expédié par Nora en cas de rejet ou d'occupation.
     */
    fun sendStandardisteSms(phoneNumber: String): Result<String> {
        val message = "Bonjour, ici Nora, l'assistante personnelle de Monsieur Maverick. " +
                "Il est actuellement retenu et n'a pu prendre votre appel. " +
                "N'hésitez pas à répondre à ce message en précisant votre demande, je la lui transmettrai immédiatement."
        return smsManager.sendSms(phoneNumber, message)
    }

    /**
     * Compte-rendu verbal fait à Maverick après la prise de message.
     */
    fun getDebriefSpeech(callerName: String, reason: String): String {
        return "Monsieur Maverick, j'ai accueilli l'appel de $callerName en tant que standardiste. Son message est le suivant : '$reason'."
    }
}
