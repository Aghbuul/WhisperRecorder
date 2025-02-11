@echo off

:: Get current directory
set CURRENT_PATH=%CD%

:: Show simple input dialog
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; $form = New-Object System.Windows.Forms.Form; $form.Text = 'Whisper Recorder Setup'; $form.Size = New-Object System.Drawing.Size(600,200); $form.StartPosition = 'CenterScreen'; $label = New-Object System.Windows.Forms.Label; $label.Location = New-Object System.Drawing.Point(10,20); $label.Size = New-Object System.Drawing.Size(560,20); $label.Text = 'Current location:'; $form.Controls.Add($label); $textBox = New-Object System.Windows.Forms.TextBox; $textBox.Location = New-Object System.Drawing.Point(10,50); $textBox.Size = New-Object System.Drawing.Size(560,20); $textBox.Text = '%CURRENT_PATH%'; $form.Controls.Add($textBox); $okButton = New-Object System.Windows.Forms.Button; $okButton.Location = New-Object System.Drawing.Point(400,100); $okButton.Size = New-Object System.Drawing.Size(75,23); $okButton.Text = 'OK'; $okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK; $form.AcceptButton = $okButton; $form.Controls.Add($okButton); $form.Topmost = $true; $result = $form.ShowDialog(); if ($result -eq [System.Windows.Forms.DialogResult]::OK) { $textBox.Text }" > "%temp%\result.txt"

set /p NEW_PATH=<"%temp%\result.txt"
del "%temp%\result.txt"

:: Simple find and replace in both files
powershell -Command "(Get-Content whisper_recorder.py) -replace 'E:\\Cursor\\Whisper', '%NEW_PATH%' | Set-Content whisper_recorder.py"
powershell -Command "(Get-Content whisper_cpp_wrapper.py) -replace 'E:\\Cursor\\Whisper', '%NEW_PATH%' | Set-Content whisper_cpp_wrapper.py"

echo Setup complete! You can now run run_whisper.bat
pause 