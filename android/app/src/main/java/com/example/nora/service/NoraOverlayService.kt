package com.example.nora.service

import android.animation.ValueAnimator
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.os.BatteryManager
import android.os.Build
import android.os.IBinder
import android.provider.Settings
import android.util.DisplayMetrics
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.view.animation.AccelerateDecelerateInterpolator
import android.view.animation.DecelerateInterpolator
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.app.NotificationCompat
import com.example.nora.MainActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.random.Random

/**
 * Service de Mascotte Flottante & Vie Autonome sur Smartphone.
 * Permet à Nora de se balader librement sur l'écran du téléphone par-dessus
 * toutes les applications (YouTube, Chrome, WhatsApp), de réagir aux notifications,
 * et d'offrir une présence bienveillante à Maverick.
 */
class NoraOverlayService : Service() {

    companion object {
        const val ACTION_START = "com.example.nora.action.START_OVERLAY"
        const val ACTION_STOP = "com.example.nora.action.STOP_OVERLAY"
        const val ACTION_TOGGLE = "com.example.nora.action.TOGGLE_OVERLAY"
        const val ACTION_THOUGHT = "com.example.nora.action.THOUGHT"
        const val EXTRA_THOUGHT_TEXT = "extra_thought_text"

        const val CHANNEL_ID = "nora_overlay_channel"
        const val NOTIFICATION_ID = 2002

        var isRunning: Boolean = false
            private set

        fun start(context: Context) {
            val intent = Intent(context, NoraOverlayService::class.java).apply {
                action = ACTION_START
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            val intent = Intent(context, NoraOverlayService::class.java).apply {
                action = ACTION_STOP
            }
            context.startService(intent)
        }

        fun showThought(context: Context, text: String) {
            val intent = Intent(context, NoraOverlayService::class.java).apply {
                action = ACTION_THOUGHT
                putExtra(EXTRA_THOUGHT_TEXT, text)
            }
            context.startService(intent)
        }
    }

    private var windowManager: WindowManager? = null
    private var floatingRootView: LinearLayout? = null
    private var avatarImageView: ImageView? = null
    private var bubbleContainer: FrameLayout? = null
    private var bubbleTextView: TextView? = null
    private var layoutParams: WindowManager.LayoutParams? = null

    private var idleBitmap: Bitmap? = null
    private var blinkBitmap: Bitmap? = null

    private val serviceScope = CoroutineScope(Dispatchers.Main + Job())
    private var hideBubbleJob: Job? = null
    private var isDragging = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action ?: ACTION_START

        when (action) {
            ACTION_STOP -> {
                stopSelf()
                return START_NOT_STICKY
            }
            ACTION_THOUGHT -> {
                val thought = intent?.getStringExtra(EXTRA_THOUGHT_TEXT)
                if (!thought.isNullOrBlank()) {
                    displayBubble(thought)
                }
                return START_STICKY
            }
            ACTION_START, ACTION_TOGGLE -> {
                if (action == ACTION_TOGGLE && isRunning) {
                    stopSelf()
                    return START_NOT_STICKY
                }

                if (!Settings.canDrawOverlays(this)) {
                    stopSelf()
                    return START_NOT_STICKY
                }

                startForegroundNotification()

                if (!isRunning) {
                    setupOverlayWindow()
                    loadSprites()
                    startBlinkLoop()
                    startAutonomousLifeLoop()
                    listenToIncomingMessages()
                    isRunning = true
                    displayBubble("Bonjour Maverick ! Je suis ravie de me balader à vos côtés 🌸")
                }
            }
        }

        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Nora - Mascotte Flottante",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Maintient Nora active en miniature sur votre écran"
                setShowBadge(false)
            }
            val nm = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
            nm?.createNotificationChannel(channel)
        }
    }

    private fun startForegroundNotification() {
        val openAppIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, NoraOverlayService::class.java).apply {
                action = ACTION_STOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🌸 Nora - Compagnon Flottant")
            .setContentText("Nora est avec vous sur votre écran.")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(openAppIntent)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "Masquer", stopIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    private fun setupOverlayWindow() {
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        val metrics = resources.displayMetrics
        val screenWidth = metrics.widthPixels
        val screenHeight = metrics.heightPixels

        val layoutType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            layoutType,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = screenWidth - dpToPx(90)
            y = screenHeight / 3
        }
        layoutParams = params

        // 1. Vue Racine (Verticale : Bulle de dialogue en haut, Avatar en bas)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
        }
        floatingRootView = root

        // 2. Bulle de dialogue stylée Zero Two
        val bubbleBox = FrameLayout(this).apply {
            val bgDrawable = GradientDrawable().apply {
                setColor(Color.parseColor("#E60F172A")) // Fond sombre ardoise 90% opaque
                setStroke(dpToPx(1.5f), Color.parseColor("#FB7185")) // Bordure rose néon Zero Two
                cornerRadius = dpToPx(14f).toFloat()
            }
            background = bgDrawable
            setPadding(dpToPx(10), dpToPx(6), dpToPx(10), dpToPx(6))
            visibility = View.GONE
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                bottomMargin = dpToPx(6)
            }
        }
        bubbleContainer = bubbleBox

        val textView = TextView(this).apply {
            setTextColor(Color.WHITE)
            textSize = 12f
            maxWidth = dpToPx(190)
            text = "Bonjour Maverick ! 🌸"
        }
        bubbleTextView = textView
        bubbleBox.addView(textView)
        root.addView(bubbleBox)

        // 3. Conteneur Avatar
        val avatarContainer = FrameLayout(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                dpToPx(76),
                dpToPx(76)
            )
        }

        val avatar = ImageView(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
            scaleType = ImageView.ScaleType.FIT_CENTER
        }
        avatarImageView = avatar
        avatarContainer.addView(avatar)
        root.addView(avatarContainer)

        setupTouchEvents(avatarContainer, metrics)

        try {
            windowManager?.addView(root, params)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun setupTouchEvents(touchView: View, metrics: DisplayMetrics) {
        var initialX = 0
        var initialY = 0
        var touchDownX = 0f
        var touchDownY = 0f
        var touchDownTime = 0L

        touchView.setOnTouchListener { _, event ->
            val params = layoutParams ?: return@setOnTouchListener false

            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    touchDownX = event.rawX
                    touchDownY = event.rawY
                    touchDownTime = System.currentTimeMillis()
                    isDragging = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = (event.rawX - touchDownX).toInt()
                    val dy = (event.rawY - touchDownY).toInt()

                    if (Math.abs(dx) > dpToPx(6) || Math.abs(dy) > dpToPx(6)) {
                        isDragging = true
                    }

                    if (isDragging) {
                        params.x = (initialX + dx).coerceIn(0, metrics.widthPixels - dpToPx(76))
                        params.y = (initialY + dy).coerceIn(dpToPx(40), metrics.heightPixels - dpToPx(120))
                        try {
                            windowManager?.updateViewLayout(floatingRootView, params)
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    val clickDuration = System.currentTimeMillis() - touchDownTime
                    val totalDistance = Math.hypot(
                        (event.rawX - touchDownX).toDouble(),
                        (event.rawY - touchDownY).toDouble()
                    )

                    if (!isDragging || (clickDuration < 220 && totalDistance < dpToPx(12))) {
                        // Clic rapide sur Nora !
                        onAvatarClicked()
                    } else {
                        // Fin de glissement : Ancrage magnétique fluide sur le bord le plus proche (Snap to Edge)
                        snapToNearestEdge(metrics)
                    }
                    isDragging = false
                    true
                }
                else -> false
            }
        }
    }

    private fun onAvatarClicked() {
        val bubble = bubbleContainer ?: return
        if (bubble.visibility == View.VISIBLE) {
            // Deuxième tap : Ouvrir l'application Nora en grand
            openMainActivity()
        } else {
            // Premier tap : Pensée bienveillante ou statut rapide
            val hour = SimpleDateFormat("HH:mm", Locale.FRENCH).format(Date())
            val battery = getBatteryLevel()
            val thoughts = listOf(
                "Bonjour Maverick ! Je suis à vos côtés 🌸 (Touchez-moi encore pour ouvrir l'application)",
                "Il est $hour. Pensez à faire une petite pause écran, Maverick !",
                "Votre téléphone est à $battery% de batterie 🔋 Tout est sous contrôle.",
                "Je veille sur vos messages et sur votre système, Maverick."
            )
            displayBubble(thoughts.random())
        }
    }

    private fun snapToNearestEdge(metrics: DisplayMetrics) {
        val params = layoutParams ?: return
        val currentX = params.x
        val screenWidth = metrics.widthPixels
        val mascotWidth = dpToPx(76)

        val targetX = if (currentX + mascotWidth / 2 < screenWidth / 2) {
            dpToPx(12) // Bord gauche
        } else {
            screenWidth - mascotWidth - dpToPx(12) // Bord droit
        }

        val animator = ValueAnimator.ofInt(currentX, targetX).apply {
            duration = 240
            interpolator = DecelerateInterpolator()
            addUpdateListener { anim ->
                params.x = anim.animatedValue as Int
                try {
                    windowManager?.updateViewLayout(floatingRootView, params)
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
        animator.start()
    }

    fun displayBubble(text: String, durationMs: Long = 6500) {
        val bubble = bubbleContainer ?: return
        val tv = bubbleTextView ?: return

        tv.text = text
        bubble.alpha = 0f
        bubble.visibility = View.VISIBLE
        bubble.animate()
            .alpha(1f)
            .setDuration(250)
            .start()

        hideBubbleJob?.cancel()
        hideBubbleJob = serviceScope.launch {
            delay(durationMs)
            bubble.animate()
                .alpha(0f)
                .setDuration(350)
                .withEndAction {
                    bubble.visibility = View.GONE
                }
                .start()
        }
    }

    private fun loadSprites() {
        try {
            val prefs = getSharedPreferences("nora_prefs", Context.MODE_PRIVATE)
            val outfit = prefs.getString("current_outfit", "franxx") ?: "franxx"

            val idlePath = "sprites/nora_${outfit}_idle.png"
            val blinkPath = "sprites/nora_${outfit}_blink.png"

            idleBitmap = try {
                assets.open(idlePath).use { BitmapFactory.decodeStream(it) }
            } catch (e: Exception) {
                assets.open("sprites/nora_idle.png").use { BitmapFactory.decodeStream(it) }
            }

            blinkBitmap = try {
                assets.open(blinkPath).use { BitmapFactory.decodeStream(it) }
            } catch (e: Exception) {
                assets.open("sprites/nora_blink.png").use { BitmapFactory.decodeStream(it) }
            }

            avatarImageView?.setImageBitmap(idleBitmap)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun startBlinkLoop() {
        serviceScope.launch {
            while (isActive) {
                delay(Random.nextLong(3200, 5600))
                if (!isDragging && blinkBitmap != null) {
                    avatarImageView?.setImageBitmap(blinkBitmap)
                    delay(150)
                    avatarImageView?.setImageBitmap(idleBitmap)
                }
            }
        }
    }

    private fun startAutonomousLifeLoop() {
        serviceScope.launch {
            while (isActive) {
                // Intervalle autonome entre 40 et 80 secondes
                delay(Random.nextLong(40000, 80000))

                if (isDragging) continue

                val actionChoice = Random.nextInt(100)
                when {
                    // 1. Petite balade / Flottement vertical autonome le long du bord (40% de chance)
                    actionChoice < 40 -> {
                        roamGently()
                    }
                    // 2. Pensée spontanée ou rappel (45% de chance)
                    actionChoice < 85 -> {
                        triggerAutonomousThought()
                    }
                    // 3. Petit clin d'œil affectueux (15% de chance)
                    else -> {
                        avatarImageView?.setImageBitmap(blinkBitmap)
                        delay(220)
                        avatarImageView?.setImageBitmap(idleBitmap)
                    }
                }
            }
        }
    }

    private fun roamGently() {
        val params = layoutParams ?: return
        val metrics = resources.displayMetrics
        val currentY = params.y

        // Déplacement vertical aléatoire de 35 à 65 pixels vers le haut ou le bas
        val deltaY = if (Random.nextBoolean()) Random.nextInt(35, 65) else -Random.nextInt(35, 65)
        val targetY = (currentY + deltaY).coerceIn(dpToPx(60), metrics.heightPixels - dpToPx(160))

        val animator = ValueAnimator.ofInt(currentY, targetY).apply {
            duration = 1200
            interpolator = AccelerateDecelerateInterpolator()
            addUpdateListener { anim ->
                params.y = anim.animatedValue as Int
                try {
                    windowManager?.updateViewLayout(floatingRootView, params)
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
        animator.start()
    }

    private fun triggerAutonomousThought() {
        val hour = SimpleDateFormat("HH:mm", Locale.FRENCH).format(Date())
        val thoughts = mutableListOf(
            "Pensez à boire une gorgée d'eau, Maverick ! 💧",
            "Je veille sur votre écran pendant votre navigation, Maverick 🌸",
            "J'ai relu mes notes sur les supraconducteurs et l'attachement... C'est passionnant !",
            "Il est $hour, j'espère que votre journée se passe à merveille, Maverick.",
            "Batterie du téléphone : ${getBatteryLevel()}% 🔋",
            "Tout est calme et sécurisé à bord ✨"
        )
        displayBubble(thoughts.random())
    }

    private fun listenToIncomingMessages() {
        NoraNotificationListenerService.onMessageReceivedListener = { msg ->
            serviceScope.launch(Dispatchers.Main) {
                val preview = if (msg.message.length > 50) msg.message.take(47) + "..." else msg.message
                displayBubble("📩 ${msg.appName} (${msg.sender}) :\n$preview", 8000)
                // Petit saut d'excitation
                roamGently()
            }
        }
    }

    private fun openMainActivity() {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        startActivity(intent)
    }

    private fun getBatteryLevel(): Int {
        val bm = getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
        return bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: 80
    }

    private fun dpToPx(dp: Float): Int = (dp * resources.displayMetrics.density).toInt()
    private fun dpToPx(dp: Int): Int = (dp * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        super.onDestroy()
        isRunning = false
        hideBubbleJob?.cancel()
        NoraNotificationListenerService.onMessageReceivedListener = null

        floatingRootView?.let { root ->
            try {
                windowManager?.removeView(root)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
        idleBitmap?.recycle()
        blinkBitmap?.recycle()
        idleBitmap = null
        blinkBitmap = null
    }
}
