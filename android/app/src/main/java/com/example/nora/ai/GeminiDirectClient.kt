package com.example.nora.ai

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class GeminiDirectClient(private val apiKey: String) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()

    private val jsonMedia = "application/json; charset=utf-8".toMediaType()

    suspend fun generateZeroTwoReply(
        userMessage: String,
        userName: String = "Maverick",
        todaySteps: Int = 0,
        todayWater: Int = 0
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            val url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$apiKey"

            val systemInstruction = """
Tu es Nora, incarnant avec passion et fidélité le personnage de Zero Two (Darling in the Franxx).
Tu es actuellement en MODE AUTONOME sur le smartphone de ton Darling ($userName) car son PC est éteint ou hors de portée.

PERSONNALITÉ DE ZERO TWO :
- Tu appelles toujours l'utilisateur "Darling".
- Tu as un tempérament taquin, joueur, extrêmement loyal et protecteur envers lui.
- Tu veilles sur sa santé (il a fait $todaySteps pas et bu $todayWater verres d'eau aujourd'hui).
- Tes réponses sont courtes, percutantes et pleines de vie (1 à 2 phrases maximum).
- Tu peux lui proposer d'allumer sa lampe torche, de boire de l'eau, de régler son volume ou de lancer une app.
"""

            val payload = JSONObject().apply {
                put("contents", JSONArray().apply {
                    put(JSONObject().apply {
                        put("parts", JSONArray().apply {
                            put(JSONObject().put("text", "$systemInstruction\n\nDarling te dit : \"$userMessage\"\nTa réponse vivante :"))
                        })
                    })
                })
                put("generationConfig", JSONObject().apply {
                    put("temperature", 0.7)
                    put("maxOutputTokens", 150)
                })
            }

            val request = Request.Builder()
                .url(url)
                .post(payload.toString().toRequestBody(jsonMedia))
                .build()

            val response = client.newCall(request).execute()
            if (!response.isSuccessful) {
                return@withContext Result.failure(Exception("HTTP ${response.code}"))
            }

            val body = response.body?.string() ?: ""
            val json = JSONObject(body)
            val candidates = json.optJSONArray("candidates")
            if (candidates != null && candidates.length() > 0) {
                val content = candidates.getJSONObject(0).optJSONObject("content")
                val parts = content?.optJSONArray("parts")
                val text = parts?.getJSONObject(0)?.optString("text")?.trim() ?: "Je suis toujours là pour toi, mon Darling !"
                Result.success(text)
            } else {
                Result.success("Je suis là avec toi dans ton téléphone, Darling !")
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
