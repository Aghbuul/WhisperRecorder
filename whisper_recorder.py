import customtkinter as ctk
import pyaudio
import wave
import threading
import time
import os
import logging
import pyperclip
from datetime import datetime
from typing import Optional
from whisper_cpp_wrapper import WhisperTranscriber

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

class WhisperRecorderApp:
    def __init__(self):
        self.setup_window()
        self.setup_audio()
        self.setup_variables()
        self.setup_whisper()
        self.create_widgets()
        self.load_history()
        
    def setup_window(self):
        self.window = ctk.CTk()
        self.window.title("Whisper Recorder")
        self.window.geometry("600x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
    def setup_audio(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.max_duration = 60  # Maximum recording duration in seconds
        self.p = pyaudio.PyAudio()
        
    def setup_variables(self):
        self.recording = False
        self.stream: Optional[pyaudio.Stream] = None
        self.frames = []
        self.auto_copy = ctk.BooleanVar(value=False)
        self.current_recording_thread: Optional[threading.Thread] = None
        self.transcriptions = []
        
    def setup_whisper(self):
        try:
            self.transcriber = WhisperTranscriber()
            logging.info("Whisper transcriber initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing Whisper: {str(e)}")
            self.show_error("Could not initialize Whisper. Please check the logs.")
        
    def create_widgets(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Recording button and indicator
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(pady=20)
        
        self.record_button = ctk.CTkButton(
            self.button_frame,
            text="Start Recording",
            command=self.toggle_recording,
            width=200,
            height=50
        )
        self.record_button.pack(pady=10)
        
        self.indicator = ctk.CTkProgressBar(self.button_frame, width=200)
        self.indicator.pack(pady=5)
        self.indicator.set(0)
        
        # Timer label
        self.timer_label = ctk.CTkLabel(self.button_frame, text="0:00")
        self.timer_label.pack(pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(self.button_frame, text="")
        self.status_label.pack(pady=5)
        
        # Auto-copy checkbox
        self.auto_copy_check = ctk.CTkCheckBox(
            self.main_frame,
            text="Auto-copy transcription to clipboard",
            variable=self.auto_copy
        )
        self.auto_copy_check.pack(pady=10)
        
        # Transcription display
        self.transcription_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            label_text="Transcription History",
            height=400
        )
        self.transcription_frame.pack(fill="both", expand=True, pady=20)
        
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        try:
            self.recording = True
            self.frames = []
            self.record_button.configure(text="Stop Recording", fg_color="red")
            self.status_label.configure(text="Recording...")
            
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.current_recording_thread = threading.Thread(target=self.record_audio)
            self.current_recording_thread.start()
            
            # Start the timer and indicator update
            self.start_time = time.time()
            self.update_timer()
            
            logging.info("Started recording")
        except Exception as e:
            logging.error(f"Error starting recording: {str(e)}")
            self.show_error("Could not start recording")
            
    def record_audio(self):
        try:
            while self.recording and (time.time() - self.start_time) < self.max_duration:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
                
            if (time.time() - self.start_time) >= self.max_duration:
                self.stop_recording()
        except Exception as e:
            logging.error(f"Error during recording: {str(e)}")
            self.recording = False
            
    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.record_button.configure(text="Start Recording", fg_color=["#3B8ED0", "#1F6AA5"])
            self.status_label.configure(text="Processing...")
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            self.save_and_transcribe()
            
    def update_timer(self):
        if self.recording:
            elapsed = int(time.time() - self.start_time)
            remaining = self.max_duration - elapsed
            if remaining >= 0:
                self.timer_label.configure(text=f"{remaining // 60}:{remaining % 60:02d}")
                self.indicator.set(elapsed / self.max_duration)
                self.window.after(100, self.update_timer)
            
    def save_and_transcribe(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            # Transcribe using Whisper
            transcription = self.transcriber.transcribe(filename)
            
            if transcription:
                self.add_transcription(transcription)
                
                if self.auto_copy.get():
                    pyperclip.copy(transcription)
                    
                logging.info(f"Successfully transcribed recording: {filename}")
            else:
                self.show_error("Could not transcribe audio")
                
            # Clean up the audio file
            try:
                os.remove(filename)
            except Exception as e:
                logging.warning(f"Could not remove temporary file {filename}: {str(e)}")
                
            self.status_label.configure(text="")
                
        except Exception as e:
            logging.error(f"Error saving/transcribing recording: {str(e)}")
            self.show_error("Error processing recording")
            self.status_label.configure(text="")
            
    def add_transcription(self, text):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create frame for this transcription
        frame = ctk.CTkFrame(self.transcription_frame)
        frame.pack(fill="x", pady=5, padx=5)
        
        # Add timestamp
        ctk.CTkLabel(frame, text=timestamp, font=("Arial", 10)).pack(anchor="w")
        
        # Add transcription text
        text_label = ctk.CTkLabel(frame, text=text, wraplength=500)
        text_label.pack(pady=5)
        
        # Add copy button
        copy_button = ctk.CTkButton(
            frame,
            text="Copy",
            width=60,
            command=lambda: pyperclip.copy(text)
        )
        copy_button.pack(pady=5)
        
        # Add to history
        self.transcriptions.insert(0, {"timestamp": timestamp, "text": text})
        self.save_history()
        
    def load_history(self):
        try:
            if os.path.exists("history.txt"):
                with open("history.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        timestamp, text = line.strip().split("|", 1)
                        self.add_transcription(text)
        except Exception as e:
            logging.error(f"Error loading history: {str(e)}")
            
    def save_history(self):
        try:
            with open("history.txt", "w", encoding="utf-8") as f:
                for item in self.transcriptions:
                    f.write(f"{item['timestamp']}|{item['text']}\n")
        except Exception as e:
            logging.error(f"Error saving history: {str(e)}")
            
    def show_error(self, message):
        error_window = ctk.CTkToplevel(self.window)
        error_window.title("Error")
        error_window.geometry("300x150")
        
        ctk.CTkLabel(error_window, text=message).pack(pady=20)
        ctk.CTkButton(
            error_window,
            text="OK",
            command=error_window.destroy
        ).pack()
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = WhisperRecorderApp()
    app.run() 