# %cd /content/Video-Dubbing/STT
import os
from pydub import AudioSegment
import subprocess
from hf_downloader import download_model
from pyannote.audio import Pipeline as PyannotePipeline
from faster_whisper import WhisperModel
import torch
import gc
import pandas as pd
import numpy as np
import re 
import torchaudio
from small_segment import segment_split

def convert_to_mono(media_file):
    # Extract folder, base name, and extension
    folder, filename = os.path.split(media_file)
    name, ext = os.path.splitext(filename)

    # Handle extension properly
    ext = ext.lower()
    if ext not in [".mp3", ".wav", ".mp4"]:
        return media_file  # unsupported file type → return original

    # Build output path with same folder, but "_mono" before extension
    temp_file = os.path.join(folder, f"{name}_mono{'.mp3' if ext == '.mp4' else ext}")

    # Case 1: If it's a video (.mp4), extract audio and convert to mono -> mp3
    if ext == ".mp4":
        print("Detected MP4 video. Extracting audio and converting to mono...")
        try:
            cmd = [
                "ffmpeg",
                "-i", media_file,
                "-ac", "1",       # force mono
                "-y",             # overwrite if exists
                temp_file
            ]
            subprocess.run(
                              cmd,
                              check=True,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL
                          )
        except subprocess.CalledProcessError:
            print("FFmpeg failed, returning original video file.")
            return media_file  # return original video file if ffmpeg fails

    # Case 2: If it's an audio file (.mp3 or .wav)
    else:
        try:
            audio = AudioSegment.from_file(media_file)
            if audio.channels > 1:
                print(f"Audio has {audio.channels} channels. Converting to mono...")
                audio = audio.set_channels(1)
                audio.export(temp_file, format=ext[1:])  # keep original format
            else:
                print("Audio is already mono. Copying to temp file...")
                audio.export(temp_file, format=ext[1:])
        except Exception as e:
            print(f"Error processing audio: {e}")
            return media_file  # fallback → return original file

    return temp_file




# Mapping of language names to their ISO 639-1 codes
LANGUAGE_CODE = {
    'Akan': 'aka', 'Albanian': 'sq', 'Amharic': 'am', 'Arabic': 'ar', 'Armenian': 'hy',
    'Assamese': 'as', 'Azerbaijani': 'az', 'Basque': 'eu', 'Bashkir': 'ba', 'Bengali': 'bn',
    'Bosnian': 'bs', 'Bulgarian': 'bg', 'Burmese': 'my', 'Catalan': 'ca', 'Chinese': 'zh',
    'Croatian': 'hr', 'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl', 'English': 'en',
    'Estonian': 'et', 'Faroese': 'fo', 'Finnish': 'fi', 'French': 'fr', 'Galician': 'gl',
    'Georgian': 'ka', 'German': 'de', 'Greek': 'el', 'Gujarati': 'gu', 'Haitian Creole': 'ht',
    'Hausa': 'ha', 'Hebrew': 'he', 'Hindi': 'hi', 'Hungarian': 'hu', 'Icelandic': 'is',
    'Indonesian': 'id', 'Italian': 'it', 'Japanese': 'ja', 'Kannada': 'kn', 'Kazakh': 'kk',
    'Korean': 'ko', 'Kurdish': 'ckb', 'Kyrgyz': 'ky', 'Lao': 'lo', 'Lithuanian': 'lt',
    'Luxembourgish': 'lb', 'Macedonian': 'mk', 'Malay': 'ms', 'Malayalam': 'ml', 'Maltese': 'mt',
    'Maori': 'mi', 'Marathi': 'mr', 'Mongolian': 'mn', 'Nepali': 'ne', 'Norwegian': 'no',
    'Norwegian Nynorsk': 'nn', 'Pashto': 'ps', 'Persian': 'fa', 'Polish': 'pl', 'Portuguese': 'pt',
    'Punjabi': 'pa', 'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr', 'Sinhala': 'si',
    'Slovak': 'sk', 'Slovenian': 'sl', 'Somali': 'so', 'Spanish': 'es', 'Sundanese': 'su',
    'Swahili': 'sw', 'Swedish': 'sv', 'Tamil': 'ta', 'Telugu': 'te', 'Thai': 'th',
    'Turkish': 'tr', 'Ukrainian': 'uk', 'Urdu': 'ur', 'Uzbek': 'uz', 'Vietnamese': 'vi',
    'Welsh': 'cy', 'Yiddish': 'yi', 'Yoruba': 'yo', 'Zulu': 'zu'
}

def get_language_name(code):
    """Retrieves the full language name from its code."""
    for name, value in LANGUAGE_CODE.items():
        if value == code:
            return name
    return None

def load_model(model_name="deepdml/faster-whisper-large-v3-turbo-ct2"):
  whisper_model, diarization_model=None,None
  device = "cuda" if torch.cuda.is_available() else "cpu"
  compute_type = "float16" if torch.cuda.is_available() else "int8"
  if model_name=="deepdml/faster-whisper-large-v3-turbo-ct2":
    model_dir = download_model(
                "deepdml/faster-whisper-large-v3-turbo-ct2",
                download_folder="./",
                redownload=False)
    whisper_model = WhisperModel(
                model_dir,
                device=device,
                compute_type=compute_type)
  else:
    whisper_model = WhisperModel(
                  model_name,
                  device=device,
                  compute_type=compute_type,
              )
  token = os.getenv("HF_AUTH_TOKEN", "TOKEN_HERE")
  try:
    diarization_model = PyannotePipeline.from_pretrained(
              "pyannote/speaker-diarization-3.1",
              use_auth_token=token,
          ).to(torch.device(device))
  except:
    # skip google colab hugging face authentication problem
    print("Google Colab Wants Huggingface Token 🤬")
    diarization_model = PyannotePipeline.from_pretrained(
              "fatymatariq/speaker-diarization-3.1"
          ).to(torch.device(device))
  return whisper_model, diarization_model


def transcribe_audio(whisper_model,mono_audio, language="English"):
  lang_code = LANGUAGE_CODE.get(language, None)
  segments,whisper_info  = whisper_model.transcribe(mono_audio, word_timestamps=True, language=lang_code)
  # predicted_lang=get_language_name(whisper_info.language)
  predicted_lang=whisper_info.language
  segments = list(segments)
  segments = [
            {
                "avg_logprob": s.avg_logprob,
                "start": float(s.start),
                "end": float(s.end),
                "text": s.text,
                "words": [
                    {
                        "start": float(w.start),
                        "end": float(w.end),
                        "word": w.word,
                        "probability": w.probability,
                    }
                    for w in s.words
                ],
            }
            for s in segments
        ]
  return segments,predicted_lang
def speaker_diarization(diarization_model,mono_audio,num_speakers=None):
  waveform, sample_rate = torchaudio.load(mono_audio)
  diarization = diarization_model(
              {"waveform": waveform, "sample_rate": sample_rate},
              num_speakers=num_speakers,
          )
  diarize_segments = []
  diarization_list = list(diarization.itertracks(yield_label=True))
  for turn, _, speaker in diarization_list:
      diarize_segments.append(
          {"start": turn.start, "end": turn.end, "speaker": speaker}
      )

  unique_speakers = {speaker for _, _, speaker in diarization_list}
  detected_num_speakers = len(unique_speakers)
  return diarize_segments, detected_num_speakers

def _assign_speaker_to_segment_or_word(segment_or_word, diarize_df, fallback_speaker=None):
    """Calculates the intersection of times."""
    diarize_df["intersection"] = np.minimum(
        diarize_df["end"], segment_or_word["end"]
    ) - np.maximum(diarize_df["start"], segment_or_word["start"])
    dia_tmp = diarize_df[diarize_df["intersection"] > 0]

    if len(dia_tmp) > 0:
        speaker = dia_tmp.groupby("speaker")["intersection"].sum().sort_values(ascending=False).index[0]
    else:
        speaker = fallback_speaker or "UNKNOWN"
    return speaker

def _group_segments(segments):
    if not segments:
        return []

    grouped_segments = []
    current_group = segments[0].copy()
    sentence_end_pattern = r"[.!?]+"

    for segment in segments[1:]:
        time_gap = segment["start"] - current_group["end"]
        current_duration = current_group["end"] - current_group["start"]
        can_combine = (
            segment["speaker"] == current_group["speaker"]
            and time_gap <= 1.0
            and current_duration < 30.0
            and not re.search(sentence_end_pattern, current_group["text"][-1:])
        )
        if can_combine:
            current_group["end"] = segment["end"]
            current_group["text"] += " " + segment["text"]
            # <<< FIX IS HERE >>>
            current_group["words"].extend(segment["words"])
        else:
            grouped_segments.append(current_group)
            current_group = segment.copy()

    grouped_segments.append(current_group)
    return grouped_segments


def _merge_segments_with_diarization(segments, diarize_segments):
    diarize_df = pd.DataFrame(diarize_segments)
    final_segments = []

    for segment in segments:
        # Segment speaker
        speaker = _assign_speaker_to_segment_or_word(segment, diarize_df)

        # Word-level speakers
        words_with_speakers = []
        for word in segment["words"]:
            word_speaker = _assign_speaker_to_segment_or_word(word, diarize_df, fallback_speaker=speaker)
            word["speaker"] = word_speaker
            words_with_speakers.append(word)

        new_segment = {
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"],
            "speaker": speaker,
            "avg_logprob": segment["avg_logprob"],
            "words": words_with_speakers,
        }
        final_segments.append(new_segment)

    final_segments = _group_segments(final_segments)
    for segment in final_segments:
        segment["text"] = re.sub(r"\s+", " ", segment["text"]).strip()
        segment["text"] = re.sub(r"\s+([.,!?])", r"\1", segment["text"])
        segment["duration"] = segment["end"] - segment["start"]

    return final_segments


import os
import shutil
import subprocess
from pathlib import Path

def demucs_separate_vocal_music(file_path, model_name="htdemucs_ft", output_dir="separated_output"):
    # model_name="htdemucs"
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

    print("🎧 Running Demucs for vocal and music split ...")
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
def vocal_music_split(media_file,mono_audio):
  separate_folder="./split_media"
  os.makedirs(separate_folder, exist_ok=True)
  name_only = os.path.splitext(os.path.basename(media_file))[0]
  vocal_path=f"{separate_folder}/{name_only}_vocal.wav"
  music_path=f"{separate_folder}/{name_only}_music.wav"
  demucs_vocal,demucs_music=demucs_separate_vocal_music(mono_audio)
  shutil.copy(demucs_vocal,vocal_path)
  if demucs_music is not None:
    shutil.copy(demucs_music,music_path)
  else:
    music_path =None
  return vocal_path,music_path  



def whisper_pyannote(mono_audio,language_name,number_of_speakers=None,make_small_segments=True,model_name="deepdml/faster-whisper-large-v3-turbo-ct2"):
  whisper_model, diarization_model=load_model(model_name="deepdml/faster-whisper-large-v3-turbo-ct2")
  segments,predicted_lang=transcribe_audio(whisper_model,mono_audio, language=language_name)
  diarize_segments, detected_num_speakers=speaker_diarization(diarization_model,mono_audio,num_speakers=number_of_speakers)
  final_segments=_merge_segments_with_diarization(segments, diarize_segments)
  if make_small_segments:
      lang_code=predicted_lang
      segments = segment_split(
                            final_segments,
                            language=lang_code,
                            max_chars=80,
                            minimum_gap=0.05,
                            allow_same_start_end_merge=True,  
                            max_chars_merge=90,               
                        )
      final_segments=segments
      
  result={'segments':final_segments, 'language':predicted_lang, 'num_speakers':detected_num_speakers}
  del whisper_model
  del diarization_model
  gc.collect()
  if torch.cuda.is_available():
      torch.cuda.empty_cache()
  return result

def get_transcript(media_file,language_name=None,number_of_speakers=None,remove_music=True,make_small_segments=True,model_name="deepdml/faster-whisper-large-v3-turbo-ct2"):
  mono_audio=convert_to_mono(media_file)
  vocal_path,music_path=vocal_music_split(media_file,mono_audio)
  if remove_music:
    result=whisper_pyannote(vocal_path,language_name,number_of_speakers,make_small_segments,model_name)
  else:
    result=whisper_pyannote(mono_audio,language_name,number_of_speakers,make_small_segments,model_name)
  return result

# from whisper_pipeline import get_transcript
# media_file="/content/video.mp4"
# result=get_transcript(media_file,language_name=None,number_of_speakers=None,remove_music=True)
