package com.example.nora.health

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class HealthManager(private val context: Context) : SensorEventListener {

    private val prefs = context.getSharedPreferences("nora_health_prefs", Context.MODE_PRIVATE)
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as? SensorManager
    private val stepSensor = sensorManager?.getDefaultSensor(Sensor.TYPE_STEP_COUNTER)

    private var initialStepOffset: Float = -1f
    private var todaySteps: Int = 0

    init {
        val todayStr = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
        val lastDate = prefs.getString("last_date", "")

        if (lastDate != todayStr) {
            prefs.edit()
                .putString("last_date", todayStr)
                .putInt("water_count", 0)
                .putInt("steps_count", 0)
                .putFloat("step_offset", -1f)
                .apply()
        } else {
            todaySteps = prefs.getInt("steps_count", 0)
            initialStepOffset = prefs.getFloat("step_offset", -1f)
        }

        // Enregistrement du capteur podomètre matériel
        stepSensor?.let { sensor ->
            sensorManager?.registerListener(this, sensor, SensorManager.SENSOR_DELAY_UI)
        }
    }

    fun getTodaySteps(): Int = todaySteps

    fun getTodayWater(): Int = prefs.getInt("water_count", 0)

    fun addWater(count: Int = 1): Int {
        val current = getTodayWater() + count
        prefs.edit().putInt("water_count", current).apply()
        return current
    }

    fun getSleepHours(): Float = prefs.getFloat("sleep_hours", 7.5f)

    fun setSleepHours(hours: Float) {
        prefs.edit().putFloat("sleep_hours", hours).apply()
    }

    fun buildSyncPayload(batteryLevel: Int): JSONObject {
        return JSONObject().apply {
            put("steps", todaySteps)
            put("water", getTodayWater())
            put("sleep_hours", getSleepHours())
            put("battery", batteryLevel)
            put("heart_rate", 72)
        }
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event?.sensor?.type == Sensor.TYPE_STEP_COUNTER) {
            val totalSensorSteps = event.values[0]
            if (initialStepOffset < 0) {
                initialStepOffset = totalSensorSteps
                prefs.edit().putFloat("step_offset", initialStepOffset).apply()
            }

            val calculatedSteps = (totalSensorSteps - initialStepOffset).coerceAtLeast(0f).toInt()
            todaySteps = calculatedSteps
            prefs.edit().putInt("steps_count", todaySteps).apply()
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
}
