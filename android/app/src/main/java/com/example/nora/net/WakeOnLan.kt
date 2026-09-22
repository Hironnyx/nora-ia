package com.example.nora.net

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

object WakeOnLan {

    const val DEFAULT_PC_MAC = "A8:A1:59:53:0D:70"
    const val DEFAULT_BROADCAST_IP = "192.168.1.255"
    const val DEFAULT_WAN_IP = "82.67.216.56"
    const val WOL_PORT = 9

    suspend fun wakePc(
        macAddress: String = DEFAULT_PC_MAC,
        broadcastIp: String = DEFAULT_BROADCAST_IP,
        wanIp: String = DEFAULT_WAN_IP
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            val cleanMac = macAddress.replace(":", "").replace("-", "")
            if (cleanMac.length != 12) {
                return@withContext Result.failure(IllegalArgumentException("Adresse MAC invalide ($macAddress)"))
            }

            val macBytes = ByteArray(6)
            for (i in 0 until 6) {
                macBytes[i] = cleanMac.substring(i * 2, i * 2 + 2).toInt(16).toByte()
            }

            // Paquet magique : 6 x 0xFF suivi de 16 x MAC address
            val bytes = ByteArray(6 + 16 * macBytes.size)
            for (i in 0 until 6) {
                bytes[i] = 0xFF.toByte()
            }
            for (i in 6 until bytes.size step macBytes.size) {
                System.arraycopy(macBytes, 0, bytes, i, macBytes.size)
            }

            // 1. Envoi sur le Wi-Fi local (192.168.1.255)
            try {
                val addressLocal = InetAddress.getByName(broadcastIp)
                val packetLocal = DatagramPacket(bytes, bytes.size, addressLocal, WOL_PORT)
                val socketLocal = DatagramSocket()
                socketLocal.broadcast = true
                socketLocal.send(packetLocal)
                socketLocal.close()
            } catch (e: Exception) {
                e.printStackTrace()
            }

            // 2. Envoi sur l'IP Publique Freebox pour réveil à distance en 4G/5G
            try {
                val addressWan = InetAddress.getByName(wanIp)
                val packetWan = DatagramPacket(bytes, bytes.size, addressWan, WOL_PORT)
                val socketWan = DatagramSocket()
                socketWan.send(packetWan)
                socketWan.close()
            } catch (e: Exception) {
                e.printStackTrace()
            }

            Result.success("Signal de réveil envoyé (Local Wi-Fi et 4G/5G WAN) !")
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
