import wave
import struct
import math
import numpy as np

# Encoding and decoding parameters
RATE = 44100        # Sampling rate
DURATION = 0.01     # Duration of each bit in seconds
FREQ_ONE = 19000    # Frequency for binary '1' (changed to 19000 Hz)
FREQ_ZERO = 20000   # Frequency for binary '0' (changed to 20000 Hz)
AMPLITUDE = 32767   # Max amplitude for 16-bit audio

# Function to encode data to audio file
def encode_binary_to_audio(data, filename):
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(RATE)
        
        # Convert data to binary string
        binary_data = ''.join(format(byte, '08b') for byte in data)
        
        # Encode each bit as a frequency
        for bit in binary_data:
            freq = FREQ_ONE if bit == '1' else FREQ_ZERO
            samples = []
            for i in range(int(RATE * DURATION)):
                sample = AMPLITUDE * math.sin(2 * math.pi * freq * (i / RATE))
                samples.append(int(sample))
            
            # Write samples to WAV file
            wav_file.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

    print(f"Encoding complete. Audio saved to {filename}")

# Function to decode audio file back to binary data
def decode_audio_to_binary(filename):
    with wave.open(filename, 'r') as wav_file:
        frames_per_bit = int(RATE * DURATION)
        decoded_bits = []
        
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

# Main function to run encoding and decoding
if __name__ == "__main__":
    # Prompt user for the file to encode
    input_data_filename = input("Enter the filename containing data to encode: ")
    with open(input_data_filename, 'rb') as file:
        data = file.read()
    
    # Prompt for the name of the audio file to save
    encoded_filename = input("Enter the filename to save encoded audio (e.g., binary_encoded.wav): ")
    
    # Encode the data into an audio file
    encode_binary_to_audio(data, encoded_filename)
    
    # Prompt the user for the audio file to decode and where to save the output
    input_audio_filename = input("Enter the filename of the audio file to decode: ")
    output_data_filename = input("Enter the filename to save decoded data: ")
    
    # Decode the specified audio file back to binary data
    decoded_data = decode_audio_to_binary(input_audio_filename)
    
    # Save decoded data to specified file
    with open(output_data_filename, 'wb') as output_file:
        output_file.write(decoded_data)
    
    print(f"Decoded data saved to {output_data_filename}")
