import os
import shutil
import subprocess
import json
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import split_on_silence

TARGET_SR = 48000  # 48 kHz

# --- Helper functions 
def atempo_chain(factor):
    if 0.5 <= factor <= 2.0:
        return f"atempo={factor:.3f}"
    parts = []
    while factor > 2.0:
        parts.append("atempo=2.0")
        factor /= 2.0
    while factor < 0.5:
        parts.append("atempo=0.5")
        factor *= 2.0
    parts.append(f"atempo={factor:.3f}")
    return ",".join(parts)

def change_speed(input_file, output_file, speedup_factor):
    print(f"{input_file} {speedup_factor}")
    try:
        command = [
            "ffmpeg", "-i", input_file,
            "-filter:a", atempo_chain(speedup_factor),
            "-ar", str(TARGET_SR),
            output_file, "-y"
        ]
        # print(" ".join(command))
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"⚠️ FFmpeg speedup error: {e}. Falling back to Librosa.")
        try:
            y, sr = librosa.load(input_file, sr=TARGET_SR)
            y_stretched = librosa.effects.time_stretch(y, rate=speedup_factor)
            sf.write(output_file, y_stretched, TARGET_SR)
        except Exception as e_librosa:
            print(f"⚠️ Librosa speedup failed: {e_librosa}. Copying original file.")
            shutil.copy(input_file, output_file)

def remove_edge_silence(input_path, output_path, top_db=30):
    y, sr = librosa.load(input_path, sr=TARGET_SR)
    trimmed_audio, _ = librosa.effects.trim(y, top_db=top_db)
    sf.write(output_path, trimmed_audio, TARGET_SR)
    return output_path

def reduce_internal_silence(file_path, output_path, min_silence_duration_ms=100, silence_reduction_ms=50):
    sound = AudioSegment.from_file(file_path, format="wav").set_frame_rate(TARGET_SR)
    audio_chunks = split_on_silence(
        sound, 
        min_silence_len=min_silence_duration_ms,
        silence_thresh=-45, 
        keep_silence=silence_reduction_ms
    )
    combined = AudioSegment.empty()
    for chunk in audio_chunks:
        combined += chunk
    combined.export(output_path, format="wav")
    return output_path


def make_silence(duration_sec, path):
    """Generate silent audio of given duration (sec)"""
    AudioSegment.silent(duration=duration_sec * 1000).export(path, format="wav")


# --- Core Algorithm
def dubbing_algorithm(segments_data, final_audio_save_path):
    """
    Processes and stitches TTS segments using a file-based approach to conserve memory.
    """
    temp_dir = "processed_segments"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    processed_file_paths = []
    sorted_segments = sorted(segments_data.values(), key=lambda x: x['start'])

    MIN_SPEED = 0.8  # <-- minimum playback speed limit
    MAX_SPEED=4 # <-- Skip tts with silence 
    for i, segment in enumerate(sorted_segments):
        tts_path = segment['tts_path']
        actual_duration = segment['actual_duration']
        starting_silence_s = segment['starting_silence']

        if not os.path.exists(tts_path):
            print(f"⚠️ WARNING: TTS file not found for segment {i+1}: {tts_path}. Skipping.")
            continue

        if actual_duration <= 0.1:
            print(f"⚠️ WARNING: Segment {i+1} has near-zero duration ({actual_duration}s). Skipping.")
            continue

        # --- Stage 1–3: Process segment ---
        temp_segment_path = tts_path
        trimmed_path = os.path.join(temp_dir, f"{i+1}_trimmed.wav")
        silence_reduced_path = os.path.join(temp_dir, f"{i+1}_silence_reduced.wav")
        final_timed_path = os.path.join(temp_dir, f"{i+1}_timed.wav")

        # Step 1: Trim edge silence
        remove_edge_silence(temp_segment_path, trimmed_path)
        temp_segment_path = trimmed_path
        current_duration = librosa.get_duration(path=temp_segment_path)

        # Step 2: Natural Compression
        if current_duration > actual_duration:
            reduce_internal_silence(temp_segment_path, silence_reduced_path)
            temp_segment_path = silence_reduced_path
            current_duration = librosa.get_duration(path=temp_segment_path)

        # Step 3: Forced Synchronization with min 0.5x cap
        speedup_factor = current_duration / actual_duration
        capped = False

        if speedup_factor < MIN_SPEED:
            print(f"⚠️ Segment {i+1}: Capping slow-down {speedup_factor:.2f}x → {MIN_SPEED:.2f}x")
            capped = True
            speedup_factor = MIN_SPEED

        
        # Normal Speed Up    
        if abs(speedup_factor - 1.0) > 0.01:
           change_speed(temp_segment_path, final_timed_path, speedup_factor)
        # Too aggressive → skip speech
        elif speedup_factor > MAX_SPEED:
            print(f"⚠️ Skipping segment {i+1}: required speed {speedup_factor:.2f}× exceeds max allowed {MAX_SPEED:.2f}....Using silence instead.")
            make_silence(actual_duration, final_timed_path)
        else:
            shutil.copy(temp_segment_path, final_timed_path)

        temp_segment_path = final_timed_path

        # --- Handle padding if capped slow-down ---
        if capped:
            new_duration = librosa.get_duration(path=temp_segment_path)
            silence_gap_s = actual_duration - new_duration

            if silence_gap_s > 0.01:
                silence_duration_ms = int(silence_gap_s * 1000)
                silence_segment = AudioSegment.silent(
                    duration=silence_duration_ms,
                    frame_rate=TARGET_SR
                )
                silence_path = os.path.join(temp_dir, f"{i+1}_extra_silence.wav")
                silence_segment.export(silence_path, format="wav")
                
                # Add both audio and silence
                processed_file_paths.append(temp_segment_path)
                processed_file_paths.append(silence_path)
                continue  # skip normal append

        # --- Stage 4: Prepend silence if needed ---
        if starting_silence_s > 0:
            silence_duration_ms = int(starting_silence_s * 1000)
            silence_file = AudioSegment.silent(duration=silence_duration_ms, frame_rate=TARGET_SR)
            silence_path = os.path.join(temp_dir, f"{i+1}_silence.wav")
            silence_file.export(silence_path, format="wav")
            processed_file_paths.append(silence_path)

        processed_file_paths.append(temp_segment_path)

    # --- Stage 5: Concatenate all ---
    concat_list_path = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_list_path, "w") as f:
        for path in processed_file_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")

    ffmpeg_save_path = f"{temp_dir}/temp.wav"
    try:
        join_command = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", concat_list_path, "-c", "copy", ffmpeg_save_path, "-y"
        ]
        subprocess.run(join_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.copy(ffmpeg_save_path, final_audio_save_path)
    except Exception as e:
        print(" ".join(join_command))
        print(f"❌ ERROR: FFmpeg concatenation failed: {e}")

# --- Wrapper function ---
def audio_sync(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    save_path = json_data['save_path']
    segments = json_data['segments']
    dubbing_algorithm(segments, save_path)
    return save_path

# Example usage:
# from audio_sync_pipeline import audio_sync
# audio_sync("/content/json_input.json")
