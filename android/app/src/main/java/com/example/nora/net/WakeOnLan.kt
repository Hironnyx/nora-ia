package com.example.nora.net

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

object WakeOnLan {

    const val DEFAULT_PC_MAC = "A8:A1:59:53:0D:70"
    const val DEFAULT_BROADCAST_IP = "192.168.1.255"
    const val WOL_PORT = 9

    suspend fun wakePc(macAddress: String = DEFAULT_PC_MAC, broadcastIp: String = DEFAULT_BROADCAST_IP): Result<String> = withContext(Dispatchers.IO) {
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

            val address = InetAddress.getByName(broadcastIp)
            val packet = DatagramPacket(bytes, bytes.size, address, WOL_PORT)
            val socket = DatagramSocket()
            socket.broadcast = true
            socket.send(packet)
            socket.close()

            Result.success("Paquet Magique Wake-on-LAN envoyé à $macAddress !")
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
