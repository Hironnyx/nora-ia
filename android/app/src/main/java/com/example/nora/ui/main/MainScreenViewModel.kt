package com.example.nora.ui.main

import android.app.Application
import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.nora.ai.GeminiDirectClient
import com.example.nora.audio.NoraAudioPlayer
import com.example.nora.controller.NoraPhoneManager
import com.example.nora.controller.SmsAndContactsManager
import com.example.nora.data.NoraAction
import com.example.nora.data.NoraApiClient
import com.example.nora.data.NoraOutfit
import com.example.nora.device.DeviceController
import com.example.nora.health.HealthManager
import com.example.nora.net.WakeOnLan
import com.example.nora.notifications.NoraNotificationManager
import com.example.nora.receiver.NoraCallReceiver
import com.example.nora.service.NoraNotificationListenerService
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
    val localServerUrl: String = "http://192.168.1.183:8000",
    val remoteServerUrl: String? = null,
    val isConnected: Boolean = false,
    val isStandaloneMode: Boolean = false,
    val connectionType: String = "none", // "local" (Wi-Fi maison), "remote" (4G/5G Cloudflare), "autonomous" (PC éteint)
    val currentOutfit: String = "franxx",
    val spriteState: String = "idle",
    val bubbleMessage: String = "Bonjour Maverick ! Je suis à votre service. Vous pouvez me parler, consulter vos messages ou piloter vos équipements.",
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

    // Hardware, Communications & Device Controllers
    val deviceController = DeviceController(application)
    val healthManager = HealthManager(application)
    val notificationManager = NoraNotificationManager(application)
    val smsManager = SmsAndContactsManager(application)
    val phoneManager = NoraPhoneManager(application, smsManager)
    private val geminiDirectClient = GeminiDirectClient("AQ.Ab8RN6LPugLNpFSWqrzBV6PkJP22OGmqPB_J_lqOwwAuh-ywPw")

    private val defaultStandaloneActions = listOf(
        NoraAction("emails", "Mes Mails 📧", "📧", "comms", "comms:emails", false),
        NoraAction("read_sms", "Lire SMS 📨", "📨", "comms", "comms:read_sms", false),
        NoraAction("standardiste", "Standardiste 👩‍💼", "👩‍💼", "comms", "comms:standardiste", false),
        NoraAction("torch", "Lampe Torche", "💡", "device", "device:flashlight", false),
        NoraAction("wol", "Réveil PC (WoL)", "⚡", "network", "device:wake_pc", false),
        NoraAction("water", "Boire un verre", "💧", "health", "health:water", false),
        NoraAction("patrimoine", "Bilan Patrimoine 💎", "💎", "finance", "finance:patrimoine", false),
        NoraAction("crypto", "Marché Crypto (BTC)", "🪙", "finance", "finance:crypto", false),
        NoraAction("bourse", "Bourse & ETF", "📈", "finance", "finance:bourse", false),
        NoraAction("budget", "Comptes Bancaires", "🏦", "finance", "finance:budget", false),
        NoraAction("youtube", "Lancer YouTube", "📺", "apps", "device:launch_youtube", false),
        NoraAction("spotify", "Lancer Spotify", "🎵", "apps", "device:launch_spotify", false),
        NoraAction("vibrate", "Vibrer Téléphone", "📳", "device", "device:vibrate", false)
    )

    private val _uiState = MutableStateFlow(
        NoraUiState(
            serverUrl = prefs.getString("server_url", "http://192.168.1.183:8000") ?: "http://192.168.1.183:8000",
            localServerUrl = prefs.getString("local_server_url", "http://192.168.1.183:8000") ?: "http://192.168.1.183:8000",
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

    private val connectivityManager = application.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
    private val networkCallback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) {
            viewModelScope.launch {
                delay(1200)
                refreshCapabilities()
            }
        }
        override fun onLost(network: Network) {
            viewModelScope.launch {
                delay(1200)
                refreshCapabilities()
            }
        }
    }

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
        registerNetworkWatcher()
        registerCommsReceivers()
        refreshCapabilities()
    }

    private fun registerCommsReceivers() {
        NoraCallReceiver.onIncomingCallListener = { number, contact ->
            viewModelScope.launch {
                val displayName = if (contact.isNotBlank() && contact != "Numéro masqué") contact else number
                val announcement = phoneManager.getCallAnnouncement(displayName)
                _uiState.update { it.copy(bubbleMessage = "📞 Appel entrant : $displayName ($number)") }
                speakTts(announcement)
            }
        }

        NoraNotificationListenerService.onMessageReceivedListener = { msg ->
            viewModelScope.launch {
                _uiState.update {
                    it.copy(bubbleMessage = "💬 Message de ${msg.sender} (${msg.appName}) : \"${msg.message}\"")
                }
            }
        }
    }

    private fun registerNetworkWatcher() {
        try {
            connectivityManager?.registerDefaultNetworkCallback(networkCallback)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun initTts(context: Context) {
        tts = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.let { engine ->
                    val result = engine.setLanguage(Locale.FRENCH)
                    if (result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED) {
                        engine.setPitch(1.15f)
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
        prefs.edit().putString("local_server_url", clean).apply()
        _uiState.update { it.copy(serverUrl = clean, localServerUrl = clean) }
        refreshCapabilities()
    }

    /**
     * Algorithme de Routage Intelligent & Automatique :
     * 1. Test rapide du Wi-Fi Maison (Local) : 192.168.1.183 (latence < 2s)
     * 2. Si échec (passage en 4G/5G dehors) : Découverte automatique du tunnel Cloudflare sur GitHub
     * 3. Si échec (PC éteint) : Passage en Mode Autonome Smartphone (Gemini Direct)
     */
    fun refreshCapabilities() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            val localUrl = _uiState.value.localServerUrl

            // Étape 1 : Vérification Wi-Fi local rapide
            val localRes = apiClient.fetchCapabilities(localUrl, fastCheck = true)
            if (localRes.isSuccess) {
                val cap = localRes.getOrNull()!!
                _uiState.update {
                    it.copy(
                        isConnected = true,
                        isStandaloneMode = false,
                        connectionType = "local",
                        serverUrl = localUrl,
                        isLoading = false,
                        actions = cap.actions.ifEmpty { defaultStandaloneActions },
                        outfits = cap.outfits,
                        currentOutfit = cap.currentOutfit
                    )
                }
                syncHealthToPc()
                return@launch
            }

            // Étape 2 : Passage automatique au tunnel sécurisé 4G/5G Cloudflare
            val remoteRes = apiClient.fetchRemoteTunnelEndpoint()
            if (remoteRes.isSuccess) {
                val tunnelUrl = remoteRes.getOrNull()!!
                val tunnelCapRes = apiClient.fetchCapabilities(tunnelUrl, fastCheck = false)
                if (tunnelCapRes.isSuccess) {
                    val cap = tunnelCapRes.getOrNull()!!
                    _uiState.update {
                        it.copy(
                            isConnected = true,
                            isStandaloneMode = false,
                            connectionType = "remote",
                            serverUrl = tunnelUrl,
                            remoteServerUrl = tunnelUrl,
                            isLoading = false,
                            actions = cap.actions.ifEmpty { defaultStandaloneActions },
                            outfits = cap.outfits,
                            currentOutfit = cap.currentOutfit,
                            bubbleMessage = "🌐 Connectée à votre PC en 4G/5G via le tunnel sécurisé Cloudflare, Maverick !"
                        )
                    }
                    syncHealthToPc()
                    return@launch
                }
            }

            // Étape 3 : PC inaccessible ou éteint -> Mode Autonome Smartphone
            _uiState.update {
                it.copy(
                    isConnected = false,
                    isStandaloneMode = true,
                    connectionType = "autonomous",
                    isLoading = false,
                    actions = defaultStandaloneActions,
                    errorMessage = null,
                    bubbleMessage = "🌸 Je suis en Mode Autonome sur votre téléphone, Maverick. Votre PC est éteint ou inaccessible, mais je reste à votre disposition."
                )
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
            _uiState.update { it.copy(bubbleMessage = "🎉 Félicitations Maverick ! Vous avez bu vos 8 verres d'eau recommandés aujourd'hui ! C'est parfait !") }
            if (_uiState.value.isStandaloneMode) speakTts("Félicitations Maverick ! Vous avez atteint vos 8 verres d'eau aujourd'hui !")
        } else {
            _uiState.update { it.copy(bubbleMessage = "💧 Bravo Maverick ! Verre d'eau n°$current enregistré. Pensez à bien vous hydrater.") }
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
                        bubbleMessage = "⚡ Signal de réveil envoyé au PC (RTX 4080) ! Attendez quelques secondes qu'il démarre, puis touchez 🔄."
                    )
                }
                if (_uiState.value.isStandaloneMode) {
                    speakTts("Signal de réveil envoyé à votre ordinateur, Maverick !")
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
                            bubbleMessage = "Je suis à vos côtés, Maverick. Même sans réseau, je reste opérationnelle. 🌸"
                        )
                    }
                    speakTts("Je suis à votre disposition, Maverick.")
                }
            } else {
                // Mode Connecté : Envoi au serveur PC (Local ou 4G/5G Tunnel)
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

                    // Exécution des commandes matérielles & téléphoniques renvoyées par le cerveau PC
                    reply.deviceCommand?.let { cmd ->
                        when (cmd.type) {
                            "sms", "send_sms" -> {
                                val target = cmd.contact ?: (cmd.value?.toString() ?: "")
                                val body = cmd.body ?: ""
                                if (target.isNotBlank() && body.isNotBlank()) {
                                    val result = smsManager.sendSms(target, body)
                                    result.onSuccess { msg ->
                                        _uiState.update { it.copy(bubbleMessage = msg) }
                                    }.onFailure { err ->
                                        _uiState.update { it.copy(bubbleMessage = "Échec d'envoi du SMS : ${err.message}") }
                                    }
                                }
                            }
                            "read_sms" -> {
                                val recent = smsManager.getRecentSms(3)
                                if (recent.isEmpty()) {
                                    val emptyMsg = "Aucun SMS récent trouvé sur votre téléphone, Maverick."
                                    _uiState.update { it.copy(bubbleMessage = emptyMsg) }
                                    speakTts(emptyMsg)
                                } else {
                                    val sb = StringBuilder("Derniers SMS reçus :\n")
                                    recent.forEach { item ->
                                        sb.append("• ${item.senderName} : \"${item.body}\"\n")
                                    }
                                    val text = sb.toString().trim()
                                    _uiState.update { it.copy(bubbleMessage = text) }
                                    speakTts("Vous avez un SMS de ${recent.first().senderName}.")
                                }
                            }
                            "standardiste", "call_standardiste" -> {
                                val active = if (cmd.action != null) {
                                    cmd.action == "enable" || cmd.action == "start" || cmd.action == "on"
                                } else {
                                    true
                                }
                                phoneManager.isStandardisteModeActive = active
                                val statusText = if (active) {
                                    "Mode Standardiste activé, Maverick. Je gère vos appels entrants."
                                } else {
                                    "Mode Standardiste désactivé, Maverick."
                                }
                                _uiState.update { it.copy(bubbleMessage = statusText) }
                            }
                            else -> {
                                deviceController.executeDeviceCommand(cmd.type, cmd.action, cmd.value)
                                if (cmd.type == "flashlight") {
                                    _uiState.update { it.copy(isFlashlightOn = deviceController.isFlashlightOn()) }
                                }
                            }
                        }
                    }

                    // Lecture audio RVC Nora si disponible, sinon synthèse vocale
                    reply.audioUrl?.let { audioEndpoint ->
                        val fullUrl = if (audioEndpoint.startsWith("http")) audioEndpoint else "${_uiState.value.serverUrl}$audioEndpoint"
                        audioPlayer.playStream(fullUrl)
                    } ?: run {
                        speakTts(reply.reply)
                    }
                }.onFailure { err ->
                    // Re-tentative immédiate de réconciliation réseau
                    refreshCapabilities()
                }
            }
        }
    }

    fun triggerAction(action: NoraAction) {
        viewModelScope.launch {
            // Traitement des actions locales smartphone & communications
            when (action.action) {
                "comms:emails" -> {
                    sendMessage("Résume-moi mes derniers emails")
                    return@launch
                }
                "comms:read_sms" -> {
                    val recent = smsManager.getRecentSms(3)
                    if (recent.isEmpty()) {
                        val emptyMsg = "Aucun SMS récent trouvé, Maverick."
                        _uiState.update { it.copy(bubbleMessage = emptyMsg) }
                        speakTts(emptyMsg)
                    } else {
                        val sb = StringBuilder("Voici vos derniers SMS, Maverick :\n")
                        recent.forEach { item ->
                            sb.append("• ${item.senderName} : \"${item.body}\"\n")
                        }
                        val text = sb.toString().trim()
                        _uiState.update { it.copy(bubbleMessage = text) }
                        speakTts("Vous avez reçu un SMS de ${recent.first().senderName}.")
                    }
                    return@launch
                }
                "comms:standardiste" -> {
                    phoneManager.isStandardisteModeActive = !phoneManager.isStandardisteModeActive
                    val state = if (phoneManager.isStandardisteModeActive) "activé" else "désactivé"
                    val msg = "Mode Standardiste $state, Monsieur Maverick. Je filtre et gère vos appels."
                    _uiState.update { it.copy(bubbleMessage = msg) }
                    speakTts(msg)
                    return@launch
                }
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
                    _uiState.update { it.copy(bubbleMessage = "📺 YouTube a été ouvert pour vous, Maverick.") }
                    return@launch
                }
                "device:launch_spotify" -> {
                    deviceController.launchApp("spotify")
                    _uiState.update { it.copy(bubbleMessage = "🎵 Spotify a été ouvert pour vous, Maverick.") }
                    return@launch
                }
                "device:vibrate" -> {
                    deviceController.vibrate(250)
                    _uiState.update { it.copy(bubbleMessage = "📳 Téléphone notifié avec succès, Maverick.") }
                    return@launch
                }
                "finance:patrimoine" -> {
                    if (!_uiState.value.isConnected) {
                        sendMessage("Donne-moi mon bilan financier et patrimoine")
                        return@launch
                    }
                }
                "finance:crypto" -> {
                    if (!_uiState.value.isConnected) {
                        sendMessage("Comment se porte le marché crypto et le Bitcoin ?")
                        return@launch
                    }
                }
                "finance:bourse" -> {
                    if (!_uiState.value.isConnected) {
                        sendMessage("Comment va la bourse, le S&P 500 et mes investissements ?")
                        return@launch
                    }
                }
                "finance:budget" -> {
                    if (!_uiState.value.isConnected) {
                        sendMessage("Quel est le solde de mes comptes et mon budget ?")
                        return@launch
                    }
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
                    it.copy(bubbleMessage = "Cette commande nécessite la connexion à votre PC (RTX 4080), Maverick. Utilisez ⚡ pour le réveiller !")
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
        try {
            connectivityManager?.unregisterNetworkCallback(networkCallback)
        } catch (e: Exception) {
            e.printStackTrace()
        }
        audioPlayer.stop()
        tts?.stop()
        tts?.shutdown()
        lipSyncJob?.cancel()
        blinkJob?.cancel()
        telemetryJob?.cancel()
    }
}
