# %cd /content/Video-Dubbing/
from utils import get_dubbing_json,get_speakers,get_media_duration,make_video
from tts import clone_voice_streaming,supported_languages
from STT.subtitle import subtitle_maker
import json
from librosa import get_duration
import os
import subprocess
from pathlib import Path
from pydub import AudioSegment
import uuid
import shutil
from audio_sync_pipeline import audio_sync
from tqdm.auto import tqdm





def redub_prompt(redub_json, language="target language", threshold=1.3):
    if language=="Hindi":
        language="Hindi Devanagari"
    prompt = f"""
You are a professional subtitle translator and dialogue editor for VIDEO DUBBING.

Your job is to IMPROVE dubbing accuracy by SHORTENING the dubbing text when needed,
without changing the meaning, tone, or emotion.

You will receive input in JSON format.
Each object represents ONE spoken sentence in a video.

IMPORTANT CONTEXT:
- "text" = original spoken sentence (source language)
- "dubbing" = current translated dubbing sentence (target language)
- "start" and "end" = original speaker timing (seconds)
- "tts_actual_duration_diff" =
  (TTS generated duration) MINUS (original speaker duration)

MEANING OF tts_actual_duration_diff:
- POSITIVE value (+) → TTS audio is LONGER than original timing ❌
- NEGATIVE value (−) → TTS audio is SHORTER than original timing ✅ (OK)
- We ONLY care about POSITIVE values

RULES:
1. If "tts_actual_duration_diff" is POSITIVE and GREATER THAN {threshold} seconds:
   - The dubbing text is TOO LONG
   - You MUST rewrite the "dubbing" text to be SHORTER
   - Keep the meaning, style, and natural spoken flow
   - Do NOT speed up speech
   - Do NOT change start/end times
   - Do NOT add explanations

2. If "tts_actual_duration_diff" is LESS THAN OR EQUAL TO {threshold} seconds
   OR NEGATIVE:
   - Keep the "dubbing" text unchanged

3. Your output MUST:
   - Be valid JSON ONLY
   - Match the input structure exactly
   - Include ONLY these fields:
     - text
     - dubbing
     - start
     - end
     - speaker_id
   - Do NOT include tts_actual_duration_diff in output

OUTPUT FORMAT (STRICT):

{{
  "sentence_number": {{
    "text": "original text",
    "dubbing": "shortened, natural, dubbing-friendly {language} translation",
    "start": start_time,
    "end": end_time,
    "speaker_id": speaker_id
  }}
}}

IMPORTANT:
- Do NOT explain your changes
- Do NOT add extra keys
- Do NOT change sentence order
- Output JSON ONLY
- Only process the sentence IDs provided.
- Do NOT assume missing sentence IDs exist.
- Do NOT create new sentences.

INPUT JSON:
{json.dumps(redub_json, ensure_ascii=False, indent=2)}
"""
    return prompt

def prepare_redub_data_and_get_prompt(json_path, language="target language", threshold=1.3):
  with open(json_path, "r", encoding="utf-8") as f:
      data = json.load(f)


  redub_json={}
  for i in data['segments']:
    temp_data=data['segments'][i]
    # print(temp_data)
    value = float(temp_data['tts_actual_duration_diff'])
    rounded = f"{value:+.2f}"
    if value>=threshold:
      redub_json[str(i)]={
        "text": temp_data['text'],
        "dubbing": temp_data['dubbing'],
        "start": temp_data['start'],
        "end": temp_data['end'],
        "tts_actual_duration_diff": rounded,
        "speaker_id": temp_data['speaker_id'],
      }
  # Call the 'redub_prompt' from cell oBOf2axfhh9Z which expects a dict.
  # This works because this function's new name avoids overwriting it.
  prompt=redub_prompt(redub_json, language=language, threshold=threshold)
  return prompt



def make_silence(duration_sec, path):
    """Generate silent audio of given duration (sec)"""
    AudioSegment.silent(duration=duration_sec * 1000).export(path, format="wav")

def srt_to_dub(
    media_file,
    dubbing_json,
    speaker_voice,
    language_name="English",
    exaggeration_input=0.5,
    temperature_input=0.8,
    cfgw_input=0.5,
    redub=False,
):


    
    #create folders
    temp_folder = "./dubbing_temp"
    if not redub:
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
    os.makedirs(temp_folder, exist_ok=True)
    
    dub_save_folder="./dubbing_result"
    os.makedirs(dub_save_folder, exist_ok=True)
    
    curr_dir=os.getcwd()
    json_path = os.path.join(curr_dir, "json_input.json")
    
    old_json={}
    if redub and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                old_json = json.load(f)
        except json.JSONDecodeError:
            old_json = {}
        
         
    #get media_duration for ending silence
    last_id = list(dubbing_json.keys())[-1]
    actual_media_duration = get_media_duration(media_file)
    target_segment_duration = dubbing_json[last_id]['end']
    media_duration = max(actual_media_duration, target_segment_duration)

    random_id = str(uuid.uuid4().hex )[:8]
    dub_file_name=dubbing_json['1']['text'][:25].replace(" ","_")
    dub_file_name+=f"_{language_name}_{random_id}.wav"
    dub_file_name=f"{dub_save_folder}/{dub_file_name}"
    json_result={"media_file":media_file,
                 "save_path":dub_file_name,
                 "speaker_voice":speaker_voice,
                 "segments":{}}
    dubbing_dict={ }

    # for i, segment_id in enumerate(dubbing_json, 1):
    
    for i, segment_id in enumerate(
        tqdm(dubbing_json.keys(),
             total=len(dubbing_json),
             desc="Generating dubbed segments"),1):
                 
        seg = dubbing_json[segment_id]
        text = seg['text']
        start = seg['start']
        end = seg['end']
        actual_duration = seg['duration']
        starting_silence = seg.get('starting_silence', 0)
        speaker_id = seg['speaker_id']
        raw_text = seg['raw_text']
        redub_tts=seg.get('redub', False)
        # print(f"spekaker id : {speaker_id}")
        # print(f"speaker voice: {speaker_voice}")
        spk_info = speaker_voice.get(speaker_id, {})
        # print(f"spk_info::: {spk_info}")
        reference_audio = spk_info.get("reference_audio", "")
        fixed_seed = spk_info.get("fixed_seed", 0)
        avg_speed = spk_info.get("avg_talk_speed", 1.0)
        seed_num_input=fixed_seed
        
        if segment_id == last_id:
            ending_silence = max(0, media_duration - end)
        else:
            next_id = str(int(segment_id) + 1)
            ending_silence = dubbing_json[next_id].get('starting_silence', 0)

        save_path = f"{temp_folder}/{segment_id}.wav"
        # print(f"text: {text}")
        # print(f"reference_audio Audio: {reference_audio}")
        # print(f"Language_name: {language_name}")
        # print(f"exaggeration_input: {exaggeration_input}")
        # print(f"temperature_input: {temperature_input}")
        # print(f"seed_num_input: {seed_num_input}")
        # print(f"cfgw_input: {cfgw_input}")
             
        if redub==True and redub_tts==True:
            try:
              raw_path = clone_voice_streaming(
                          text,
                          reference_audio,
                          language_name,
                          exaggeration_input,
                          temperature_input,
                          seed_num_input,
                          cfgw_input,
                          stereo=False,
                          remove_silence=False,
                      )
            except Exception as e:
              print(f"Audio Generation Failed")
              preview = (text[:25] + "...") if text and len(text) > 25 else (text or "[EMPTY TEXT]")
              print(preview)
              make_silence(actual_duration, raw_path)
        if redub==True and redub_tts==False:
            raw_path=old_json["segments"][segment_id]['tts_path']
        if redub==False:   
            try:
              raw_path = clone_voice_streaming(
                          text,
                          reference_audio,
                          language_name,
                          exaggeration_input,
                          temperature_input,
                          seed_num_input,
                          cfgw_input,
                          stereo=False,
                          remove_silence=False,
                      )
            except Exception as e:
              print(f"Audio Generation Failed")
              preview = (text[:25] + "...") if text and len(text) > 25 else (text or "[EMPTY TEXT]")
              print(preview)
              make_silence(actual_duration, raw_path)
        # print(raw_path)
        if os.path.exists(raw_path):
          shutil.copy(raw_path,save_path)
        else:
          make_silence(actual_duration, save_path)
        tts_duration=get_duration(path=save_path) if os.path.exists(save_path) else 0.0
        gap=tts_duration-actual_duration
        if gap>0:
            gap=f"+{gap}"
        else:
            gap=str(gap)
        dubbing_dict[segment_id] = {
            'text': raw_text,
            'dubbing':text,
            'start': start,
            'end': end,
            'speaker_id': speaker_id,
            'tts_actual_duration_diff': gap,
            'actual_duration': actual_duration,
            'speaker_speed': avg_speed,
            'starting_silence': starting_silence,
            'ending_silence': ending_silence,
            'tts_path':  os.path.abspath(save_path),
            'tts_duration': tts_duration ,
            'language': language_name,
            'exaggeration': exaggeration_input,
            'temperature': temperature_input,
            'seed_num': seed_num_input,
            'cfgw': cfgw_input,
            'reference_audio': reference_audio,
        }
    json_result["segments"]=dubbing_dict
    with open(json_path, "w", encoding="utf-8") as f:
      json.dump(json_result, f, ensure_ascii=False, indent=4)

    redubbing_prompt=prepare_redub_data_and_get_prompt(json_path, language=language_name, threshold=1.2)
    
    return json_result,json_path,redubbing_prompt




def make_json_for_redub(json_path,redub_json_string):
  with open(json_path, "r", encoding="utf-8") as f:
      data = json.load(f)
  redub_input=json.loads(redub_json_string)
  redub_json={}
  for i in data['segments']:
    
    temp_data=data['segments'][i]
    redub=False
    dubbing_text=temp_data['dubbing']
    if i in redub_input.keys():
      dubbing_text=redub_input[i]['dubbing']
      redub=True

    redub_json[i]={
      "raw_text": temp_data['text'],
      "text": dubbing_text,
      "start": temp_data['start'],
      "end": temp_data['end'],
      "speaker_id": temp_data['speaker_id'],
      "redub":redub,
      "duration": temp_data['actual_duration'],
      "starting_silence": temp_data['starting_silence'],
      
    }
  return redub_json





# --------------------------
# Step 6: Main dubbing function
# --------------------------

def dubbing(
    media_file,
    dubbing_json,
    speaker_voice,
    language_name="English",
    exaggeration_input=0.5,
    temperature_input=0.8,
    cfgw_input=0.5,
    want_subtile=False,
    redub=False
):    
    curr_dir=os.getcwd()
    json_path = os.path.join(curr_dir, "json_input.json")
    if redub and os.path.exists(json_path):
        dubbing_json=make_json_for_redub(json_path,dubbing_json)

    json_result,json_path,redubbing_prompt=srt_to_dub(
        media_file,
        dubbing_json,
        speaker_voice,
        language_name,
        exaggeration_input,
        temperature_input,
        cfgw_input,
        redub,

    )
    save_path=audio_sync(json_path)
    default_srt,custom_srt, word_srt, shorts_srt=None,None,None,None
    if want_subtile:
         default_srt, translated_srt_path, custom_srt, word_srt, shorts_srt, txt_path,sentence_json,word_json, transcript= subtitle_maker(save_path, language_name, language_name)
    return save_path ,save_path,default_srt,custom_srt, word_srt, shorts_srt,redubbing_prompt
