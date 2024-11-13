# TranSSound

TranSSound is a Python application that encodes binary data into high-frequency audio signals and decodes it back into binary form. By converting binary data into audio frequencies that are undetectable to the human ear, TranSSound enables discrete audio data transmission. Unique start and end markers ensure accurate data transmission and decoding.

## 🚀 Features

- **Binary-to-Audio Encoding**: Encode text or binary files into audio using specific frequencies for binary bits.
- **Audio-to-Binary Decoding**: Decode binary data from a WAV audio file or real-time audio stream.
- **Custom Start/End Markers**: Start and end markers enhance transmission reliability by marking data boundaries.
- **Real-Time & File-Based Modes**: Transmit data via microphone/speaker in real-time or through audio files.
- **User-Friendly**: Prompts users to specify filenames for saving encoded/decoded data for easy file management.

## 🛠️ How It Works

### Encoding

1. **Input Data**: Users can input text or select a binary file to encode.
2. **Audio Signal Generation**: Each bit is represented by a specific frequency:
   - **`1`** bit ➔ 19 kHz tone
   - **`0`** bit ➔ 19.5 kHz tone
3. **Markers**: Start and end markers are unique frequency sequences that help identify data boundaries.
4. **Output**: The generated audio is saved as a WAV file, ready for playback or transmission.

### Decoding

1. **Audio Input**: TranSSound can decode from a real-time audio input or a WAV file.
2. **Marker Detection**: The app identifies the start marker to begin decoding and stops upon detecting the end marker.
3. **Binary Decoding**: Each frequency is mapped to its corresponding binary bit (`1` or `0`).
4. **Output**: Decoded binary data is saved as specified by the user.

## 📖 Getting Started

1. **Install Dependencies**:
    ```bash
    pip install numpy pyaudio
    ```
2. **Run the Program**:
    ```bash
    python tranSSound.py
    ```

## 💻 Usage

### Encoding

1. Run the program and select the encoding option.
2. Enter the data to encode (or select a file).
3. Specify a filename for the output audio file.

### Decoding

1. Run the program and select the decoding option.
2. Choose between real-time decoding or file-based decoding.
3. Specify the filename of the audio file (if file-based) and where to save the decoded data.

## ⚙️ Technical Details

- **Sampling Rate**: 44.1 kHz
- **Bit Duration**: 10 ms per bit
- **Binary Frequencies**:
  - Binary `1`: 19 kHz
  - Binary `0`: 19.5 kHz
- **Marker Frequencies**: Unique frequencies mark data start and end points, improving decoding reliability.

## ⚠️ Limitations

- **Noise Sensitivity**: Transmission may be affected by ambient noise. A quiet environment or direct audio input is recommended.
- **High Frequencies**: The selected high frequencies may not work on all devices due to hardware limitations.

## 🌟 Future Improvements
- Get real-time decoding working
- Enhanced noise filtering for real-time decoding in noisy environments.
- Improved marker detection and synchronization for more accurate data retrieval.

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).
