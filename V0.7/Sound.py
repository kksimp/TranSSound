import wave
import struct
import math
import numpy as np
import pyaudio
import threading
import time
import sys

# Encoding and decoding parameters
RATE = 44100        # Sampling rate
DURATION = 0.01     # Duration of each bit in seconds
FREQ_ONE = 19000    # Frequency for binary '1'
FREQ_ZERO = 19500   # Frequency for binary '0'
START_MARKER_FREQS = [15000, 17000, 15500, 17500, 15000, 17000, 15500, 17500]  # Sequence for start marker
END_MARKER_FREQS = [20000, 17000, 20000, 17500, 15000, 17000, 20000, 17500]    # Sequence for end marker
AMPLITUDE = 32767   # Max amplitude for 16-bit audio

# PyAudio setup for real-time audio playback and recording
p = pyaudio.PyAudio()

# Function to encode data to audio file with start and end markers
def encode_binary_to_audio(data, filename):
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(RATE)
        
        # Add start marker
        add_marker_to_audio(wav_file, START_MARKER_FREQS)

        # Convert data to binary string
        binary_data = ''.join(format(byte, '08b') for byte in data)
        
        # Encode each bit as a frequency
        for bit in binary_data:
            freq = FREQ_ONE if bit == '1' else FREQ_ZERO
            encode_bit(wav_file, freq)
        
        # Add end marker
        add_marker_to_audio(wav_file, END_MARKER_FREQS)

    print(f"Encoding complete. Audio saved to {filename}")

# Function to encode a single bit as a frequency in the WAV file
def encode_bit(wav_file, freq):
    samples = []
    for i in range(int(RATE * DURATION)):
        sample = AMPLITUDE * math.sin(2 * math.pi * freq * (i / RATE))
        samples.append(int(sample))
    wav_file.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

# Function to add a sequence of marker frequencies to the audio file (start or end)
def add_marker_to_audio(wav_file, marker_freqs):
    for marker_freq in marker_freqs:
        samples = []
        for i in range(int(RATE * DURATION)):
            sample = AMPLITUDE * math.sin(2 * math.pi * marker_freq * (i / RATE))
            samples.append(int(sample))
        wav_file.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

# Function to detect and skip the entire marker sequence (start or end) from a file-based WAV
def skip_marker_file_based(wav_file, marker_freqs):
    frames_per_bit = int(RATE * DURATION)
    marker_index = 0
    while True:
        frames = wav_file.readframes(frames_per_bit)
        if not frames:
            break

        samples = np.frombuffer(frames, dtype=np.int16)
        fft_result = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_result), 1 / RATE)
        
        peak_freq = abs(freqs[np.argmax(np.abs(fft_result))])
        
        # Check if the peak frequency matches the current marker
        if abs(peak_freq - marker_freqs[marker_index]) < 500:  # Tolerance for marker frequency
            marker_index += 1
            if marker_index == len(marker_freqs):  # All markers found
                break
        else:
            marker_index = 0  # Reset if the frequency does not match the expected marker

# Function to detect and skip the entire marker sequence (start or end) in real-time
def skip_marker_realtime(stream, marker_freqs):
    frames_per_bit = int(RATE * DURATION)
    marker_index = 0
    while True:
        frames = stream.read(1024)
        samples = np.frombuffer(frames, dtype=np.int16)
        fft_result = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_result), 1 / RATE)
        
        peak_freq = abs(freqs[np.argmax(np.abs(fft_result))])
        
        # Check if the peak frequency matches the current marker
        if abs(peak_freq - marker_freqs[marker_index]) < 500:  # Tolerance for marker frequency
            marker_index += 1
            if marker_index == len(marker_freqs):  # All markers found
                break
        else:
            marker_index = 0  # Reset if the frequency does not match the expected marker

# Function to decode audio from a file (file-based decoding)
def decode_audio_from_file(filename):
    with wave.open(filename, 'r') as wav_file:
        frames_per_bit = int(RATE * DURATION)
        decoded_bits = []
        
        # First, read and skip the start marker
        skip_marker_file_based(wav_file, START_MARKER_FREQS)

        while True:
            frames = wav_file.readframes(frames_per_bit)
            if not frames:
                break
            
            # Convert frames to numpy array
            samples = np.frombuffer(frames, dtype=np.int16)
            fft_result = np.fft.fft(samples)
            freqs = np.fft.fftfreq(len(fft_result), 1 / RATE)
            
            # Find the dominant frequency
            peak_freq = abs(freqs[np.argmax(np.abs(fft_result))])
            
            # Check for the end marker and stop decoding if found
            if any(abs(peak_freq - freq) < 500 for freq in END_MARKER_FREQS):  # Tolerance for end marker frequencies
                break

            # Determine if it's a '1' or '0'
            if abs(peak_freq - FREQ_ONE) < abs(peak_freq - FREQ_ZERO):
                decoded_bits.append('1')
            else:
                decoded_bits.append('0')
        
        # Convert binary string to bytes
        binary_string = ''.join(decoded_bits)
        byte_chunks = [binary_string[i:i+8] for i in range(0, len(binary_string), 8)]
        decoded_data = bytes(int(byte, 2) for byte in byte_chunks if len(byte) == 8)
    
    return decoded_data

# Function to decode audio in real-time
def decode_audio_in_real_time():
    # Open a stream for audio recording
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=1024)
    
    listening = False
    decoded_bits = []
    start_marker_detected = False

    while True:
        frames = stream.read(1024)
        samples = np.frombuffer(frames, dtype=np.int16)
        fft_result = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_result), 1 / RATE)
        
        # Find the dominant frequency
        peak_freq = abs(freqs[np.argmax(np.abs(fft_result))])

        # Check for start marker only after enough data is collected (avoid false positives)
        if not start_marker_detected:
            # Check if the start marker sequence is detected in order
            skip_marker_realtime(stream, START_MARKER_FREQS)
            print("Start marker detected. Starting data transmission...")
            listening = True
            decoded_bits = []  # Clear any previous data
            start_marker_detected = True
            time.sleep(1)  # Small delay to avoid false start detections
        
        # If we're listening, keep collecting the bits
        if listening:
            if any(abs(peak_freq - freq) < 500 for freq in END_MARKER_FREQS):
                print("End marker detected. Stopping data transmission.")
                break  # Stop when the end marker is detected
            
            if abs(peak_freq - FREQ_ONE) < abs(peak_freq - FREQ_ZERO):
                decoded_bits.append('1')
            else:
                decoded_bits.append('0')
    
    # Close the stream after listening
    stream.stop_stream()
    stream.close()
    
    # Convert the decoded bits to bytes
    binary_string = ''.join(decoded_bits)
    byte_chunks = [binary_string[i:i+8] for i in range(0, len(binary_string), 8)]
    decoded_data = bytes(int(byte, 2) for byte in byte_chunks if len(byte) == 8)
    
    print("Decoded data:", decoded_data)
    return decoded_data

# Save decoded data to a file
def save_decoded_data(decoded_data):
    filename = input("Enter the filename to save the decoded data: ").strip()
    with open(filename, 'wb') as file:
        file.write(decoded_data)
    print(f"Decoded data saved to {filename}")

# Main function to run encoding and decoding
if __name__ == "__main__":
    action = input("Select an action (1 = Encode, 2 = Decode): ").strip()
    
    if action == "1":
        print("You selected encoding.")
        
        # Prompt user for the file to encode or real-time option
        mode = input("Choose encoding mode (1 = Real-time, 2 = File-based): ").strip()
        
        if mode == "1":
            input_data = input("Enter text data to encode: ").strip()
            data_to_encode = input_data.encode('utf-8')
            filename = input("Enter the filename to save the encoded audio: ").strip()
            encode_binary_to_audio(data_to_encode, filename)
        
        elif mode == "2":
            input_data_filename = input("Enter the filename to read binary data to encode: ").strip()
            with open(input_data_filename, 'rb') as f:
                data_to_encode = f.read()
            filename = input("Enter the filename to save the encoded audio: ").strip()
            encode_binary_to_audio(data_to_encode, filename)
    
    elif action == "2":
        print("You selected decoding.")
        
        # Decode the audio from file or real-time
        mode = input("Choose decoding mode (1 = Real-time, 2 = File-based): ").strip()
        
        if mode == "1":
            decoded_data = decode_audio_in_real_time()
            save_decoded_data(decoded_data)
        
        elif mode == "2":
            filename = input("Enter the filename of the audio to decode: ").strip()
            decoded_data = decode_audio_from_file(filename)
            save_decoded_data(decoded_data)
