import os
import subprocess
import logging
from typing import Optional

class WhisperTranscriber:
    def __init__(self, model_path: str = "models/ggml-base.en.bin"):
        self.whisper_path = os.path.join(os.path.dirname(__file__), "whisper.cpp")
        self.model_path = os.path.join(self.whisper_path, model_path)
        self.executable = os.path.join(self.whisper_path, "build", "bin", "Release", "whisper-cli.exe")
        
        if not os.path.exists(self.executable):
            logging.error(f"Whisper executable not found at {self.executable}")
            raise FileNotFoundError(f"Whisper executable not found. Please compile whisper.cpp first.")
            
        if not os.path.exists(self.model_path):
            logging.error(f"Model not found at {self.model_path}")
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
            
    def transcribe(self, audio_path: str) -> Optional[str]:
        try:
            output_base = audio_path.rsplit(".", 1)[0]
            
            # Run whisper.cpp command with better parameters
            cmd = [
                self.executable,
                "-m", self.model_path,
                "-f", audio_path,
                "-otxt",         # Output as text
                "-pp",          # Print progress
                "-l", "en",     # English language
                "-t", "4",      # Use 4 threads
                "--output-file", output_base  # Base name for output files
            ]
            
            logging.info(f"Running Whisper command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # The output will be in a .txt file
            txt_path = output_base + ".txt"
            
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    transcription = f.read().strip()
                    
                # Clean up the text file
                try:
                    os.remove(txt_path)
                except Exception as e:
                    logging.warning(f"Could not remove temporary file {txt_path}: {str(e)}")
                    
                return transcription
            else:
                logging.error("Transcription file not found after processing")
                return None
                
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running Whisper: {str(e)}")
            logging.error(f"Whisper stderr: {e.stderr}")
            return None
        except Exception as e:
            logging.error(f"Error during transcription: {str(e)}")
            return None 