import customtkinter as ctk
import pyaudio
import wave
import threading
import time
import os
import logging
import pyperclip
import keyboard
import ctypes
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

# Windows API constants for console management
SW_HIDE = 0
SW_SHOW = 5
KERNEL32 = ctypes.WinDLL('kernel32')
USER32 = ctypes.WinDLL('user32')

class WhisperRecorderApp:
    def __init__(self):
        # Create necessary folders
        self.recordings_dir = "recordings"
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        self.setup_window()
        self.setup_audio()
        self.setup_variables()
        self.setup_whisper()
        self.setup_hotkeys()
        self.create_widgets()
        self.load_history()
        
        # Hide console after initialization
        self.window.after(1000, self.hide_console)
        
    def setup_window(self):
        self.window = ctk.CTk()
        self.window.title("Whisper Recorder")
        self.window.geometry("800x900")
        self.window.configure(fg_color="#1a1a1a")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Make window centered
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 900) // 2
        self.window.geometry(f"800x900+{x}+{y}")
        
        # Add window close handler
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_audio(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.max_duration = 60
        self.p = pyaudio.PyAudio()
        
    def setup_variables(self):
        self.recording = False
        self.processing = False
        self.stream = None
        self.frames = []
        self.auto_copy = ctk.BooleanVar(value=True)
        self.show_console = ctk.BooleanVar(value=False)
        self.current_recording_thread = None
        self.transcriptions = []
        self.start_time = None
        self.hotkey_pressed = False
        logging.debug("Variables initialized")
        
    def setup_whisper(self):
        try:
            self.transcriber = WhisperTranscriber()
            logging.info("Whisper transcriber initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing Whisper: {str(e)}", exc_info=True)
            
    def setup_hotkeys(self):
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey('ctrl+shift+c', self.toggle_recording, suppress=True)
            logging.info("Hotkeys registered successfully")
        except Exception as e:
            logging.error(f"Error setting up hotkeys: {str(e)}", exc_info=True)
            
    def create_widgets(self):
        # Top section with gradient
        self.top_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=40, pady=(40, 20))
        
        # Title
        title = ctk.CTkLabel(
            self.top_frame,
            text="Whisper Recorder",
            font=("Segoe UI", 24, "bold"),
            text_color="#ffffff"
        )
        title.pack(pady=(0, 20))
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            self.top_frame,
            text="Record and transcribe your voice with one click",
            font=("Segoe UI", 14),
            text_color="#888888"
        )
        subtitle.pack(pady=(0, 30))
        
        # Settings section with hotkey info and console toggle
        settings_frame = ctk.CTkFrame(self.window, fg_color="#222222", corner_radius=15)
        settings_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        # Settings grid for better organization
        settings_grid = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_grid.pack(fill="x", padx=15, pady=15)
        
        # Hotkey info
        hotkey_label = ctk.CTkLabel(
            settings_grid,
            text="Press Ctrl+Shift+C to Start/Stop Recording",
            font=("Segoe UI", 12, "bold"),
            text_color="#ffffff"
        )
        hotkey_label.pack(side="left", padx=(0, 20))
        
        # Console toggle with icon-like symbol
        self.console_toggle = ctk.CTkCheckBox(
            settings_grid,
            text="⌨ Show Console",
            variable=self.show_console,
            command=self.toggle_console,
            font=("Segoe UI", 12),
            fg_color="#4a9eff",
            hover_color="#2d5a88",
            corner_radius=4
        )
        self.console_toggle.pack(side="right")
        
        # Main recording section
        self.record_frame = ctk.CTkFrame(self.window, fg_color="#222222", corner_radius=15)
        self.record_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        # Recording button with modern design
        self.record_button = ctk.CTkButton(
            self.record_frame,
            text="Start Recording",
            command=self.toggle_recording,
            width=300,
            height=60,
            corner_radius=30,
            font=("Segoe UI", 16, "bold"),
            fg_color="#2d5a88",
            hover_color="#1d3a58"
        )
        self.record_button.pack(pady=(30, 15))
        
        # Timer with modern font
        self.timer_label = ctk.CTkLabel(
            self.record_frame,
            text="0:00",
            font=("Segoe UI", 36, "bold"),
            text_color="#4a9eff"
        )
        self.timer_label.pack(pady=(0, 10))
        
        # Progress bar with modern style
        self.indicator = ctk.CTkProgressBar(
            self.record_frame,
            width=300,
            height=4,
            corner_radius=2,
            fg_color="#333333",
            progress_color="#4a9eff"
        )
        self.indicator.pack(pady=(0, 10))
        self.indicator.set(0)
        
        # Status label with subtle color
        self.status_label = ctk.CTkLabel(
            self.record_frame,
            text="",
            font=("Segoe UI", 12),
            text_color="#888888"
        )
        self.status_label.pack(pady=(0, 30))
        
        # Latest transcription section
        latest_frame = ctk.CTkFrame(self.window, fg_color="#222222", corner_radius=15)
        latest_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        # Latest transcription header with settings
        latest_header = ctk.CTkFrame(latest_frame, fg_color="transparent")
        latest_header.pack(fill="x", padx=15, pady=(15, 0))
        
        latest_title = ctk.CTkLabel(
            latest_header,
            text="Latest Transcription",
            font=("Segoe UI", 14, "bold"),
            text_color="#ffffff"
        )
        latest_title.pack(side="left")
        
        # Auto-copy checkbox with modern style
        self.auto_copy_check = ctk.CTkCheckBox(
            latest_header,
            text="Auto-copy to clipboard",
            variable=self.auto_copy,
            font=("Segoe UI", 12),
            fg_color="#4a9eff",
            hover_color="#2d5a88",
            corner_radius=4
        )
        self.auto_copy_check.pack(side="right", padx=15)
        
        # Latest transcription text
        self.latest_text = ctk.CTkTextbox(
            latest_frame,
            height=100,
            font=("Segoe UI", 12),
            fg_color="#2a2a2a",
            text_color="#ffffff",
            wrap="word"
        )
        self.latest_text.pack(fill="x", padx=15, pady=15)
        
        # History section with modern header
        history_header = ctk.CTkFrame(self.window, fg_color="transparent")
        history_header.pack(fill="x", padx=40, pady=(20, 10))
        
        history_title = ctk.CTkLabel(
            history_header,
            text="Transcription History",
            font=("Segoe UI", 16, "bold"),
            text_color="#ffffff"
        )
        history_title.pack(anchor="w")
        
        # Scrollable history with modern styling
        self.transcription_frame = ctk.CTkScrollableFrame(
            self.window,
            fg_color="#222222",
            corner_radius=15,
            height=300
        )
        self.transcription_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
    def toggle_recording(self):
        try:
            logging.debug(f"Toggle recording called. Current state - recording: {self.recording}, processing: {self.processing}")
            if self.processing:
                logging.debug("Ignoring toggle while processing")
                return
                
            if not self.recording:
                self.start_recording()
            else:
                self.stop_recording()
        except Exception as e:
            logging.error(f"Error in toggle_recording: {str(e)}", exc_info=True)
            
    def start_recording(self):
        try:
            if self.recording or self.processing:
                logging.debug("Ignoring start_recording while already recording/processing")
                return
                
            logging.debug("Starting recording")
            self.recording = True
            self.frames = []
            self.start_time = time.time()
            
            if self.stream is not None:
                try:
                    logging.debug("Cleaning up existing stream")
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    logging.error(f"Error cleaning up stream: {str(e)}", exc_info=True)
                self.stream = None
            
            self.record_button.configure(
                text="Stop Recording",
                fg_color="#cc3333",
                hover_color="#992222"
            )
            self.status_label.configure(text="Recording in progress...")
            self.latest_text.delete("1.0", "end")
            
            logging.debug("Opening new audio stream")
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            logging.debug("Starting recording thread")
            self.current_recording_thread = threading.Thread(target=self.record_audio)
            self.current_recording_thread.start()
            
            self.update_timer()
            logging.info("Started recording")
        except Exception as e:
            logging.error(f"Error in start_recording: {str(e)}", exc_info=True)
            self.cleanup_recording()
            
    def cleanup_recording(self):
        try:
            logging.debug("Cleaning up recording state")
            self.recording = False
            self.start_time = None
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    logging.error(f"Error closing stream during cleanup: {str(e)}", exc_info=True)
                self.stream = None
        except Exception as e:
            logging.error(f"Error in cleanup_recording: {str(e)}", exc_info=True)
            
    def record_audio(self):
        try:
            logging.debug("Starting audio recording loop")
            while self.recording and (time.time() - self.start_time) < self.max_duration:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                except Exception as e:
                    logging.error(f"Error reading audio data: {str(e)}", exc_info=True)
                    break
                    
            logging.debug("Recording loop ended")
            if (time.time() - self.start_time) >= self.max_duration:
                logging.info("Max duration reached")
                self.window.after(0, self.stop_recording)
        except Exception as e:
            logging.error(f"Error in record_audio thread: {str(e)}", exc_info=True)
        finally:
            if self.recording:
                logging.debug("Forcing recording cleanup from thread")
                self.window.after(0, self.cleanup_recording)
                self.window.after(0, self.reset_ui)
            
    def stop_recording(self):
        try:
            if not self.recording:
                logging.debug("Ignoring stop_recording while not recording")
                return
                
            logging.debug("Stopping recording")
            self.recording = False
            self.processing = True
            
            self.record_button.configure(
                text="Processing...",
                state="disabled",
                fg_color="#666666",
                hover_color="#666666"
            )
            self.status_label.configure(text="Processing audio...")
            
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
                except Exception as e:
                    logging.error(f"Error closing stream: {str(e)}", exc_info=True)
            
            logging.debug("Starting process_recording thread")
            threading.Thread(target=self.process_recording).start()
        except Exception as e:
            logging.error(f"Error in stop_recording: {str(e)}", exc_info=True)
            self.cleanup_recording()
            self.reset_ui()
            
    def process_recording(self):
        try:
            logging.debug("Processing recording")
            self.save_and_transcribe()
        except Exception as e:
            logging.error(f"Error in process_recording: {str(e)}", exc_info=True)
        finally:
            logging.debug("Resetting UI after processing")
            self.window.after(0, self.reset_ui)
            
    def save_and_transcribe(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recordings_dir, f"recording_{timestamp}.wav")
            txt_filename = os.path.join(self.recordings_dir, f"transcript_{timestamp}.txt")
            
            logging.debug(f"Saving WAV file: {filename}")
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            logging.debug("Starting transcription")
            transcription = self.transcriber.transcribe(filename)
            
            if transcription:
                logging.debug("Saving transcript")
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                
                self.window.after(0, lambda: self.update_transcription(transcription))
                logging.info(f"Successfully transcribed recording: {filename}")
            else:
                logging.error("Transcription failed or returned empty")
                
            try:
                os.remove(filename)
                logging.debug("Removed WAV file")
            except Exception as e:
                logging.warning(f"Could not remove temporary file {filename}: {str(e)}")
                
        except Exception as e:
            logging.error(f"Error in save_and_transcribe: {str(e)}", exc_info=True)
            
    def update_transcription(self, text):
        self.latest_text.delete("1.0", "end")
        self.latest_text.insert("1.0", text)
        
        if self.auto_copy.get():
            pyperclip.copy(text)
            
        self.add_transcription(text)
        
    def add_transcription(self, text, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        frame = ctk.CTkFrame(
            self.transcription_frame,
            fg_color="#2a2a2a",
            corner_radius=10
        )
        # Pack at the beginning of the frame
        frame.pack(fill="x", padx=10, pady=5, side="top")
        
        time_label = ctk.CTkLabel(
            frame,
            text=timestamp,
            font=("Segoe UI", 10),
            text_color="#666666"
        )
        time_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        text_label = ctk.CTkLabel(
            frame,
            text=text,
            font=("Segoe UI", 12),
            text_color="#ffffff",
            wraplength=680,
            justify="left"
        )
        text_label.pack(padx=15, pady=(0, 10), anchor="w")
        
        copy_button = ctk.CTkButton(
            frame,
            text="Copy",
            width=80,
            height=28,
            corner_radius=14,
            font=("Segoe UI", 11),
            fg_color="#333333",
            hover_color="#444444",
            command=lambda: self.copy_text(text)
        )
        copy_button.pack(anchor="e", padx=15, pady=(0, 10))
        
        # Add to transcriptions list at the beginning
        self.transcriptions.insert(0, {"timestamp": timestamp, "text": text})
        self.save_history()
        
    def copy_text(self, text):
        pyperclip.copy(text)
        
    def load_history(self):
        history_file = os.path.join(self.recordings_dir, "history.txt")
        try:
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Process lines in chronological order (oldest to newest)
                    for line in lines:
                        timestamp, text = line.strip().split("|", 1)
                        self.add_transcription(text, timestamp)
                        
                    # Set the latest transcription
                    if lines:
                        _, latest_text = lines[-1].strip().split("|", 1)
                        self.latest_text.delete("1.0", "end")
                        self.latest_text.insert("1.0", latest_text)
        except Exception as e:
            logging.error(f"Error loading history: {str(e)}")
            
    def save_history(self):
        history_file = os.path.join(self.recordings_dir, "history.txt")
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                # Save in chronological order (oldest first)
                for item in reversed(self.transcriptions):
                    f.write(f"{item['timestamp']}|{item['text']}\n")
        except Exception as e:
            logging.error(f"Error saving history: {str(e)}")
            
    def reset_ui(self):
        try:
            logging.debug("Resetting UI")
            self.processing = False
            self.record_button.configure(
                text="Start Recording",
                state="normal",
                fg_color="#2d5a88",
                hover_color="#1d3a58"
            )
            self.status_label.configure(text="")
            self.indicator.set(0)
            self.timer_label.configure(text="0:00")
        except Exception as e:
            logging.error(f"Error in reset_ui: {str(e)}", exc_info=True)
            
    def on_closing(self):
        try:
            logging.debug("Application closing")
            keyboard.unhook_all()
            
            if self.recording:
                self.stop_recording()
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.p.terminate()
            logging.debug("Cleanup completed")
            self.window.destroy()
        except Exception as e:
            logging.error(f"Error during application shutdown: {str(e)}", exc_info=True)
            self.window.destroy()
        
    def update_timer(self):
        if self.recording:
            elapsed = int(time.time() - self.start_time)
            remaining = self.max_duration - elapsed
            if remaining >= 0:
                self.timer_label.configure(text=f"{remaining // 60}:{remaining % 60:02d}")
                self.indicator.set(elapsed / self.max_duration)
                self.window.after(100, self.update_timer)
            
    def hide_console(self):
        """Hide the console window"""
        console_window = KERNEL32.GetConsoleWindow()
        if console_window:
            USER32.ShowWindow(console_window, SW_HIDE)
            self.show_console.set(False)
            
    def show_console_window(self):
        """Show the console window"""
        console_window = KERNEL32.GetConsoleWindow()
        if console_window:
            USER32.ShowWindow(console_window, SW_SHOW)
            
    def toggle_console(self):
        """Toggle console visibility based on checkbox state"""
        if self.show_console.get():
            self.show_console_window()
        else:
            self.hide_console()
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = WhisperRecorderApp()
    app.run() 
