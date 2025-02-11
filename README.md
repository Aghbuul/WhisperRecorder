# Whisper Recorder

A clean and modern desktop application for recording audio and transcribing it using Whisper CPP.

## Features

- Clean, dark-themed modern UI
- One-click recording with visual feedback
- Maximum recording duration of 1 minute
- Visual recording indicator and countdown timer
- Transcription history with timestamps
- Copy functionality for transcriptions
- Auto-copy option for immediate clipboard access
- Extensive error logging

## Installation

1. Make sure you have Python 3.8+ installed
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure you have the Whisper CPP library properly set up in the `whisper.cpp` directory

## Usage

1. Run the application:
```bash
python whisper_recorder.py
```

2. Click the "Start Recording" button to begin recording
3. The progress bar and timer will show the recording progress
4. Click "Stop Recording" or wait for the 1-minute limit
5. The transcription will appear in the history section
6. Use the copy button or enable auto-copy for easy access to transcriptions

## Error Logging

The application logs errors and debug information to:
- Console output for development
- `app.log` file for persistent logging

## Notes

- Recordings are saved as WAV files with timestamps
- Transcription history is preserved between sessions
- The application uses the high-quality Whisper CPP model for transcription 