package com.example.nora.ui.main

import android.app.Activity
import android.content.Intent
import android.speech.RecognizerIntent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.example.nora.data.NoraAction
import com.example.nora.theme.ZeroTwoAmber
import com.example.nora.theme.ZeroTwoBorder
import com.example.nora.theme.ZeroTwoCardBg
import com.example.nora.theme.ZeroTwoCrimson
import com.example.nora.theme.ZeroTwoCyan
import com.example.nora.theme.ZeroTwoDarkBg
import com.example.nora.theme.ZeroTwoEmerald
import com.example.nora.theme.ZeroTwoPink
import com.example.nora.theme.ZeroTwoPurple
import com.example.nora.theme.ZeroTwoRoseLight
import com.example.nora.theme.ZeroTwoTextMuted
import com.example.nora.theme.ZeroTwoTextWhite
import java.util.Locale

@Composable
fun MainScreen(
    modifier: Modifier = Modifier,
    viewModel: MainScreenViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var inputText by remember { mutableStateOf("") }
    var showSettingsDialog by remember { mutableStateOf(false) }
    var settingsUrlText by remember { mutableStateOf(state.serverUrl) }

    val context = LocalContext.current

    // Lanceur de reconnaissance vocale Android
    val speechLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val spoken = result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
            if (!spoken.isNullOrBlank()) {
                viewModel.sendMessage(spoken)
            }
        }
    }

    // Animation de lévitation sinusoïdale 30 FPS pour Zero Two
    val infiniteTransition = rememberInfiniteTransition(label = "float")
    val floatOffset by infiniteTransition.animateFloat(
        initialValue = -6f,
        targetValue = 6f,
        animationSpec = infiniteRepeatable(
            animation = tween(2200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "mascot_float"
    )

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(ZeroTwoDarkBg)
            .padding(horizontal = 14.dp, vertical = 6.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // 1. Barre Supérieure (Statut Réseau & Contrôles Rapides)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "🌸 NORA",
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        color = ZeroTwoPink
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "Zero Two",
                        fontSize = 12.sp,
                        color = ZeroTwoRoseLight
                    )
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val statusColor = when (state.connectionType) {
                        "local" -> ZeroTwoEmerald
                        "remote" -> ZeroTwoCyan
                        "autonomous" -> ZeroTwoPurple
                        else -> if (state.isConnected) ZeroTwoEmerald else ZeroTwoRoseLight
                    }
                    val statusText = when (state.connectionType) {
                        "local" -> "Wi-Fi Maison (RTX 4080) 🟢"
                        "remote" -> "4G/5G Distant (Cloudflare) 🌐"
                        "autonomous" -> "Mode Autonome Mobile 📱"
                        else -> if (state.isConnected) "Connecté au PC" else "Recherche de Nora..."
                    }
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(statusColor)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = statusText,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = statusColor
                    )
                }
            }

            // Boutons d'actions rapides (Torche, WoL, Actualiser, Réglages)
            Row(verticalAlignment = Alignment.CenterVertically) {
                // Lampe torche rapide
                IconButton(
                    onClick = { viewModel.toggleTorch() },
                    modifier = Modifier.size(36.dp)
                ) {
                    Text(
                        text = if (state.isFlashlightOn) "💡" else "🔦",
                        fontSize = 18.sp
                    )
                }

                // Réveil PC rapide (WoL)
                IconButton(
                    onClick = { viewModel.wakePc() },
                    modifier = Modifier.size(36.dp)
                ) {
                    Text("⚡", fontSize = 18.sp)
                }

                IconButton(
                    onClick = { viewModel.refreshCapabilities() },
                    modifier = Modifier.size(36.dp)
                ) {
                    Text("🔄", fontSize = 16.sp)
                }

                IconButton(
                    onClick = {
                        settingsUrlText = state.serverUrl
                        showSettingsDialog = true
                    },
                    modifier = Modifier.size(36.dp)
                ) {
                    Text("⚙️", fontSize = 16.sp)
                }
            }
        }

        // 2. Bandeau Santé & Télémétrie Téléphone (Ange Gardien)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 4.dp)
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Verres d'eau avec bouton d'ajout direct
            HealthChip(
                icon = "💧",
                title = "${state.todayWater}/8",
                subtitle = "Eau",
                highlight = state.todayWater >= 8,
                onClick = { viewModel.addWater() }
            )

            // Podomètre Pas réels
            HealthChip(
                icon = "🏃",
                title = "${state.todaySteps}",
                subtitle = "Pas",
                highlight = state.todaySteps >= 6000,
                onClick = null
            )

            // Batterie smartphone
            HealthChip(
                icon = "🔋",
                title = "${state.batteryPercent}%",
                subtitle = "Batterie",
                highlight = state.batteryPercent > 20,
                onClick = null
            )

            // Sommeil
            HealthChip(
                icon = "💤",
                title = "${state.sleepHours}h",
                subtitle = "Sommeil",
                highlight = true,
                onClick = null
            )
        }

        // 3. Zone Centrale (Mascotte & Dialogue)
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(4.dp))

            // Bulle de dialogue Zero Two
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.5.dp, ZeroTwoPink, RoundedCornerShape(16.dp)),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = ZeroTwoCardBg)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(
                        text = state.bubbleMessage,
                        color = ZeroTwoTextWhite,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium,
                        lineHeight = 19.sp,
                        textAlign = TextAlign.Start
                    )
                    if (state.isSpeaking) {
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "🎙️ Zero Two te parle...",
                            fontSize = 11.sp,
                            color = ZeroTwoRoseLight,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Sprite animé Zero Two avec basculement automatique Asset local / Serveur PC
            val localAssetPath = "file:///android_asset/sprites/nora_${state.currentOutfit}_${state.spriteState}.png"
            val fallbackLocalPath = "file:///android_asset/sprites/nora_${state.spriteState}.png"
            val serverSpriteUrl = "${state.serverUrl.trimEnd('/')}/api/sprites/${state.currentOutfit}/${state.spriteState}.png"
            val targetSpriteUrl = if (state.isConnected) serverSpriteUrl else localAssetPath

            Box(
                modifier = Modifier
                    .size(190.dp)
                    .offset(y = floatOffset.dp),
                contentAlignment = Alignment.Center
            ) {
                AsyncImage(
                    model = ImageRequest.Builder(context)
                        .data(targetSpriteUrl)
                        .crossfade(true)
                        .build(),
                    contentDescription = "Zero Two Mascot",
                    modifier = Modifier.fillMaxSize()
                )
            }

            // Sélecteur de tenues
            Row(
                modifier = Modifier.padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                val outfits = listOf("franxx" to "Pilote 🚀", "school" to "Écolière 🎓", "hoodie" to "Hoodie 🧸")
                outfits.forEach { (id, label) ->
                    val isSelected = state.currentOutfit == id
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(20.dp))
                            .background(if (isSelected) ZeroTwoCrimson else ZeroTwoCardBg)
                            .border(1.dp, if (isSelected) ZeroTwoPink else ZeroTwoBorder, RoundedCornerShape(20.dp))
                            .clickable { viewModel.selectOutfit(id) }
                            .padding(horizontal = 12.dp, vertical = 5.dp)
                    ) {
                        Text(
                            text = label,
                            fontSize = 11.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                            color = if (isSelected) Color.White else ZeroTwoTextMuted
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // 4. Panneau Dynamique des Capacités & Domotique
            Text(
                text = if (state.isConnected) "⚡ CONTRÔLES PC & MAISON CONNECTÉE" else "📱 ACTIONS RAPIDES DU SMARTPHONE",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = if (state.isConnected) ZeroTwoPink else ZeroTwoCyan,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 4.dp, vertical = 2.dp)
            )

            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(175.dp),
                contentPadding = PaddingValues(2.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(state.actions) { action ->
                    ActionCard(action = action, onClick = { viewModel.triggerAction(action) })
                }
            }
        }

        // 5. Barre Inférieure (Microphone & Saisie Texte)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = inputText,
                onValueChange = { inputText = it },
                placeholder = { Text("Parler à Nora ou donner un ordre...", color = ZeroTwoTextMuted, fontSize = 12.sp) },
                modifier = Modifier
                    .weight(1f)
                    .height(50.dp),
                shape = RoundedCornerShape(25.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = ZeroTwoPink,
                    unfocusedBorderColor = ZeroTwoBorder,
                    focusedTextColor = ZeroTwoTextWhite,
                    unfocusedTextColor = ZeroTwoTextWhite,
                    focusedContainerColor = ZeroTwoCardBg,
                    unfocusedContainerColor = ZeroTwoCardBg
                ),
                singleLine = true
            )

            Spacer(modifier = Modifier.width(8.dp))

            if (inputText.isNotBlank()) {
                IconButton(
                    onClick = {
                        viewModel.sendMessage(inputText)
                        inputText = ""
                    },
                    modifier = Modifier
                        .size(46.dp)
                        .clip(CircleShape)
                        .background(ZeroTwoPink)
                ) {
                    Text("➤", fontSize = 18.sp, color = Color.White)
                }
            } else {
                IconButton(
                    onClick = {
                        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.FRENCH.toString())
                            putExtra(RecognizerIntent.EXTRA_PROMPT, "Parlez à Nora (Zero Two)...")
                        }
                        try {
                            speechLauncher.launch(intent)
                        } catch (e: Exception) {
                            viewModel.sendMessage("Bonjour Darling !")
                        }
                    },
                    modifier = Modifier
                        .size(46.dp)
                        .clip(CircleShape)
                        .background(
                            Brush.linearGradient(
                                colors = listOf(ZeroTwoCrimson, ZeroTwoPink)
                            )
                        )
                ) {
                    Text(text = "🎙️", fontSize = 20.sp)
                }
            }
        }
    }

    // Dialogue de configuration de l'IP du serveur PC ou Tunnel 4G/5G
    if (showSettingsDialog) {
        AlertDialog(
            onDismissRequest = { showSettingsDialog = false },
            title = { Text("Connexion au PC Nora", color = ZeroTwoPink, fontWeight = FontWeight.Bold) },
            text = {
                Column {
                    Text(
                        "Entrez l'adresse IP Wi-Fi locale ou l'URL de tunnel distant Cloudflare :",
                        color = ZeroTwoTextWhite,
                        fontSize = 12.sp
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = settingsUrlText,
                        onValueChange = { settingsUrlText = it },
                        label = { Text("URL Serveur / Tunnel") },
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = ZeroTwoPink,
                            focusedTextColor = ZeroTwoTextWhite
                        )
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        "Wi-Fi Maison : http://192.168.1.183:8000\nAccès 4G/5G : URL Cloudflare générée par 'activer_acces_distant.bat'",
                        fontSize = 10.sp,
                        color = ZeroTwoTextMuted
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.setServerUrl(settingsUrlText)
                        showSettingsDialog = false
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = ZeroTwoPink)
                ) {
                    Text("Enregistrer", color = Color.White)
                }
            },
            dismissButton = {
                TextButton(onClick = { showSettingsDialog = false }) {
                    Text("Annuler", color = ZeroTwoTextMuted)
                }
            },
            containerColor = ZeroTwoCardBg
        )
    }
}

@Composable
fun HealthChip(
    icon: String,
    title: String,
    subtitle: String,
    highlight: Boolean,
    onClick: (() -> Unit)?
) {
    val chipModifier = Modifier
        .clip(RoundedCornerShape(12.dp))
        .background(ZeroTwoCardBg)
        .border(1.dp, if (highlight) ZeroTwoCyan else ZeroTwoBorder, RoundedCornerShape(12.dp))
        .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
        .padding(horizontal = 10.dp, vertical = 6.dp)

    Row(
        modifier = chipModifier,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = icon, fontSize = 16.sp)
        Spacer(modifier = Modifier.width(6.dp))
        Column {
            Text(
                text = title,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = if (highlight) ZeroTwoCyan else ZeroTwoTextWhite
            )
            Text(
                text = subtitle,
                fontSize = 9.sp,
                color = ZeroTwoTextMuted
            )
        }
    }
}

@Composable
fun ActionCard(action: NoraAction, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .height(72.dp)
            .border(
                1.dp,
                if (action.active) ZeroTwoPink else ZeroTwoBorder,
                RoundedCornerShape(12.dp)
            )
            .clickable { onClick() },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (action.active) Color(0xFF2E1065) else ZeroTwoCardBg
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 10.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(text = action.icon, fontSize = 22.sp)
            Spacer(modifier = Modifier.width(8.dp))
            Column {
                Text(
                    text = action.title,
                    color = ZeroTwoTextWhite,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = if (action.active) "Actif ✓" else "Prêt",
                    color = if (action.active) ZeroTwoPink else ZeroTwoTextMuted,
                    fontSize = 10.sp
                )
            }
        }
    }
}
