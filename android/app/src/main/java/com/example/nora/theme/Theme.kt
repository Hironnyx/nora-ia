package com.example.nora.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val NoraColorScheme = darkColorScheme(
  primary = ZeroTwoPink,
  onPrimary = Color.White,
  secondary = ZeroTwoCrimson,
  onSecondary = Color.White,
  background = ZeroTwoDarkBg,
  onBackground = ZeroTwoTextWhite,
  surface = ZeroTwoCardBg,
  onSurface = ZeroTwoTextWhite
)

@Composable
fun NoraTheme(
  content: @Composable () -> Unit,
) {
  MaterialTheme(colorScheme = NoraColorScheme, typography = Typography, content = content)
}
