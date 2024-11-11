import wave
import struct
import math
import numpy as np
import pyaudio

# Encoding and decoding parameters
RATE = 44100        # Sampling rate
DURATION = 0.01     # Duration of each bit in seconds
FREQ_ONE = 19000    # Frequency for binary '1'
FREQ_ZERO = 19500   # Frequency for binary '0'
START_MARKER_FREQ = 15000  # Start marker frequency
END_MARKER_FREQ = 20000    # End marker frequency
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
        add_marker_to_audio(wav_file, START_MARKER_FREQ)

        # Convert data to binary string
        binary_data = ''.join(format(byte, '08b') for byte in data)
        
        # Encode each bit as a frequency
        for bit in binary_data:
            freq = FREQ_ONE if bit == '1' else FREQ_ZERO
            encode_bit(wav_file, freq)
        
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

# Function to skip over the start marker in the audio file
def skip_marker(wav_file, marker_freq):
    frames_per_bit = int(RATE * DURATION)
    while True:
        frames = wav_file.readframes(frames_per_bit)
        if not frames:
            break

        samples = np.frombuffer(frames, dtype=np.int16)
        fft_result = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_result), 1 / RATE)
        
        peak_freq = abs(freqs[np.argmax(np.abs(fft_result))])
        if abs(peak_freq - marker_freq) < 500:  # Tolerance for marker frequency
            break  # Start marker found, exit loop to start decoding

# Function to decode audio file back to binary data
def decode_audio_to_binary(filename):
    with wave.open(filename, 'r') as wav_file:
        frames_per_bit = int(RATE * DURATION)
        decoded_bits = []
        
        # First, read and skip the start marker
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

# Function to record audio and decode it in real-time
def record_audio():
    # Open a stream for audio recording
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=1024)
    
    decoded_bits = []
    while True:
        frames = stream.read(1024)
        samples = np.frombuffer(frames, dtype=np.int16)
        fft_result = np.fft.fft(samples)
        freqs = np.fft.fftfreq(len(fft_result), 1 / RATE)
        
        # Find the dominant frequency
        peak_freq = abs(freqs[np.argmax(np.abs(fft_result))])
        
        # Check for the start marker
        if abs(peak_freq - START_MARKER_FREQ) < 500:  # Tolerance for start marker frequency
            print("Start marker detected. Starting data transmission...")
            skip_marker(stream, START_MARKER_FREQ)  # Skip the start marker
            
        # Check for the end marker
        if abs(peak_freq - END_MARKER_FREQ) < 500:  # Tolerance for end marker frequency
            print("End marker detected. Ending data transmission.")
            break
        
        # Decode the data bits (1 or 0)
        if abs(peak_freq - FREQ_ONE) < abs(peak_freq - FREQ_ZERO):
            decoded_bits.append('1')
        else:
            decoded_bits.append('0')
    
    # Close the stream after recording
    stream.stop_stream()
    stream.close()
    
    # Convert the decoded bits to bytes
    binary_string = ''.join(decoded_bits)
    byte_chunks = [binary_string[i:i+8] for i in range(0, len(binary_string), 8)]
    decoded_data = bytes(int(byte, 2) for byte in byte_chunks if len(byte) == 8)
    
    return decoded_data

# Main function to run encoding and decoding
if __name__ == "__main__":
    action = input("Select an action (1 = Encode, 2 = Decode): ").strip()
    
    if action == "1":
        print("You selected encoding.")
        
        # Prompt user for the file to encode or real-time option
        mode = input("Choose encoding mode (1 = Real-time, 2 = File-based): ").strip()
        
        if mode == "1":
            input_data_filename = input("Enter the filename containing data to encode: ")
            with open(input_data_filename, 'rb') as file:
                data = file.read()
            
            # Encode the data to an audio file
            encoded_filename = input("Enter the filename to save encoded audio (e.g., binary_encoded.wav): ")
            encode_binary_to_audio(data, encoded_filename)
            
            # Play the encoded audio through speakers
            print("Playing encoded audio through speakers...")
            play_audio(encoded_filename)
        
        elif mode == "2":
            input_data_filename = input("Enter the filename containing data to encode: ")
            with open(input_data_filename, 'rb') as file:
                data = file.read()
            
            # Encode and save to file
            encoded_filename = input("Enter the filename to save encoded audio (e.g., binary_encoded.wav): ")
            encode_binary_to_audio(data, encoded_filename)
    
    elif action == "2":
        print("You selected decoding.")
        
        # Prompt for the real-time option
        mode = input("Choose decoding mode (1 = Real-time, 2 = File-based): ").strip()
        
        if mode == "1":
            decoded_data = record_audio()  # Record and decode real-time audio
            print("Decoded data:", decoded_data)
        
        elif mode == "2":
            input_audio_filename = input("Enter the filename of the audio file to decode: ")
            output_data_filename = input("Enter the filename to save decoded data: ")
            
            decoded_data = decode_audio_to_binary(input_audio_filename)
            
            # Save decoded data to file
            with open(output_data_filename, 'wb') as output_file:
                output_file.write(decoded_data)
            print(f"Decoded data saved to {output_data_filename}")
    
    else:
        print("Invalid option. Please restart and select a valid action.")