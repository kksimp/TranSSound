import wave
import struct
import math
import numpy as np
import time

# Encoding and decoding parameters
RATE = 44100        # Sampling rate
DURATION = 0.01     # Duration of each bit in seconds
FREQ_ONE = 19000    # Frequency for binary '1' (changed to 19000 Hz)
FREQ_ZERO = 19500   # Frequency for binary '0' (changed to 20000 Hz)
START_MARKER_FREQ = 15000  # Start marker frequency (unique frequency for the start)
END_MARKER_FREQ = 20000    # End marker frequency (unique frequency for the end)
AMPLITUDE = 32767   # Max amplitude for 16-bit audio

# Function to encode data to audio file with start and end markers
def encode_binary_to_audio(data, filename, real_time=False):
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(RATE)
        
        # Add start marker
        add_marker_to_audio(wav_file, START_MARKER_FREQ)

        # Convert data to binary string
        binary_data = ''.join(format(byte, '08b') for byte in data)
        
        # Encode each bit as a frequency
        for bit in binary_data:
            freq = FREQ_ONE if bit == '1' else FREQ_ZERO
            encode_bit(wav_file, freq)
            if real_time:
                time.sleep(DURATION)  # Simulate real-time encoding
        
        # Add end marker
        add_marker_to_audio(wav_file, END_MARKER_FREQ)

    print(f"Encoding complete. Audio saved to {filename}")

# Function to encode a single bit as a frequency in the WAV file
def encode_bit(wav_file, freq):
    samples = []
    for i in range(int(RATE * DURATION)):
        sample = AMPLITUDE * math.sin(2 * math.pi * freq * (i / RATE))
        samples.append(int(sample))
    wav_file.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

# Function to add a marker frequency to the audio file (start or end)
def add_marker_to_audio(wav_file, marker_freq):
    samples = []
    for i in range(int(RATE * DURATION)):
        sample = AMPLITUDE * math.sin(2 * math.pi * marker_freq * (i / RATE))
        samples.append(int(sample))
    wav_file.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

# Function to decode audio file back to binary data with start and end markers
def decode_audio_to_binary(filename):
    with wave.open(filename, 'r') as wav_file:
        frames_per_bit = int(RATE * DURATION)
        decoded_bits = []
        
        # First, read the start marker (skip start marker)
        skip_marker(wav_file, START_MARKER_FREQ)

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
            if abs(peak_freq - END_MARKER_FREQ) < 500:  # Tolerance for end marker frequency
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

# Function to skip the marker during decoding
def skip_marker(wav_file, marker_freq):
    frames_per_marker = int(RATE * DURATION)
    while True:
        frames = wav_file.readframes(frames_per_marker)
        if not frames:
            break
        
        samples = np.frombuffer(frames, dtype=np.int16)
        fft_result = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_result), 1 / RATE)
        
        peak_freq = abs(freqs[np.argmax(np.abs(fft_result))])
        if abs(peak_freq - marker_freq) < 500:  # Check if it's the marker frequency
            break

# Main function to run encoding and decoding
if __name__ == "__main__":
    action = input("Select an action (1 = Encode, 2 = Decode): ").strip()
    
    if action == "1":
        print("You selected encoding.")
        
        # Prompt user for the file to encode or real-time option
        mode = input("Choose encoding mode (1 = Real-time, 2 = File-based): ").strip()
        
        if mode == "1":
            data = b"Hello"  # Use a small data set for real-time testing
        else:
            input_data_filename = input("Enter the filename containing data to encode: ")
            with open(input_data_filename, 'rb') as file:
                data = file.read()
        
        # Prompt for the name of the audio file to save
        encoded_filename = input("Enter the filename to save encoded audio (e.g., binary_encoded.wav): ")
        
        # Encode the data into an audio file
        encode_binary_to_audio(data, encoded_filename, real_time=(mode=="1"))
    
    elif action == "2":
        print("You selected decoding.")
        
        # Prompt the user for the audio file to decode and where to save the output
        input_audio_filename = input("Enter the filename of the audio file to decode: ")
        output_data_filename = input("Enter the filename to save decoded data: ")
        
        # Decode the specified audio file back to binary data
        decoded_data = decode_audio_to_binary(input_audio_filename)
        
        # Save decoded data to specified file
        with open(output_data_filename, 'wb') as output_file:
            output_file.write(decoded_data)
        
        print(f"Decoded data saved to {output_data_filename}")
    
    else:
        print("Invalid option. Please restart and select a valid action.")
