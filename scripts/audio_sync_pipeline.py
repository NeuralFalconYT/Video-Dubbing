import os
import shutil
import subprocess
import json
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import split_on_silence

# --- Helper functions 
def atempo_chain(factor):
    if 0.5 <= factor <= 2.0: return f"atempo={factor:.3f}"
    parts = []
    while factor > 2.0: parts.append("atempo=2.0"); factor /= 2.0
    while factor < 0.5: parts.append("atempo=0.5"); factor *= 2.0
    parts.append(f"atempo={factor:.3f}")
    return ",".join(parts)

def change_speed(input_file, output_file, speedup_factor):
    print(f"Applying speed factor {speedup_factor:.3f} to {os.path.basename(input_file)}")
    try:
        subprocess.run(
            ["ffmpeg", "-i", input_file, "-filter:a", atempo_chain(speedup_factor), output_file, "-y"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"FFmpeg speedup error: {e}. Falling back to Librosa.")
        try:
            y, sr = librosa.load(input_file, sr=None)
            y_stretched = librosa.effects.time_stretch(y, rate=speedup_factor)
            sf.write(output_file, y_stretched, sr)
        except Exception as e_librosa:
            print(f"Librosa speedup failed: {e_librosa}. Copying original file.")
            shutil.copy(input_file, output_file)

def remove_edge_silence(input_path, output_path, top_db=30):
    y, sr = librosa.load(input_path, sr=None)
    trimmed_audio, _ = librosa.effects.trim(y, top_db=top_db)
    sf.write(output_path, trimmed_audio, sr)
    return output_path

def reduce_internal_silence(file_path, output_path, min_silence_duration_ms=100, silence_reduction_ms=50):
    sound = AudioSegment.from_file(file_path, format="wav")
    audio_chunks = split_on_silence(sound, min_silence_len=min_silence_duration_ms, silence_thresh=-45, keep_silence=silence_reduction_ms)
    combined = AudioSegment.empty()
    for chunk in audio_chunks: combined += chunk
    combined.export(output_path, format="wav")
    return output_path



def dubbing_algorithm(segments_data, final_audio_save_path):
    """
    Processes and stitches TTS segments using a file-based approach to conserve memory.
    """
    temp_dir = "processed_segments"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    # This list will store the paths to the final processed audio files, not the audio data itself.
    processed_file_paths = []
    
    sorted_segments = sorted(segments_data.values(), key=lambda x: x['start'])

    for i, segment in enumerate(sorted_segments):
        # print(f"\n--- Processing Segment {i+1}/{len(sorted_segments)} ---")
        
        tts_path = segment['tts_path']
        actual_duration = segment['actual_duration']
        starting_silence_s = segment['starting_silence']
        
        if not os.path.exists(tts_path):
            # print(f"WARNING: TTS file not found for segment {i+1}: {tts_path}. Skipping.")
            continue
            
        if actual_duration <= 0.1:
             # print(f"WARNING: Segment {i+1} has near-zero duration ({actual_duration}s). Skipping.")
             continue

        # --- STAGE 1-3: Process each segment individually (this part is memory-safe) ---
        
        # Define paths for this segment's intermediate files
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

        # Step 3: Forced Synchronization
        speedup_factor = current_duration / actual_duration
        if abs(speedup_factor - 1.0) > 0.01:
            change_speed(temp_segment_path, final_timed_path, speedup_factor)
            temp_segment_path = final_timed_path
        else:
            shutil.copy(temp_segment_path, final_timed_path)
            temp_segment_path = final_timed_path
        
        # --- STAGE 4: Silence Padding & Path Collection ---
        
        # If there's starting silence, create a temporary silence file.
        if starting_silence_s > 0:
            silence_duration_ms = int(starting_silence_s * 1000)
            silence_file = AudioSegment.silent(duration=silence_duration_ms)
            silence_path = os.path.join(temp_dir, f"{i+1}_silence.wav")
            silence_file.export(silence_path, format="wav")
            # Add the path of the silence file to our list
            processed_file_paths.append(silence_path)
        
        # Add the path of the main processed audio segment to our list
        processed_file_paths.append(temp_segment_path)

    # --- STAGE 5: Final Concatenation using FFmpeg ---
    # print("\n--- All segments processed. Concatenating files using FFmpeg (Memory-Safe) ---")

    # Create the text file for FFmpeg's concat demuxer
    concat_list_path = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_list_path, "w") as f:
        for path in processed_file_paths:
            # FFmpeg requires paths to be properly quoted/escaped
            f.write(f"file '{os.path.abspath(path)}'\n")
    #Because sometime ffmpeg can't read another language
    ffmpeg_save_path=f"{temp_dir}/temp.wav"
    # Run the FFmpeg command
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-f", "concat",          # Use the concat demuxer
                "-safe", "0",            # Needed for absolute paths
                "-i", concat_list_path,  # The input list of files
                "-c", "copy",            # Copy the codec, don't re-encode (fast!)
                ffmpeg_save_path,   # The final output file
                "-y"                     # Overwrite output file if it exists
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        shutil.copy(ffmpeg_save_path, final_audio_save_path)
        # print(f"Successfully exported final dubbed audio track to: {final_audio_save_path}")
    except Exception as e:
        print(f"ERROR: FFmpeg concatenation failed: {e}")
    # --- Cleanup ---  
    shutil.rmtree(temp_dir)
    # print("Dubbing process complete.")

# --- Updated Main Execution Function ---
def audio_sync(json_path):
  with open(json_path, "r", encoding="utf-8") as f:
      json_data = json.load(f)
  save_path = json_data['save_path']
  segments = json_data['segments']
  
  # Call the dubbing_algorithm
  dubbing_algorithm(segments, save_path)
  
  # print(f"Save Path: {save_path}")
  return save_path

#Example
# from audio_sync_pipeline import audio_sync
# audio_sync("/content/Video-Dubbing/json_input.json")
