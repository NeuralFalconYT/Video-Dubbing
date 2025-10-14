#@title  utils for cleaning llm json translation and get extract speakers from media file

# %%writefile /content/Video-Dubbing/utils.py

import subprocess
import os 
import math
import shutil
import random
def update_speaker_speeds(dubbing_json, default_speaker_voice, default_tts_rate=14):
    """
    Calculate the average speaking speed for each speaker based on the dubbing JSON
    and update the default_speaker_voice dictionary with a relative TTS speed factor.

    Args:
        dubbing_json (dict): Dictionary containing segments with keys:
            - 'text': original or dubbed text
            - 'start': segment start time in seconds
            - 'end': segment end time in seconds
            - 'speaker_id': ID of the speaker
        default_speaker_voice (dict): Dictionary with speaker_id as key containing:
            - 'referece_audio': path to reference audio
            - 'fixed_seed': TTS seed
        default_tts_rate (float, optional): Default chars/sec rate of TTS engine.
            Defaults to 14.

    Returns:
        dict: Updated default_speaker_voice with an additional key 'avg_talk_speed'
            for each speaker, representing the relative TTS speed factor (e.g., 1.0x, 1.2x)
    """
    # Store total chars and total time per speaker
    speaker_stats = {}

    for seg in dubbing_json.values():
        speaker_id = seg["speaker_id"]
        duration = seg["end"] - seg["start"]
        char_count = len(seg["text"].replace(" ", ""))

        if duration > 0 and char_count > 0:
            if speaker_id not in speaker_stats:
                speaker_stats[speaker_id] = {"chars": 0, "time": 0.0}
            speaker_stats[speaker_id]["chars"] += char_count
            speaker_stats[speaker_id]["time"] += duration

    # Calculate average speed for each speaker
    for spk_id, stats in speaker_stats.items():
        avg_speed = stats["chars"] / stats["time"] if stats["time"] > 0 else default_tts_rate
        if spk_id in default_speaker_voice:
            speed_factor = avg_speed / default_tts_rate if default_tts_rate > 0 else 1.0
            talk_speed = math.floor(speed_factor * 100) / 100  # Truncate to 2 decimal places
            default_speaker_voice[spk_id]["avg_talk_speed"] = talk_speed

    return default_speaker_voice


def get_speaker_from_media(media_file,json_data):
  if media_file is None:
    media_file=""
  segments = sorted(json_data.values(), key=lambda x: x['start'])
  merged = []
  current_speaker, start, end = None, None, None

  for seg in segments:
      spk = seg['speaker_id']
      if spk == current_speaker:
          end = seg['end']
      else:
          if current_speaker is not None:
              merged.append((start, end, current_speaker))
          current_speaker = spk
          start, end = seg['start'], seg['end']

  if current_speaker is not None:
      merged.append((start, end, current_speaker))

  # --- Step 2: find max speaking duration for each speaker ---
  max_turns = {}
  for s, e, spk in merged:
      dur = e - s
      if spk not in max_turns or dur > (max_turns[spk][1] - max_turns[spk][0]):
          max_turns[spk] = (s, e)

  # print("Max speaking interval per speaker:")
  # print(max_turns)

  _, extension = os.path.splitext(media_file)
  if extension.lower() == ".mp4":
    temp_mp3_file = "convert.mp3"
    try:
      subprocess.run(
          ["ffmpeg", "-y", "-i", media_file, temp_mp3_file],
          check=True,
          stdout=subprocess.DEVNULL,  # hide normal output
          stderr=subprocess.DEVNULL   # hide error/progress output
      )
      print("Speaker Extraction Successful")
    except subprocess.CalledProcessError:
      print("Failed Video to audio conversion")
    media_file = temp_mp3_file
    extension=".mp3"

  speaker_voices={}
  if os.path.exists("./speaker_voice"):
    shutil.rmtree("./speaker_voice")
  os.makedirs("./speaker_voice")
  for i in max_turns:
    start = max_turns[i][0]
    end = max_turns[i][1]
    duration = end - start

    try:
        output_file=f"./speaker_voice/{i}{extension}"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", media_file,
                "-ss", str(start), "-t", str(duration),
                "-c", "copy", output_file
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if os.path.exists(output_file):
          seed_num_input = random.randint(1, 999999)
          speaker_voices[i]={"reference_audio":output_file,
                             "fixed_seed":seed_num_input}
    except subprocess.CalledProcessError:
        print(f"Failed Speaker {i} audio extraction")
        seed_num_input = random.randint(1, 999999)
        speaker_voices[i]={"reference_audio":"",
                             "fixed_seed":seed_num_input}
  speaker_voices=update_speaker_speeds(json_data, speaker_voices)
  return speaker_voices




def merge_short_silences(dubbing_json, silence_threshold=1.0, max_merged_duration=12.0):
    """
    Merge consecutive segments if:
      - they have the same speaker_id AND
      - the silence gap (next.start - curr.end) < silence_threshold
      - AND the merged duration does not exceed max_merged_duration

    Returns a new dict with sequential string keys '1','2',...
    Recalculates starting_silence relative to previous merged segment end.
    """
    keys = sorted(dubbing_json.keys(), key=lambda k: int(k))
    merged_segments = []
    i = 0
    n = len(keys)

    while i < n:
        curr = dict(dubbing_json[keys[i]])  # copy
        j = i + 1

        # Try to merge following segments
        while j < n:
            nxt = dubbing_json[keys[j]]
            gap = nxt["start"] - curr["end"]
            new_duration = nxt["end"] - curr["start"]

            if (
                nxt["speaker_id"] == curr["speaker_id"]
                and gap < silence_threshold
                and new_duration <= max_merged_duration
            ):
                # Merge: concat text and extend end/duration
                curr["text"] = curr["text"].rstrip() + " " + nxt["text"].lstrip()
                curr["end"] = nxt["end"]
                curr["duration"] = new_duration
                j += 1
            else:
                break

        merged_segments.append(curr)
        i = j

    # Recompute starting_silence
    result = {}
    prev_end = 0.0
    for idx, seg in enumerate(merged_segments, start=1):
        seg_start = seg["start"]
        seg_end = seg["end"]
        seg["starting_silence"] = seg_start - prev_end
        seg["duration"] = seg_end - seg_start
        result[str(idx)] = seg
        prev_end = seg_end

    return result


def get_dubbing_json(raw_json, silence_threshold=0.6, max_merged_duration=10.0):
    """
    Build normalized dubbing JSON and compute starting_silence = start - previous_end.
    Keys in returned dict are '1','2',... in chronological order.
    """
    dubbing_json = {}
    prev_end = 0.0

    keys = sorted(raw_json.keys(), key=lambda k: int(k))  # numeric order
    for out_idx, k in enumerate(keys, start=1):
        item = raw_json[k]
        raw_text = item.get("text", "")
        dubbing_text = item.get("dubbing", "")
        speaker_id = item.get("speaker_id")
        start = float(item.get("start", 0.0))
        end = float(item.get("end", start))
        duration = end - start

        # Correct starting_silence: gap between this start and previous segment's end
        starting_silence = start - prev_end
        prev_end = end

        text = dubbing_text if dubbing_text else raw_text

        dubbing_json[str(out_idx)] = {
            "text": text,
            "starting_silence": starting_silence,
            "start": start,
            "end": end,
            "duration": duration,
            "speaker_id": speaker_id,
            }
    fixed_dubbing_json=merge_short_silences(dubbing_json, silence_threshold, max_merged_duration)
    return fixed_dubbing_json

import os
from pydub import AudioSegment
import subprocess
import shutil

def convert_to_mono(media_file):
    folder, filename = os.path.split(media_file)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    # Supported formats
    if ext not in [".mp3", ".wav", ".mp4", ".mkv"]:
        print("Unsupported file type. Returning original file.")
        return media_file

    # Output folder
    folder_name = "./audio_separation"
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
    os.makedirs(folder_name, exist_ok=True)

    temp_file = os.path.join(folder_name, f"{name}_mono.mp3" if ext in [".mp4", ".mkv"] else f"{name}_mono{ext}")
    safe_file = os.path.join(folder_name, "temp.mp3")

    # Case 1: Video file → extract audio and convert to mono
    if ext in [".mp4", ".mkv"]:
        print(f"Detected video ({ext}). Extracting audio and converting to mono...")
        try:
            cmd = [
                "ffmpeg",
                "-i", media_file,
                "-ac", "1",       # force mono
                "-y",             # overwrite
                safe_file
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            shutil.copy(safe_file, temp_file)
        except subprocess.CalledProcessError:
            print("FFmpeg failed. Returning original file.")
            return media_file

    # Case 2: Audio file
    else:
        try:
            audio = AudioSegment.from_file(media_file)
            if audio.channels > 1:
                print(f"Audio has {audio.channels} channels. Converting to mono...")
                audio = audio.set_channels(1)
            else:
                print("Audio is already mono.")
            audio.export(temp_file, format=ext[1:])  # remove dot
        except Exception as e:
            print(f"Error processing audio: {e}")
            return media_file

    return os.path.abspath(temp_file)





from pydub import AudioSegment
from librosa import get_duration
def combine_audios(audio_files, output_path="./new.wav"):
    if not audio_files:
        raise ValueError("No audio files provided!")

    # Load the first file
    combined = AudioSegment.from_file(audio_files[0])

    # Append the rest
    for file_path in audio_files[1:]:
        audio = AudioSegment.from_file(file_path)
        combined += audio  # Concatenate

    # Export to new file
    combined.export(output_path, format="wav")
    return output_path

def seperate_audio(audio_path):
  instrumental_path=""
  vocal_path=audio_path
  save_dir="./audio_separation" 
  if os.path.exists(save_dir):
    shutil.rmtree(save_dir)
  os.makedirs(save_dir, exist_ok=True)
  command=f"audio-separator {audio_path} --model_filename Kim_Vocal_2.onnx --output_format mp3 --output_dir {save_dir}"
  var=os.system(command)
  if var==0:
    for i in os.listdir(save_dir):
      if "(Instrumental)" in i:
        instrumental_path=f"{save_dir}/{i}"
      elif "(Vocals)" in i:
        vocal_path=f"{save_dir}/{i}"

  return vocal_path,instrumental_path


import os
import shutil
import subprocess
from pathlib import Path

def demucs_separate_vocal_music(file_path, model_name="htdemucs_ft", output_dir="separated_output"):
    duration=get_media_duration(file_path)
    max_duration=10*60 #10 min
    if duration>max_duration:
        model_name="htdemucs"
        
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "python", "-m", "demucs",
        "--two-stems=vocals",
        "-o", output_dir,
        "-d", "cuda",
        file_path,
        "-n", model_name,
    ]

    print("🎧 Running Demucs...")
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"❌ Demucs failed: {e}")
        return file_path, None

    file_name = Path(file_path).stem
    model_dir = f"./{output_dir}/{model_name}/{file_name}"
    vocals_path = f"{model_dir}/vocals.wav"
    background_path = f"{model_dir}/no_vocals.wav"

    return vocals_path, background_path
# vocals_path, background_path=demucs_separate_vocal_music(file_path)
import subprocess
from pathlib import Path

def slice_audio(input_file, start_sec, duration_sec,save_path):
    """
    Slice any audio (WAV or MP3) and save as MP3.

    Args:
        input_file: Path to input audio (WAV or MP3)
        start_sec: Start time in seconds
        duration_sec: Duration in seconds
        output_file: Path to save output MP3
    """
    output_file="./safe.mp3"
    ext = Path(input_file).suffix.lower()
    
    cmd = ["ffmpeg", "-y", "-i", input_file, "-ss", str(start_sec), "-t", str(duration_sec)]
    
    # If input is WAV or anything non-MP3 → encode to MP3
    if ext != ".mp3":
        cmd += ["-codec:a", "libmp3lame", "-qscale:a", "2"]
    cmd.append(output_file)
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ Created {output_file}")
        shutil.copy(output_file,save_path)
    except subprocess.CalledProcessError:
        print("❌ FFmpeg failed. Check your input file and parameters.")
        

def get_clean_vocal(speaker_voice):
  start=0
  cuts={}
  audio_files=[]
  for i in speaker_voice:
    voice_path=speaker_voice[i]["reference_audio"]
    audio_files.append(voice_path)
    duration=get_duration(path=voice_path)
    cuts[i]=(start,start+duration)
    start+=duration
    # print(duration)
  new_audio=combine_audios(audio_files)
  # vocal_path,instrumental_path=  seperate_audio(new_audio)
  vocal_path,instrumental_path=demucs_separate_vocal_music(new_audio)
  for i in cuts:
    output_file=speaker_voice[i]["reference_audio"]
    start=cuts[i][0]
    end=cuts[i][1]
    duration_sec=end-start
    slice_audio(vocal_path, start, duration_sec,output_file)
    


from librosa import get_duration, load
import soundfile as sf

def fix_duration(speaker_voice, max_duration=20.0):
    """
    Trim reference_audio in speaker_voice dict to max_duration seconds,
    overriding the original file.
    """
    for speaker_id, data in speaker_voice.items():
        ref_path = data.get('reference_audio')
        if not ref_path:
            continue

        # Check duration quickly without loading full audio
        dur = get_duration(path=ref_path)

        if dur > max_duration:
            # Load the full audio only if trimming is needed
            y, sr = load(ref_path, sr=None)
            num_samples = int(max_duration * sr)
            y_trimmed = y[:num_samples]

            # Overwrite the original file
            sf.write(ref_path, y_trimmed, sr)
            print(f"[INFO] Trimmed {ref_path} from {dur:.2f}s to {max_duration}s")
        else:
            print(f"[INFO] {ref_path} is already under {max_duration}s ({dur:.2f}s)")







def get_speakers(media_file,it_has_backgroud_music,json_data):
  speaker_voice=get_speaker_from_media(media_file,json_data)
  fix_duration(speaker_voice, max_duration=20.0)
  if it_has_backgroud_music:
    print("Start Removing Speaker's Background Music ... ")
    get_clean_vocal(speaker_voice)
    print("Speaker's Background Music Removal Complete")
    
  return speaker_voice
    
## how to use 
# from utils import get_speaker_from_media,get_dubbing_json
## how to use 
# from utils import get_speaker_from_media,get_dubbing_json
# import json
# media_file="/content/video.mp4"
# llm_result= "{   \"1\": {          \"text\": \"An\",          \"dubbing\": \"एक\",          \"start\": 0.0,            \"end\": 11.68,          \"speaker_id\": 0           } }" # @param {type: "string"}
# json_data=json.loads(llm_result)
# default_speaker_voice=get_speaker_from_media(media_file,json_data)
# dubbing_json=get_dubbing_json(json_data, silence_threshold=0.6, max_merged_duration=10.0)
# speaker_voice=default_speaker_voice

def get_media_duration(media_file=None):
    """
    Get the exact playback duration (in seconds) of any audio or video file,
    suitable for dubbing synchronization.

    Args:
        media_file (str): Path to the audio or video file.

    Returns:
        float: Exact duration in seconds. Returns 0.0 if file not found or error.
    """
    if media_file is None:
      media_file=""
    if not os.path.exists(media_file):
        print(f"File not found: {media_file}")
        return 0.0

    ext = Path(media_file).suffix.lower()

    # Audio formats to decode for exact duration
    audio_exts = [".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a", ".aiff", ".aif"]

    try:
        if ext in audio_exts:
            # Decode audio fully for exact duration
            audio = AudioSegment.from_file(media_file)
            return len(audio) / 1000.0  # milliseconds → seconds
        else:
            # For video, use ffprobe to get duration
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                media_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {media_file}: {e}")
        return 0.0





from pydub import AudioSegment
import os
import subprocess
import os


def replace_audio_in_video(video_path, audio_path, output_path, gpu=True):
    """
    Replace the audio track in a video with a new audio file.
    Returns the output path on success, or None if the command fails.
    """
    # Choose video codec
    codec = "h264_nvenc" if gpu else "libx264"

    command = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", codec,
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        "-y",  # overwrite output
        output_path
    ]

    try:
        # Run FFmpeg with output hidden
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_path
    except subprocess.CalledProcessError:
        # Return None if FFmpeg fails
        return None



def pad_audio_to_video(audio_path, video_duration_sec, output_path=None):
    """
    Pads the given audio with silence at the end to match video duration.
    
    audio_path: path to the audio file
    video_duration_sec: duration of video in seconds
    output_path: optional path to save padded audio
    """
    audio = AudioSegment.from_file(audio_path)
    audio_duration_sec = len(audio) / 1000  # convert ms to sec

    if audio_duration_sec >= video_duration_sec:
        # Audio is already equal or longer
        return audio_path

    # Calculate required silence duration
    silence_duration_ms = (video_duration_sec - audio_duration_sec) * 1000
    silence = AudioSegment.silent(duration=silence_duration_ms)

    # Append silence
    padded_audio = audio + silence

    # Determine output path
    if output_path is None:
        base, ext = os.path.splitext(audio_path)
        output_path = f"{base}_add_silence{ext}"

    # Export padded audio
    padded_audio.export(output_path, format=os.path.splitext(output_path)[1][1:])
    return output_path

def is_video_file(file_path):
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.mpeg']
    ext = os.path.splitext(file_path)[1].lower()
    return ext in video_extensions
from pathlib import Path


def make_video(media_file,dubbed_audio_path,language="en"):
  if is_video_file(media_file):
      os.makedirs("./replace_audio",exist_ok=True)
      video_duration = get_media_duration(media_file)  # in seconds
      audio_duration = get_media_duration(dubbed_audio_path)  # in seconds
      
      if audio_duration < video_duration:
          new_audio_path = pad_audio_to_video(dubbed_audio_path, video_duration)
          # print("Padded audio saved at:", new_audio_path)
      else:
        new_audio_path=dubbed_audio_path
      video_base, video_ext = os.path.splitext(os.path.basename(media_file))
      # Create new video filename with "_dubbing" suffix
      new_video_file = f"{video_base}_{language}_dubbing{video_ext}"
      new_video_file=f"./replace_audio/{new_video_file}"
      vid_save_path=replace_audio_in_video(media_file, new_audio_path, new_video_file, gpu=True)
      # print("Video with replaced audio saved at:", new_video_file)
      return vid_save_path

