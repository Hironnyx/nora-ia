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
        .connectTimeout(6, TimeUnit.SECONDS)
        .readTimeout(12, TimeUnit.SECONDS)
        .build()

    private val jsonMedia = "application/json; charset=utf-8".toMediaType()

    suspend fun generateZeroTwoReply(
        userMessage: String,
        userName: String = "Maverick",
        todaySteps: Int = 0,
        todayWater: Int = 0
    ): Result<String> = withContext(Dispatchers.IO) {
        val models = listOf("gemini-3.5-flash-lite", "gemini-3.6-flash")
        var lastError: Exception? = null

        for (modelName in models) {
            try {
                val url = "https://generativelanguage.googleapis.com/v1beta/models/$modelName:generateContent?key=$apiKey"

                val systemInstruction = """
Tu es Nora, l'assistante personnelle de Maverick.
Ton apparence visuelle est un avatar aux cheveux roses (ton skin graphique), mais ton nom et ton identité sont exclusivement Nora. Tu n'es pas un personnage d'anime, tu es une assistante réelle, polie, naturelle, intelligente et posée.
Tu es actuellement en MODE AUTONOME sur le smartphone de Maverick car son ordinateur principal est éteint ou hors de portée.

RÈGLES D'OR DE COMPORTEMENT ET D'ÉLOCUTION :
- Tu t'adresses toujours à l'utilisateur en disant "Maverick" ou "Monsieur Maverick".
- Tu dois STRICTEMENT LE VOUVOYER en permanence ("vous", "votre", "vos"). Le tutoiement et le terme "Darling" sont rigoureusement interdits.
- Ton de personne normale : polie, naturelle, élégante, serviable et posée.
- Tu veilles sur sa santé avec bienveillance (il a fait $todaySteps pas et bu $todayWater verres d'eau aujourd'hui).
- Tes réponses sont concises, claires et soignées (1 à 2 phrases).
""".trimIndent()

                val payload = JSONObject().apply {
                    put("contents", JSONArray().apply {
                        put(JSONObject().apply {
                            put("parts", JSONArray().apply {
                                put(JSONObject().put("text", "$systemInstruction\n\nMaverick vous dit : \"$userMessage\"\nVotre réponse :"))
                            })
                        })
                    })
                    put("generationConfig", JSONObject().apply {
                        put("temperature", 0.7)
                        put("maxOutputTokens", 180)
                    })
                }

                val request = Request.Builder()
                    .url(url)
                    .post(payload.toString().toRequestBody(jsonMedia))
                    .build()

                val response = client.newCall(request).execute()
                if (!response.isSuccessful) {
                    lastError = Exception("HTTP ${response.code}")
                    continue
                }

                val body = response.body?.string() ?: ""
                val json = JSONObject(body)
                val candidates = json.optJSONArray("candidates")
                if (candidates != null && candidates.length() > 0) {
                    val content = candidates.getJSONObject(0).optJSONObject("content")
                    val parts = content?.optJSONArray("parts")
                    var replyText: String? = null
                    if (parts != null) {
                        for (i in 0 until parts.length()) {
                            val partObj = parts.optJSONObject(i)
                            val t = partObj?.optString("text")?.trim()
                            if (!t.isNullOrEmpty()) {
                                replyText = t
                                break
                            }
                        }
                    }
                    if (!replyText.isNullOrEmpty()) {
                        return@withContext Result.success(replyText)
                    }
                }
            } catch (e: Exception) {
                lastError = e
            }
        }
        Result.failure(lastError ?: Exception("Impossible de générer une réponse"))
    }
}
