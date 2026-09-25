param(
    [string]$ShortcutPath,
    [string]$TargetPath,
    [string]$Arguments,
    [string]$WorkingDirectory,
    [string]$IconLocation,
    [string]$Description,
    [string]$Hotkey
)
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
if ($Arguments) { $Shortcut.Arguments = $Arguments }
if ($WorkingDirectory) { $Shortcut.WorkingDirectory = $WorkingDirectory }
if ($IconLocation) { $Shortcut.IconLocation = $IconLocation }
if ($Description) { $Shortcut.Description = $Description }
if ($Hotkey) { $Shortcut.Hotkey = $Hotkey }
$Shortcut.Save()
