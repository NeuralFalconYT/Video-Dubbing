import os
import shutil
import subprocess
import json
import librosa
import soundfile as sf
from pydub import AudioSegment

# Standard sample rate for video production
TARGET_SR = 48000 

def get_atempo_filter(speed_factor):
    """
    Generates an FFmpeg filter chain for time-stretching.
    FFmpeg 'atempo' is limited to 0.5 to 2.0. This chains them for larger changes.
    """
    if speed_factor == 1.0:
        return None
    
    factors = []
    remaining = speed_factor
    
    # Handle speed up (> 2.0x)
    while remaining > 2.0:
        factors.append("atempo=2.0")
        remaining /= 2.0
    
    # Handle slow down (< 0.5x)
    while remaining < 0.5:
        factors.append("atempo=0.5")
        remaining /= 0.5
        
    factors.append(f"atempo={remaining:.5f}")
    return ",".join(factors)

def process_segment_audio(input_path, output_path, target_duration_sec):
    """
    1. Trims silence from raw TTS.
    2. Stretches/Compresses audio to fit EXACTLY into the target video slot.
    3. Preserves pitch.
    """
    # --- Step 1: Load and Trim Silence (VAD) ---
    try:
        y, sr = librosa.load(input_path, sr=TARGET_SR)
    except Exception as e:
        print(f"❌ Error loading {input_path}: {e}")
        return False

    # trim silence (top_db=30 is standard for voice)
    y_trimmed, _ = librosa.effects.trim(y, top_db=30)
    
    # Save a temporary trimmed file
    temp_trim_path = output_path.replace(".wav", "_trim.wav")
    sf.write(temp_trim_path, y_trimmed, TARGET_SR)
    
    current_duration = librosa.get_duration(y=y_trimmed, sr=sr)
    
    # Safety: If audio is extremely short or target is 0, just copy
    if target_duration_sec <= 0.1 or current_duration <= 0.1:
        shutil.copy(temp_trim_path, output_path)
        if os.path.exists(temp_trim_path): os.remove(temp_trim_path)
        return True

    # --- Step 2: Calculate Speed Factor ---
    # Formula: speed = current_length / desired_length
    speed_factor = current_duration / target_duration_sec
    
    # CLAMPING: Prevent audio from becoming garbage.
    # We limit speedup to 2.5x and slowdown to 0.5x.
    # If it needs to go faster/slower than this, it's better to overlap/gap 
    # than to make the audio unintelligible.
    speed_factor = max(0.5, min(speed_factor, 2.5))

    # --- Step 3: Apply FFmpeg Time Stretch ---
    filter_str = get_atempo_filter(speed_factor)
    
    # If speed change is less than 2%, don't re-encode (preserves quality)
    if abs(speed_factor - 1.0) < 0.02:
        shutil.move(temp_trim_path, output_path)
    else:
        cmd = [
            "ffmpeg", "-v", "error", "-i", temp_trim_path,
            "-filter:a", filter_str,
            "-ar", str(TARGET_SR),
            output_path, "-y"
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print(f"⚠️ FFmpeg failed for segment. Using unstretched audio.")
            shutil.copy(temp_trim_path, output_path)
        
        # Cleanup temp trim file
        if os.path.exists(temp_trim_path):
            os.remove(temp_trim_path)
            
    return True

def dubbing_algorithm(segments_data, final_audio_save_path):
    """
    Timeline/Canvas approach:
    1. Create a blank silent audio track of the total duration.
    2. Process every segment to fit its specific time slot.
    3. Paste every segment at its exact START timestamp.
    """
    temp_dir = "processed_segments_temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    # Sort segments by start time
    sorted_segments = sorted(segments_data.values(), key=lambda x: x['start'])
    
    if not sorted_segments:
        print("❌ No segments found in JSON.")
        return

    # --- 1. Determine Total Duration & Create Canvas ---
    last_segment = sorted_segments[-1]
    # Add 2 seconds buffer at the end
    total_duration_sec = last_segment['start'] + last_segment['actual_duration'] + 2.0
    
    print(f"Creating Audio Canvas: {total_duration_sec:.2f} seconds...")
    
    # Create silent master track (pydub works in milliseconds)
    canvas = AudioSegment.silent(duration=int(total_duration_sec * 1000), frame_rate=TARGET_SR)

    # --- 2. Process & Overlay Loop ---
    for i, segment in enumerate(sorted_segments):
        tts_path = segment['tts_path']
        start_time_sec = segment['start']
        target_duration = segment['actual_duration']
        
        if not os.path.exists(tts_path):
            print(f"⚠️ Warning: File not found {tts_path}")
            continue

        # Define temporary output filename
        processed_path = os.path.join(temp_dir, f"seg_{i}.wav")
        
        # A. Process Audio (Trim -> Stretch -> Save to processed_path)
        success = process_segment_audio(tts_path, processed_path, target_duration)
        
        if success and os.path.exists(processed_path):
            # B. Load processed audio
            audio_clip = AudioSegment.from_wav(processed_path)
            
            # C. Apply Micro-Fade (2ms)
            # This removes the "digital click" without eating the words.
            audio_clip = audio_clip.fade_in(2).fade_out(2)
            
            # D. Overlay onto Canvas at EXACT timestamp
            # This ensures 0% drift. Segment 100 will be perfectly synced.
            position_ms = int(start_time_sec * 1000)
            canvas = canvas.overlay(audio_clip, position=position_ms)
            
            # Optional: Log progress
            # print(f"Synced Segment {i+1}/{len(sorted_segments)} at {start_time_sec}s")

    # --- 3. Export Final Audio ---
    print(f"💾 Exporting final dubbed audio to: {final_audio_save_path}")
    canvas.export(final_audio_save_path, format="wav")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print("✅ Dubbing process completed successfully.")

def audio_sync(json_path):
    """
    Wrapper function to be called from other scripts.
    """
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    
    save_path = json_data['save_path']
    segments = json_data['segments']
    
    dubbing_algorithm(segments, save_path)
    return save_path

# --- Execution Block (for testing) ---
if __name__ == "__main__":
    # You can test the script directly by providing a JSON file path here
    # example_json = "input_data.json"
    # audio_sync(example_json)
    pass
