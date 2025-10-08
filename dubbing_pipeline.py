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
):



    #create folders
    temp_folder = "./dubbing_temp"
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    os.makedirs(temp_folder, exist_ok=True)
    dub_save_folder="./dubbing_result"
    os.makedirs(dub_save_folder, exist_ok=True)
    curr_dir=os.getcwd()
    json_path = os.path.join(curr_dir, "json_input.json")

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

    for i, segment_id in enumerate(dubbing_json, 1):
        seg = dubbing_json[segment_id]
        text = seg['text']
        start = seg['start']
        end = seg['end']
        actual_duration = seg['duration']
        starting_silence = seg.get('starting_silence', 0)
        speaker_id = seg['speaker_id']
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
        # print(raw_path)
        if os.path.exists(raw_path):
          shutil.copy(raw_path,save_path)
        else:
          make_silence(actual_duration, save_path)


        dubbing_dict[segment_id] = {
            'text': text,
            'start': start,
            'end': end,
            'actual_duration': actual_duration,
            'speaker_speed': avg_speed,
            'starting_silence': starting_silence,
            'ending_silence': ending_silence,
            'tts_path':  os.path.abspath(save_path),
            'tts_duration': get_duration(filename=save_path) if os.path.exists(save_path) else 0.0,
            'speaker_id': speaker_id,
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
    return json_result,json_path


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
):
    json_result,json_path=srt_to_dub(
        media_file,
        dubbing_json,
        speaker_voice,
        language_name,
        exaggeration_input,
        temperature_input,
        cfgw_input,

    )
    save_path=audio_sync(json_path)
    default_srt,custom_srt, word_srt, shorts_srt=None,None,None,None
    if want_subtile:
         default_srt, translated_srt_path, custom_srt, word_srt, shorts_srt, txt_path,sentence_json,word_json, transcript= subtitle_maker(media_file, language_name, language_name)
    return save_path ,save_path,default_srt,custom_srt, word_srt, shorts_srt
