import os
import re
import sys
from pathlib import Path

def configure_paths():
    print("\n=== Whisper Recorder Setup ===")
    print("\nThis script will configure the application for your system.")
    
    # Get the current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    print(f"\nCurrent installation directory: {current_dir}")
    print("\nPress Enter to use this directory or input a different path:")
    
    user_path = input().strip()
    install_path = user_path if user_path else current_dir
    install_path = os.path.abspath(install_path)
    
    if not os.path.exists(install_path):
        try:
            os.makedirs(install_path)
        except Exception as e:
            print(f"Error creating directory: {e}")
            sys.exit(1)
    
    # Files to update
    files_to_update = [
        'whisper_recorder.py',
        'whisper_cpp_wrapper.py',
        'run_whisper.bat',
        'run_whisper_admin.bat'
    ]
    
    # Create recordings directory
    recordings_dir = os.path.join(install_path, "recordings")
    os.makedirs(recordings_dir, exist_ok=True)
    
    # Update paths in files
    for filename in files_to_update:
        filepath = os.path.join(install_path, filename)
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace paths
        content = content.replace(r'E:\Cursor\Whisper', install_path.replace('\\', '/'))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("\nConfiguration complete!")
    print(f"Installation directory: {install_path}")
    print("\nNext steps:")
    print("1. Download the Whisper model file (ggml-base.en.bin)")
    print("2. Place it in the whisper.cpp/models directory")
    print("3. Run run_whisper.bat to start the application")
    print("\nFor more details, please refer to the README.md file.")

if __name__ == "__main__":
    configure_paths() 