package com.example.nora.ui.main

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.nora.audio.NoraAudioPlayer
import com.example.nora.data.NoraAction
import com.example.nora.data.NoraApiClient
import com.example.nora.data.NoraOutfit
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

data class NoraUiState(
    val serverUrl: String = "http://192.168.1.183:8000",
    val isConnected: Boolean = false,
    val currentOutfit: String = "franxx",
    val spriteState: String = "idle",
    val bubbleMessage: String = "Bonjour Darling ! Je suis prête. Tu peux me parler ou piloter la maison.",
    val actions: List<NoraAction> = emptyList(),
    val outfits: List<NoraOutfit> = emptyList(),
    val isSpeaking: Boolean = false,
    val isLoading: Boolean = false,
    val errorMessage: String? = null
)

class MainScreenViewModel(application: Application) : AndroidViewModel(application) {
    private val prefs = application.getSharedPreferences("nora_prefs", Context.MODE_PRIVATE)
    private val apiClient = NoraApiClient()

    private val _uiState = MutableStateFlow(
        NoraUiState(
            serverUrl = prefs.getString("server_url", "http://192.168.1.183:8000") ?: "http://192.168.1.183:8000"
        )
    )
    val uiState: StateFlow<NoraUiState> = _uiState.asStateFlow()

    private var lipSyncJob: Job? = null
    private var blinkJob: Job? = null

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
        startBlinkLoop()
        refreshCapabilities()
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
                        isLoading = false,
                        actions = cap.actions,
                        outfits = cap.outfits,
                        currentOutfit = cap.currentOutfit
                    )
                }
            }.onFailure { err ->
                _uiState.update {
                    it.copy(
                        isConnected = false,
                        isLoading = false,
                        errorMessage = "Connexion au PC impossible (${err.message}). Vérifie l'adresse IP."
                    )
                }
            }
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
            val res = apiClient.sendChat(_uiState.value.serverUrl, text)
            res.onSuccess { reply ->
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        bubbleMessage = reply.reply,
                        currentOutfit = reply.outfit ?: it.currentOutfit,
                        isConnected = true
                    )
                }
                reply.audioUrl?.let { audioEndpoint ->
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
                        bubbleMessage = "Erreur de communication : ${err.message}"
                    )
                }
            }
        }
    }

    fun triggerAction(action: NoraAction) {
        viewModelScope.launch {
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
        }
    }

    fun selectOutfit(outfitId: String) {
        viewModelScope.launch {
            apiClient.setOutfit(_uiState.value.serverUrl, outfitId)
            _uiState.update { it.copy(currentOutfit = outfitId) }
            refreshCapabilities()
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
        lipSyncJob?.cancel()
        blinkJob?.cancel()
    }
}
