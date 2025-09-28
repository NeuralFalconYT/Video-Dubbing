
from pipeline import WhisperDiarizationPipeline
import torch
import json

# Detect device and compute type automatically
if torch.cuda.is_available():
    device = "cuda"        # Use GPU if available
    compute_type = "float16"  # Use faster, lower-precision computation on GPU
elif torch.backends.mps.is_available():
    device = "mps"         # Apple GPU (Metal)
    compute_type = "float16"
else:
    device = "cpu"         # Fallback to CPU
    compute_type = "int8"  # Low-memory, quantized CPU computation

# Initialize Whisper + Diarization pipeline
pipeline = WhisperDiarizationPipeline(
    device=device,  # hardware to run model on
    compute_type=compute_type,  # model precision / speed
    model_name="deepdml/faster-whisper-large-v3-turbo-ct2"  # model variant
)

# Run prediction on the audio file
result = pipeline.predict(
    file_string=None,             # Optional: raw audio as base64 string (not used here)
    file_url=None,                # Optional: URL of audio file to download (not used)
    file_path="/content/test.mp3",  # Path to local audio file
    num_speakers=None,            # Number of speakers; None = auto-detect
    translate=False,              # True = convert audio to English; False = keep original language
    language="en",                # Force transcription in a specific language; None = auto-detect
    prompt=None,                  # Optional text prompt for better transcription context
    preprocess=0,                 # Audio preprocessing level (0 = none, 1-4 = increasing filtering/denoise)
    highpass_freq=45,             # High-pass filter frequency (Hz) to remove low rumble
    lowpass_freq=8000,            # Low-pass filter frequency (Hz) to remove high-frequency noise
    prop_decrease=0.3,            # Noise reduction proportion (higher = more aggressive)
    stationary=True,              # Assume background noise is stationary (True/False)
    target_dBFS=-18.0             # Normalize audio loudness to this dBFS level
)

# Save result to JSON file
with open("output.json", "w") as f:
    json.dump(result.to_dict(), f, indent=2)

print("✅ Done. Output saved to output.json")
print(result.to_dict())
