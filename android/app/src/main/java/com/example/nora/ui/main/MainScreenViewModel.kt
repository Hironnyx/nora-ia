package com.example.nora.ui.main

import android.app.Application
import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.nora.ai.GeminiDirectClient
import com.example.nora.audio.NoraAudioPlayer
import com.example.nora.data.NoraAction
import com.example.nora.data.NoraApiClient
import com.example.nora.data.NoraOutfit
import com.example.nora.device.DeviceController
import com.example.nora.health.HealthManager
import com.example.nora.net.WakeOnLan
import com.example.nora.notifications.NoraNotificationManager
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.Locale

data class NoraUiState(
    val serverUrl: String = "http://192.168.1.183:8000",
    val isConnected: Boolean = false,
    val isStandaloneMode: Boolean = false,
    val currentOutfit: String = "franxx",
    val spriteState: String = "idle",
    val bubbleMessage: String = "Bonjour Darling ! Je suis prête. Tu peux me parler ou piloter la maison.",
    val actions: List<NoraAction> = emptyList(),
    val outfits: List<NoraOutfit> = emptyList(),
    val isSpeaking: Boolean = false,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    // Health & Phone stats
    val todaySteps: Int = 0,
    val todayWater: Int = 0,
    val sleepHours: Float = 7.5f,
    val batteryPercent: Int = 80,
    val isFlashlightOn: Boolean = false
)

class MainScreenViewModel(application: Application) : AndroidViewModel(application) {
    private val prefs = application.getSharedPreferences("nora_prefs", Context.MODE_PRIVATE)
    private val apiClient = NoraApiClient()

    // Hardware & Device Controllers
    val deviceController = DeviceController(application)
    val healthManager = HealthManager(application)
    val notificationManager = NoraNotificationManager(application)
    private val geminiDirectClient = GeminiDirectClient("AQ.Ab8RN6LPugLNpFSWqrzBV6PkJP22OGmqPB_J_lqOwwAuh-ywPw")

    private val defaultStandaloneActions = listOf(
        NoraAction("torch", "Lampe Torche", "💡", "device", "device:flashlight", false),
        NoraAction("wol", "Réveil PC (WoL)", "⚡", "network", "device:wake_pc", false),
        NoraAction("water", "Boire un verre", "💧", "health", "health:water", false),
        NoraAction("youtube", "Lancer YouTube", "📺", "apps", "device:launch_youtube", false),
        NoraAction("spotify", "Lancer Spotify", "🎵", "apps", "device:launch_spotify", false),
        NoraAction("vibrate", "Vibrer Téléphone", "📳", "device", "device:vibrate", false)
    )

    private val _uiState = MutableStateFlow(
        NoraUiState(
            serverUrl = prefs.getString("server_url", "http://192.168.1.183:8000") ?: "http://192.168.1.183:8000",
            actions = defaultStandaloneActions,
            todaySteps = healthManager.getTodaySteps(),
            todayWater = healthManager.getTodayWater(),
            sleepHours = healthManager.getSleepHours(),
            batteryPercent = deviceController.getBatteryLevel(),
            isFlashlightOn = deviceController.isFlashlightOn()
        )
    )
    val uiState: StateFlow<NoraUiState> = _uiState.asStateFlow()

    private var lipSyncJob: Job? = null
    private var blinkJob: Job? = null
    private var telemetryJob: Job? = null
    private var tts: TextToSpeech? = null
    private var ttsReady = false

    private val audioPlayer = NoraAudioPlayer(
        onPlaybackStarted = {
            _uiState.update { it.copy(isSpeaking = true) }
            startLipSync()
        },
        onPlaybackFinished = {
            stopLipSync()
            _uiState.update { it.copy(isSpeaking = false, spriteState = "idle") }
        }
    )

    init {
        initTts(application)
        startBlinkLoop()
        startTelemetryLoop()
        refreshCapabilities()
    }

    private fun initTts(context: Context) {
        tts = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.let { engine ->
                    val result = engine.setLanguage(Locale.FRENCH)
                    if (result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED) {
                        engine.setPitch(1.15f) // Voix légèrement plus aiguë pour Zero Two
                        engine.setSpeechRate(1.02f)
                        engine.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                            override fun onStart(utteranceId: String?) {
                                _uiState.update { it.copy(isSpeaking = true) }
                                startLipSync()
                            }
                            override fun onDone(utteranceId: String?) {
                                stopLipSync()
                                _uiState.update { it.copy(isSpeaking = false, spriteState = "idle") }
                            }
                            override fun onError(utteranceId: String?) {
                                stopLipSync()
                                _uiState.update { it.copy(isSpeaking = false, spriteState = "idle") }
                            }
                        })
                        ttsReady = true
                    }
                }
            }
        }
    }

    private fun speakTts(text: String) {
        if (!ttsReady || tts == null) return
        val utteranceId = "nora_zero_two_${System.currentTimeMillis()}"
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId)
    }

    private fun startTelemetryLoop() {
        telemetryJob?.cancel()
        telemetryJob = viewModelScope.launch {
            while (isActive) {
                delay(3000)
                _uiState.update {
                    it.copy(
                        todaySteps = healthManager.getTodaySteps(),
                        todayWater = healthManager.getTodayWater(),
                        sleepHours = healthManager.getSleepHours(),
                        batteryPercent = deviceController.getBatteryLevel(),
                        isFlashlightOn = deviceController.isFlashlightOn()
                    )
                }
            }
        }
    }

    fun setServerUrl(url: String) {
        val clean = url.trim().trimEnd('/')
        prefs.edit().putString("server_url", clean).apply()
        _uiState.update { it.copy(serverUrl = clean) }
        refreshCapabilities()
    }

    fun refreshCapabilities() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            val res = apiClient.fetchCapabilities(_uiState.value.serverUrl)
            res.onSuccess { cap ->
                _uiState.update {
                    it.copy(
                        isConnected = true,
                        isStandaloneMode = false,
                        isLoading = false,
                        actions = cap.actions.ifEmpty { defaultStandaloneActions },
                        outfits = cap.outfits,
                        currentOutfit = cap.currentOutfit
                    )
                }
                // Synchronisation santé avec le PC
                syncHealthToPc()
            }.onFailure { err ->
                // PC inaccessible -> Passage transparent en Mode Autonome Téléphone
                _uiState.update {
                    it.copy(
                        isConnected = false,
                        isStandaloneMode = true,
                        isLoading = false,
                        actions = defaultStandaloneActions,
                        errorMessage = null,
                        bubbleMessage = "🌸 Je suis en Mode Autonome sur ton téléphone, Darling ! Ton PC dort ou est éteint, mais je veille toujours sur toi."
                    )
                }
            }
        }
    }

    fun toggleTorch() {
        val newState = deviceController.toggleFlashlight()
        _uiState.update { it.copy(isFlashlightOn = newState) }
        deviceController.vibrate(50)
    }

    fun addWater() {
        val current = healthManager.addWater(1)
        _uiState.update { it.copy(todayWater = current) }
        deviceController.vibrate(60)

        if (current == 8) {
            notificationManager.sendWaterReminder(current)
            _uiState.update { it.copy(bubbleMessage = "🎉 Félicitations Darling ! Tu as bu tes 8 verres d'eau recommandés aujourd'hui ! Tu es au top !") }
            if (_uiState.value.isStandaloneMode) speakTts("Félicitations Darling ! Tu as atteint tes 8 verres d'eau aujourd'hui !")
        } else {
            _uiState.update { it.copy(bubbleMessage = "💧 Bravo Darling ! Verre d'eau n°$current enregistré. Reste bien hydraté !") }
        }

        if (_uiState.value.isConnected) {
            syncHealthToPc()
        }
    }

    fun wakePc() {
        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoading = true,
                    bubbleMessage = "⚡ Envoi du Paquet Magique Wake-on-LAN au PC..."
                )
            }
            deviceController.vibrate(100)
            val result = WakeOnLan.wakePc()
            result.onSuccess { msg ->
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        bubbleMessage = "⚡ Signal de réveil envoyé au PC (RTX 4080) ! Attends 15 secondes qu'il démarre, puis touche 🔄."
                    )
                }
                if (_uiState.value.isStandaloneMode) {
                    speakTts("Signal de réveil envoyé à ton ordinateur, Darling !")
                }
            }.onFailure { err ->
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        bubbleMessage = "Erreur Wake-on-LAN : ${err.message}"
                    )
                }
            }
        }
    }

    private fun syncHealthToPc() {
        viewModelScope.launch {
            val payload = healthManager.buildSyncPayload(deviceController.getBatteryLevel())
            apiClient.syncHealth(_uiState.value.serverUrl, payload)
        }
    }

    fun sendMessage(text: String) {
        if (text.isBlank()) return
        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoading = true,
                    bubbleMessage = "⏳ Réflexion...",
                    spriteState = "listen"
                )
            }

            // Gestion des commandes directes au téléphone dans le texte
            val lower = text.lowercase().trim()
            if (lower.contains("allume la lampe") || lower.contains("allumer la torche") || lower.contains("active la torche")) {
                deviceController.setFlashlight(true)
                _uiState.update { it.copy(isFlashlightOn = true) }
            } else if (lower.contains("éteins la lampe") || lower.contains("eteindre la lampe") || lower.contains("éteindre la torche")) {
                deviceController.setFlashlight(false)
                _uiState.update { it.copy(isFlashlightOn = false) }
            } else if (lower.contains("réveille le pc") || lower.contains("allume le pc") || lower.contains("démarrer le pc")) {
                wakePc()
                return@launch
            } else if (lower.contains("j'ai bu") || lower.contains("verre d'eau") || lower.contains("boire de l'eau")) {
                addWater()
            }

            if (_uiState.value.isStandaloneMode) {
                // Mode Autonome : Appel direct à Google Gemini Flash
                val res = geminiDirectClient.generateZeroTwoReply(
                    userMessage = text,
                    todaySteps = healthManager.getTodaySteps(),
                    todayWater = healthManager.getTodayWater()
                )
                res.onSuccess { reply ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            bubbleMessage = reply
                        )
                    }
                    speakTts(reply)
                }.onFailure { err ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            spriteState = "idle",
                            bubbleMessage = "Je suis là avec toi Darling ! Même sans réseau je reste à tes côtés. 🌸"
                        )
                    }
                    speakTts("Je suis là avec toi Darling !")
                }
            } else {
                // Mode Connecté : Envoi au serveur PC avec télémétrie santé
                val healthPayload = healthManager.buildSyncPayload(deviceController.getBatteryLevel())
                val res = apiClient.sendChat(_uiState.value.serverUrl, text, healthPayload)
                res.onSuccess { reply ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            bubbleMessage = reply.reply,
                            currentOutfit = reply.outfit ?: it.currentOutfit,
                            isConnected = true
                        )
                    }

                    // Exécution des commandes matérielles renvoyées par le cerveau PC
                    reply.deviceCommand?.let { cmd ->
                        deviceController.executeDeviceCommand(cmd.type, cmd.action, cmd.value)
                        if (cmd.type == "flashlight") {
                            _uiState.update { it.copy(isFlashlightOn = deviceController.isFlashlightOn()) }
                        }
                    }

                    // Lecture audio RVC Zero Two si disponible, sinon synthèse vocale
                    reply.audioUrl?.let { audioEndpoint ->
                        val fullUrl = if (audioEndpoint.startsWith("http")) audioEndpoint else "${_uiState.value.serverUrl}$audioEndpoint"
                        audioPlayer.playStream(fullUrl)
                    } ?: run {
                        speakTts(reply.reply)
                    }
                }.onFailure { err ->
                    // Échec PC -> Basculement transparent en mode autonome
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            isConnected = false,
                            isStandaloneMode = true,
                            bubbleMessage = "Le PC ne répond plus, Darling ! Je bascule en Mode Autonome sur ton téléphone."
                        )
                    }
                    speakTts("Le PC ne répond plus, Darling ! Je prends le relais sur ton téléphone.")
                }
            }
        }
    }

    fun triggerAction(action: NoraAction) {
        viewModelScope.launch {
            // Traitement des actions locales smartphone
            when (action.action) {
                "device:flashlight" -> {
                    toggleTorch()
                    return@launch
                }
                "device:wake_pc" -> {
                    wakePc()
                    return@launch
                }
                "health:water" -> {
                    addWater()
                    return@launch
                }
                "device:launch_youtube" -> {
                    deviceController.launchApp("youtube")
                    _uiState.update { it.copy(bubbleMessage = "📺 YouTube lancé pour toi Darling !") }
                    return@launch
                }
                "device:launch_spotify" -> {
                    deviceController.launchApp("spotify")
                    _uiState.update { it.copy(bubbleMessage = "🎵 Spotify lancé pour toi Darling !") }
                    return@launch
                }
                "device:vibrate" -> {
                    deviceController.vibrate(250)
                    _uiState.update { it.copy(bubbleMessage = "📳 Bzz ! Je te tiens la main Darling !") }
                    return@launch
                }
            }

            // Si action serveur PC
            if (_uiState.value.isConnected) {
                _uiState.update {
                    it.copy(
                        isLoading = true,
                        spriteState = "work",
                        bubbleMessage = "⚙️ En cours..."
                    )
                }
                val res = apiClient.sendAction(_uiState.value.serverUrl, action.action)
                res.onSuccess { actRes ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            bubbleMessage = actRes.reply,
                            isConnected = true
                        )
                    }
                    refreshCapabilities()
                    actRes.audioUrl?.let { audioEndpoint ->
                        val fullUrl = if (audioEndpoint.startsWith("http")) audioEndpoint else "${_uiState.value.serverUrl}$audioEndpoint"
                        audioPlayer.playStream(fullUrl)
                    } ?: run {
                        _uiState.update { it.copy(spriteState = "idle") }
                    }
                }.onFailure { err ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            spriteState = "idle",
                            bubbleMessage = "Erreur : ${err.message}"
                        )
                    }
                }
            } else {
                _uiState.update {
                    it.copy(bubbleMessage = "Cette commande nécessite la connexion à ton PC (RTX 4080), Darling. Utilise ⚡ pour le réveiller !")
                }
            }
        }
    }

    fun selectOutfit(outfitId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(currentOutfit = outfitId) }
            if (_uiState.value.isConnected) {
                apiClient.setOutfit(_uiState.value.serverUrl, outfitId)
                refreshCapabilities()
            }
        }
    }

    private fun startLipSync() {
        lipSyncJob?.cancel()
        lipSyncJob = viewModelScope.launch {
            var phase = 0
            while (isActive && _uiState.value.isSpeaking) {
                val nextState = if (phase == 0) "talk_open" else "talk_closed"
                _uiState.update { it.copy(spriteState = nextState) }
                phase = 1 - phase
                delay(135)
            }
        }
    }

    private fun stopLipSync() {
        lipSyncJob?.cancel()
        lipSyncJob = null
    }

    private fun startBlinkLoop() {
        blinkJob?.cancel()
        blinkJob = viewModelScope.launch {
            while (isActive) {
                delay(3500)
                if (!_uiState.value.isSpeaking && _uiState.value.spriteState == "idle") {
                    _uiState.update { it.copy(spriteState = "blink") }
                    delay(150)
                    if (!_uiState.value.isSpeaking) {
                        _uiState.update { it.copy(spriteState = "idle") }
                    }
                }
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        audioPlayer.stop()
        tts?.stop()
        tts?.shutdown()
        lipSyncJob?.cancel()
        blinkJob?.cancel()
        telemetryJob?.cancel()
    }
}
