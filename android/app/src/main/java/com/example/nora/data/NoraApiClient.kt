package com.example.nora.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

data class NoraAction(
    val id: String,
    val title: String,
    val icon: String,
    val category: String,
    val action: String,
    val active: Boolean
)

data class NoraOutfit(
    val id: String,
    val name: String,
    val active: Boolean
)

data class NoraCapabilities(
    val actions: List<NoraAction>,
    val outfits: List<NoraOutfit>,
    val currentOutfit: String
)

data class NoraDeviceCommand(
    val type: String,
    val action: String?,
    val value: Int?
)

data class NoraChatResponse(
    val reply: String,
    val audioUrl: String?,
    val intent: String?,
    val outfit: String?,
    val deviceCommand: NoraDeviceCommand? = null
)

data class NoraActionResponse(
    val success: Boolean,
    val reply: String,
    val audioUrl: String?,
    val deviceCommand: NoraDeviceCommand? = null
)

class NoraApiClient {
    private val client = OkHttpClient.Builder()
        .connectTimeout(4, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(8, TimeUnit.SECONDS)
        .build()

    private val jsonMedia = "application/json; charset=utf-8".toMediaType()

    private val fastClient = OkHttpClient.Builder()
        .connectTimeout(2, TimeUnit.SECONDS)
        .readTimeout(3, TimeUnit.SECONDS)
        .writeTimeout(3, TimeUnit.SECONDS)
        .build()

    suspend fun fetchRemoteTunnelEndpoint(): Result<String> = withContext(Dispatchers.IO) {
        try {
            val rawUrl = "https://raw.githubusercontent.com/Hironnyx/nora-ia/main/remote_endpoint.json?nocache=${System.currentTimeMillis()}"
            val request = Request.Builder()
                .url(rawUrl)
                .get()
                .build()
            val response = client.newCall(request).execute()
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}"))
            }
            val body = response.body?.string() ?: ""
            val json = JSONObject(body)
            val tunnelUrl = json.optString("tunnel_url")
            if (tunnelUrl.isNotBlank() && tunnelUrl.startsWith("http") && !tunnelUrl.contains("trycloudflare.com/")) {
                Result.success(tunnelUrl.trimEnd('/'))
            } else if (tunnelUrl.isNotBlank() && tunnelUrl.startsWith("http")) {
                Result.success(tunnelUrl.trimEnd('/'))
            } else {
                Result.failure(Exception("URL de tunnel vide"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun fetchCapabilities(baseUrl: String, fastCheck: Boolean = false): Result<NoraCapabilities> = withContext(Dispatchers.IO) {
        try {
            val cleanUrl = baseUrl.trimEnd('/')
            val request = Request.Builder()
                .url("$cleanUrl/api/capabilities")
                .get()
                .build()
            val activeClient = if (fastCheck) fastClient else client
            val response = activeClient.newCall(request).execute()
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}"))
            }
            val body = response.body?.string() ?: ""
            val json = JSONObject(body)
            val actionsArray = json.optJSONArray("actions") ?: JSONArray()
            val actionsList = mutableListOf<NoraAction>()
            for (i in 0 until actionsArray.length()) {
                val act = actionsArray.getJSONObject(i)
                actionsList.add(
                    NoraAction(
                        id = act.optString("id"),
                        title = act.optString("title"),
                        icon = act.optString("icon"),
                        category = act.optString("category"),
                        action = act.optString("action"),
                        active = act.optBoolean("active")
                    )
                )
            }
            val outfitsArray = json.optJSONArray("outfits") ?: JSONArray()
            val outfitsList = mutableListOf<NoraOutfit>()
            for (i in 0 until outfitsArray.length()) {
                val o = outfitsArray.getJSONObject(i)
                outfitsList.add(
                    NoraOutfit(
                        id = o.optString("id"),
                        name = o.optString("name"),
                        active = o.optBoolean("active")
                    )
                )
            }
            val currentOutfit = json.optString("current_outfit", "franxx")
            Result.success(NoraCapabilities(actionsList, outfitsList, currentOutfit))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendChat(baseUrl: String, message: String, mobileHealth: JSONObject? = null): Result<NoraChatResponse> = withContext(Dispatchers.IO) {
        try {
            val cleanUrl = baseUrl.trimEnd('/')
            val payload = JSONObject().apply {
                put("message", message)
                if (mobileHealth != null) {
                    put("mobile_health", mobileHealth)
                }
            }
            val request = Request.Builder()
                .url("$cleanUrl/api/chat")
                .post(payload.toString().toRequestBody(jsonMedia))
                .build()
            val response = client.newCall(request).execute()
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}"))
            }
            val body = response.body?.string() ?: ""
            val json = JSONObject(body)
            val reply = json.optString("reply", "Pas de réponse.")
            val audioUrl = if (json.has("audio_url") && !json.isNull("audio_url")) json.optString("audio_url") else null
            val intent = json.optString("intent")
            val outfit = json.optString("outfit")

            var devCmd: NoraDeviceCommand? = null
            val cmdObj = json.optJSONObject("device_command")
            if (cmdObj != null) {
                devCmd = NoraDeviceCommand(
                    type = cmdObj.optString("type"),
                    action = if (cmdObj.has("action")) cmdObj.optString("action") else null,
                    value = if (cmdObj.has("value")) cmdObj.optInt("value") else null
                )
            }

            Result.success(NoraChatResponse(reply, audioUrl, intent, outfit, devCmd))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendAction(baseUrl: String, actionName: String): Result<NoraActionResponse> = withContext(Dispatchers.IO) {
        try {
            val cleanUrl = baseUrl.trimEnd('/')
            val payload = JSONObject().apply { put("action", actionName) }
            val request = Request.Builder()
                .url("$cleanUrl/api/action")
                .post(payload.toString().toRequestBody(jsonMedia))
                .build()
            val response = client.newCall(request).execute()
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}"))
            }
            val body = response.body?.string() ?: ""
            val json = JSONObject(body)
            val success = json.optBoolean("success", true)
            val reply = json.optString("reply", "Action exécutée.")
            val audioUrl = if (json.has("audio_url") && !json.isNull("audio_url")) json.optString("audio_url") else null
            Result.success(NoraActionResponse(success, reply, audioUrl))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun syncHealth(baseUrl: String, healthData: JSONObject): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val cleanUrl = baseUrl.trimEnd('/')
            val request = Request.Builder()
                .url("$cleanUrl/api/health")
                .post(healthData.toString().toRequestBody(jsonMedia))
                .build()
            val response = client.newCall(request).execute()
            Result.success(response.isSuccessful)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun setOutfit(baseUrl: String, outfit: String): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val cleanUrl = baseUrl.trimEnd('/')
            val payload = JSONObject().apply { put("outfit", outfit) }
            val request = Request.Builder()
                .url("$cleanUrl/api/outfit")
                .post(payload.toString().toRequestBody(jsonMedia))
                .build()
            val response = client.newCall(request).execute()
            Result.success(response.isSuccessful)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
