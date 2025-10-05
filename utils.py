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
      print("Success!")
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

## how to use 

# import json
# media_file="/content/video.mp4"
# llm_result= "{   \"1\": {          \"text\": \"An\",          \"dubbing\": \"एक\",          \"start\": 0.0,            \"end\": 11.68,          \"speaker_id\": 0           } }" # @param {type: "string"}
# json_data=json.loads(llm_result)
# default_speaker_voice=get_speaker_from_media(media_file,json_data)
# dubbing_json=get_dubbing_json(json_data, silence_threshold=0.6, max_merged_duration=10.0)
# speaker_voice=default_speaker_voice
