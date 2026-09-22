package com.example.nora.controller

import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.ContactsContract
import android.provider.Telephony
import android.telephony.SmsManager
import androidx.core.content.ContextCompat

data class SmsMessageItem(
    val address: String,
    val senderName: String,
    val body: String,
    val date: Long
)

class SmsAndContactsManager(private val context: Context) {

    fun hasSmsPermissions(): Boolean {
        val send = ContextCompat.checkSelfPermission(context, android.Manifest.permission.SEND_SMS) == PackageManager.PERMISSION_GRANTED
        val read = ContextCompat.checkSelfPermission(context, android.Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED
        return send && read
    }

    fun hasContactsPermission(): Boolean {
        return ContextCompat.checkSelfPermission(context, android.Manifest.permission.READ_CONTACTS) == PackageManager.PERMISSION_GRANTED
    }

    fun resolveContactNumber(nameOrNumber: String): String {
        val clean = nameOrNumber.trim()
        if (clean.matches(Regex("^[+0-9 ]+$"))) {
            return clean.replace(" ", "")
        }

        if (!hasContactsPermission()) return clean

        try {
            val uri = ContactsContract.CommonDataKinds.Phone.CONTENT_URI
            val projection = arrayOf(
                ContactsContract.CommonDataKinds.Phone.NUMBER,
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME
            )
            val selection = "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?"
            val selectionArgs = arrayOf("%$clean%")

            context.contentResolver.query(uri, projection, selection, selectionArgs, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val numIndex = cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER)
                    if (numIndex >= 0) {
                        return cursor.getString(numIndex).replace(" ", "")
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return clean
    }

    fun resolveContactName(phoneNumber: String): String {
        if (!hasContactsPermission()) return phoneNumber
        try {
            val uri = Uri.withAppendedPath(ContactsContract.PhoneLookup.CONTENT_FILTER_URI, Uri.encode(phoneNumber))
            val projection = arrayOf(ContactsContract.PhoneLookup.DISPLAY_NAME)
            context.contentResolver.query(uri, projection, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val nameIdx = cursor.getColumnIndex(ContactsContract.PhoneLookup.DISPLAY_NAME)
                    if (nameIdx >= 0) {
                        return cursor.getString(nameIdx)
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return phoneNumber
    }

    fun sendSms(contactOrNumber: String, messageText: String): Result<String> {
        if (!hasSmsPermissions()) {
            return Result.failure(SecurityException("Autorisation SMS non accordée. Veuillez l'activer dans les Paramètres Android."))
        }
        return try {
            val number = resolveContactNumber(contactOrNumber)
            val smsMgr: SmsManager = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
                context.getSystemService(SmsManager::class.java)
            } else {
                @Suppress("DEPRECATION")
                SmsManager.getDefault()
            }
            smsMgr.sendTextMessage(number, null, messageText, null, null)
            Result.success("Message envoyé à $contactOrNumber ($number), Maverick.")
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun getRecentSms(limit: Int = 3): List<SmsMessageItem> {
        val list = mutableListOf<SmsMessageItem>()
        if (!hasSmsPermissions()) return list

        try {
            val uri = Telephony.Sms.Inbox.CONTENT_URI
            val projection = arrayOf(
                Telephony.Sms.Inbox.ADDRESS,
                Telephony.Sms.Inbox.BODY,
                Telephony.Sms.Inbox.DATE
            )
            context.contentResolver.query(uri, projection, null, null, "${Telephony.Sms.Inbox.DATE} DESC")?.use { cursor ->
                val addrIdx = cursor.getColumnIndex(Telephony.Sms.Inbox.ADDRESS)
                val bodyIdx = cursor.getColumnIndex(Telephony.Sms.Inbox.BODY)
                val dateIdx = cursor.getColumnIndex(Telephony.Sms.Inbox.DATE)

                var count = 0
                while (cursor.moveToNext() && count < limit) {
                    val addr = if (addrIdx >= 0) cursor.getString(addrIdx) ?: "" else ""
                    val body = if (bodyIdx >= 0) cursor.getString(bodyIdx) ?: "" else ""
                    val date = if (dateIdx >= 0) cursor.getLong(dateIdx) else 0L
                    val name = resolveContactName(addr)
                    list.add(SmsMessageItem(addr, name, body, date))
                    count++
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return list
    }
}
