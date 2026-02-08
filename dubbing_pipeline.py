#@title /content/Video-Dubbing/dubbing_pipeline.py
# %%writefile /content/Video-Dubbing/dubbing_pipeline.py
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
# from tts_hub import run_kokoro_tts



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




import os
import json
import time
import uuid
import re

import soundfile as sf
from pydub import AudioSegment
import torch,gc
from turbo_tts import generate, unload_turbo_model
from tts import clone_voice_streaming, unload_multilingual_model
from kokoro import KPipeline
from rich import print
import shutil
from edge_tts_code import edge_tts_generate


# =========================
# GLOBAL PIPELINES
# =========================
kokoro_pipeline = None


# =========================
# UTILITIES
# =========================
def clear_screen():
    try:
        from IPython.display import clear_output
        clear_output(wait=True)
    except:
        import sys
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def make_silence(duration_sec, path):
    """Generate silent wav audio"""
    AudioSegment.silent(duration=duration_sec * 1000).export(path, format="wav")


def temp_tts_file_name(text, language="en"):
    """Create safe temp wav filename"""
    save_folder = "./kokoro_tts"
    os.makedirs(save_folder, exist_ok=True)

    text = re.sub(r"[^a-zA-Z\s]", "", text).lower().strip().replace(" ", "_")
    if not text:
        text = "audio"

    truncated = text[:20]
    random_str = uuid.uuid4().hex[:8].upper()

    return f"{save_folder}/{truncated}_{language}_{random_str}.wav"


# =========================
# TURBO TTS
# =========================
def call_turbo_tts(text, audio_prompt_path, seed_num):
    audio_path, _ = generate(
        text=text,
        audio_prompt_path=audio_prompt_path,
        temperature=0.8,
        seed=seed_num,
        min_p=0.0,
        top_p=0.95,
        top_k=1000,
        repetition_penalty=1.2,
        norm_loudness=True,
        remove_silence=False,
        output_format="wav",
        minimum_silence=0.05,
        mp3_bitrate="192k",
    )
    return audio_path


# =========================
# KOKORO TTS
# =========================
def run_kokoro_tts(text, language="English", voice="af_heart", speed=1.0):
    global kokoro_pipeline

    language_map = {
        "English": "a",
        "American English": "a",
        "British English": "b",
        "Hindi": "h",
        "Spanish": "e",
        "French": "f",
        "Italian": "i",
        "Brazilian Portuguese": "p",
        "Japanese": "j",
        "Mandarin Chinese": "z",
    }

    lang_code = language_map.get(language, "a")
    if language=="English":
      voice="af_heart"
    if language=="Hindi":
      voice="hf_alpha"

    if kokoro_pipeline is None:
        kokoro_pipeline = KPipeline(lang_code=lang_code)

    file_name = temp_tts_file_name(text, lang_code)

    generator = kokoro_pipeline(text, voice=voice, speed=speed)
    for _, _, audio in generator:
        sf.write(file_name, audio, 24000)

    return file_name



def run_tts(text, reference_audio, language_name, seed_num, voice_model):
    """
    Central TTS router (safe version).
    Returns None if generation fails.
    """

    try:
        if voice_model == "Chatterbox Multilingual":
            return clone_voice_streaming(
                text,
                reference_audio,
                lang_name=language_name,
                exaggeration_input=0.5,
                temperature_input=0.8,
                seed_num_input=seed_num,
                cfgw_input=0.5,
                stereo=False,
                remove_silence=False,
                remove_noise=True,
            )

        elif voice_model == "Chatterbox Turbo":
            return call_turbo_tts(text, reference_audio, seed_num)

        elif voice_model == "Kokoro":
            return run_kokoro_tts(text, language=language_name)
        elif voice_model == "Edge TTS":
            return edge_tts_generate(
                  text=text,
                  language=language_name,
                  gender="Female",
                  speed=1.0,
              )

        # Future models here
        # elif voice_model == "NewTTS":
        #     return run_new_tts(...)

    except Exception as e:
        print(f"⚠️ TTS failed ({voice_model}): {e}")

    return None






def srt_to_dub(
    media_file,
    dubbing_json,
    speaker_voice,
    language_name="English",
    # exaggeration_input=0.5,
    # temperature_input=0.8,
    # cfgw_input=0.5,
    redub=False,
    voice_model="Chatterbox Multilingual"
):
    global kokoro_pipeline
    if voice_model=="Chatterbox Multilingual":
      unload_turbo_model()
    else:
      unload_multilingual_model()

    if voice_model=="Chatterbox Turbo" and language_name!="English":
      voice_model="Chatterbox Multilingual"




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

    # for i, segment_id in enumerate(
    #     tqdm(dubbing_json.keys(),
    #          total=len(dubbing_json),
    #          desc="Generating dubbed segments"),1):
    total_segments = len(dubbing_json)
    for idx, segment_id in enumerate(dubbing_json.keys(), start=1):
        clear_screen()

        print(
            f"[bold white]Generating TTS[/] "
            f"[green]{idx}[/]/[cyan]{total_segments}[/]"
        )

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

        if voice_model == "Chatterbox Multilingual":
            unload_turbo_model()

        elif voice_model == "Chatterbox Turbo":
            unload_multilingual_model()

        elif voice_model == "Kokoro":
            if kokoro_pipeline is not None:
                del kokoro_pipeline
                kokoro_pipeline = None

            gc.collect()
            if torch:
                torch.cuda.empty_cache()


        raw_path = None

        if redub and redub_tts:
            raw_path = run_tts(text, reference_audio, language_name, seed_num_input, voice_model)
        
        elif redub and not redub_tts:
            raw_path = old_json["segments"][segment_id]['tts_path']
        
        else:
            raw_path = run_tts(text, reference_audio, language_name, seed_num_input, voice_model)
        
        if raw_path is None:
            make_silence(actual_duration, save_path)
        
        elif os.path.exists(raw_path):
            raw_abs = os.path.abspath(raw_path)
            save_abs = os.path.abspath(save_path)
        
            if raw_abs != save_abs:
                shutil.copy(raw_abs, save_abs)


   
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
            # 'exaggeration': exaggeration_input,
            # 'temperature': temperature_input,
            'seed_num': seed_num_input,
            # 'cfgw': cfgw_input,
            'reference_audio': reference_audio,
        }
    json_result["segments"]=dubbing_dict
    with open(json_path, "w", encoding="utf-8") as f:
      json.dump(json_result, f, ensure_ascii=False, indent=4)

    redubbing_prompt=prepare_redub_data_and_get_prompt(json_path, language=language_name, threshold=0.9)
    # =========================
    # Post-clean models
    # =========================
    if voice_model == "Chatterbox Multilingual":
        unload_multilingual_model()

    elif voice_model == "Chatterbox Turbo":
        unload_turbo_model()

    elif voice_model == "Kokoro":
        if kokoro_pipeline is not None:
            del kokoro_pipeline
            kokoro_pipeline = None

        gc.collect()
        if torch:
            torch.cuda.empty_cache()

    return json_result,json_path,redubbing_prompt




# def make_json_for_redub(json_path,redub_json_string):
#   with open(json_path, "r", encoding="utf-8") as f:
#       data = json.load(f)
#   redub_input=json.loads(redub_json_string)
#   redub_json={}
#   for i in data['segments']:

#     temp_data=data['segments'][i]
#     redub=False
#     dubbing_text=temp_data['dubbing']
#     if i in redub_input.keys():
#       dubbing_text=redub_input[i]['dubbing']
#       redub=True

#     redub_json[i]={
#       "raw_text": temp_data['text'],
#       "text": dubbing_text,
#       "start": temp_data['start'],
#       "end": temp_data['end'],
#       "speaker_id": temp_data['speaker_id'],
#       "redub":redub,
#       "duration": temp_data['actual_duration'],
#       "starting_silence": temp_data['starting_silence'],

#     }
#   return redub_json





# --------------------------
# Step 6: Main dubbing function
# --------------------------

def dubbing(
    media_file,
    dubbing_json,
    speaker_voice,
    language_name="English",
    # exaggeration_input=0.5,
    # temperature_input=0.8,
    # cfgw_input=0.5,
    want_subtile=False,
    redub=False,
    voice_model="Chatterbox Multilingual"
):
    # curr_dir=os.getcwd()
    # json_path = os.path.join(curr_dir, "json_input.json")
    # if redub and os.path.exists(json_path):
    #     dubbing_json=make_json_for_redub(json_path,dubbing_json)
    print(dubbing_json)
    json_result,json_path,redubbing_prompt=srt_to_dub(
        media_file,
        dubbing_json,
        speaker_voice,
        language_name,
        # exaggeration_input,
        # temperature_input,
        # cfgw_input,
        redub,
        voice_model

    )
    save_path=audio_sync(json_path)
    default_srt,custom_srt, word_srt, shorts_srt=None,None,None,None
    if want_subtile:
         default_srt, translated_srt_path, custom_srt, word_srt, shorts_srt, txt_path,sentence_json,word_json, transcript= subtitle_maker(save_path, language_name, language_name)
    return save_path ,save_path,default_srt,custom_srt, word_srt, shorts_srt,redubbing_prompt
