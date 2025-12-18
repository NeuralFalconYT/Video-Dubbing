#@title Whisper Transcription with speaker diarization

# %%writefile /content/Video-Dubbing/whisper_diarization.py
import sys
sys.path.append("./STT/")

# from pipeline import WhisperDiarizationPipeline
import torch
import gc
import re
import os
import json
import uuid
from deep_translator import GoogleTranslator
from llama_translate import hunyuan_mt_translate
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
# def speech_to_text(audio_path,language_name=None,number_of_speakers=None):
#   lang_code = LANGUAGE_CODE.get(language_name, None)
#   if number_of_speakers==0:
#     number_of_speakers=None
#   # Detect device and compute type automatically
#   if torch.cuda.is_available():
#     device = "cuda"        # Use GPU if available
#     compute_type = "float16"  # Use faster, lower-precision computation on GPU
#   elif torch.backends.mps.is_available():
#       device = "mps"         # Apple GPU (Metal)
#       compute_type = "float16"
#   else:
#       device = "cpu"         # Fallback to CPU
#       compute_type = "int8"  # Low-memory, quantized CPU computation

#   # Initialize Whisper + Diarization pipeline
#   pipeline = WhisperDiarizationPipeline(
#       device=device,  # hardware to run model on
#       compute_type=compute_type,  # model precision / speed
#       model_name="deepdml/faster-whisper-large-v3-turbo-ct2"  # model variant
#   )

#   # Run prediction on the audio file
#   result = pipeline.predict(
#       file_string=None,             # Optional: raw audio as base64 string (not used here)
#       file_url=None,                # Optional: URL of audio file to download (not used)
#       file_path=audio_path,  # Path to local audio file
#       num_speakers=number_of_speakers,  # Number of speakers; None = auto-detect
#       translate=False,              # True = convert audio to English; False = keep original language
#       language=lang_code,                # Force transcription in a specific language; None = auto-detect
#       prompt=None,                  # Optional text prompt for better transcription context
#       preprocess=0,                 # Audio preprocessing level (0 = none, 1-4 = increasing filtering/denoise)
#       highpass_freq=45,             # High-pass filter frequency (Hz) to remove low rumble
#       lowpass_freq=8000,            # Low-pass filter frequency (Hz) to remove high-frequency noise
#       prop_decrease=0.3,            # Noise reduction proportion (higher = more aggressive)
#       stationary=True,              # Assume background noise is stationary (True/False)
#       target_dBFS=-18.0             # Normalize audio loudness to this dBFS level
#   )
#   del pipeline
#   gc.collect()
#   if torch.cuda.is_available():
#     torch.cuda.empty_cache()
#   # print(result.to_dict())
#   return result.to_dict()

from whisper_pipeline import get_transcript
# media_file="/content/video.mp4"
# result=get_transcript(media_file,language_name=None,number_of_speakers=None,remove_music=True)


import copy
from collections import Counter

def fix_speaker(res, max_check=6, debug=True):
    res = copy.deepcopy(res)   # <<< makes a true independent copy

    segments = res["segments"]

    for i in range(len(segments)):
        old = segments[i]["speaker"]

        if old != "UNKNOWN":
            continue

        neighbors = []

        for j in range(max(0, i - max_check), i):
            s = segments[j]["speaker"]
            if s != "UNKNOWN":
                neighbors.append(s)

        for j in range(i + 1, min(len(segments), i + 1 + max_check)):
            s = segments[j]["speaker"]
            if s != "UNKNOWN":
                neighbors.append(s)

        if neighbors:
            new = Counter(neighbors).most_common(1)[0][0]
        else:
            new = None

        if new:
            segments[i]["speaker"] = new
            for w in segments[i].get("words", []):
                w["speaker"] = new

            if debug:
                print(f"UNKNOWN → {new}")
        else:
            if debug:
                print("UNKNOWN → (no decision yet)")

    for seg in segments:
        if seg["speaker"] == "UNKNOWN":
            seg["speaker"] = "SPEAKER_69"
            for w in seg.get("words", []):
                w["speaker"] = "SPEAKER_69"
            if debug:
                print("UNKNOWN → SPEAKER_69")

    return res

def speech_to_text(audio_path,language_name=None,number_of_speakers=None,remove_music=True,make_small_segments=True,model_name="deepdml/faster-whisper-large-v3-turbo-ct2"):
  result=get_transcript(audio_path,language_name,number_of_speakers,remove_music,make_small_segments)
  res=fix_speaker(result, max_check=6, debug=True)
  return res

def save_json(res):
    try:
        os.makedirs("transcript", exist_ok=True)
        if "segments" in res and len(res["segments"]) > 0:
            text = res["segments"][0]["text"][:25]
        else:
            text = "transcription"
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = text.lower().strip().replace(" ", "_")
        if len(text) <= 1:
            text = "transcription"
        unique_id = str(uuid.uuid4())[:6]
        filename = f"{text}_{unique_id}.json"
        filepath = os.path.join("./transcript", filename)
        with open(filepath, "w") as f:
            json.dump(res, f, indent=2)
        print(f"✅ Saved transcription to {filepath}")
    except Exception as e:
        print(f"❌ Error saving transcription: {e}")
        filepath = None
    return filepath

def translate_text(text, source_language, destination_language):
    """Translates a single block of text using GoogleTranslator."""
    source_code = LANGUAGE_CODE.get(source_language, None)
    target_code = LANGUAGE_CODE[destination_language]
    if destination_language == "Chinese":
        target_code = 'zh-CN'
    try:
      if source_code is None:
        translator = GoogleTranslator(target=target_code)
      else:
        translator = GoogleTranslator(source=source_code, target=target_code)
      return str(translator.translate(text.strip()))
    except Exception as e:
      print(f"Translation failed: {e}")
      return ""

def process_media(media_file,num_speakers,remove_music, make_small_segments,input_lang, output_lang,method,task):
  json_transcription,readable_json,prompt=None,None,None
  timestamp={}
  try:
    res = speech_to_text(media_file,language_name=input_lang,number_of_speakers=num_speakers,remove_music=remove_music,make_small_segments=make_small_segments)
    json_transcription=save_json(res)
    sentence_number=1
    for i in res["segments"]:
      text=i["text"]
      start=i["start"]
      end=i["end"]
      speaker=i["speaker"]
      speaker_id=int(speaker.split("SPEAKER_")[-1])
      if input_lang==output_lang:
        trans_text=""
      else:
        if method=="Using Google Translator" and task=="Translation":
          trans_text=translate_text(text, input_lang,output_lang)
        else:
          trans_text=""
      data={
          "text":text,
          "dubbing":trans_text,
          "start":start,
          "end":end,
          "speaker_id":speaker_id
      }
      timestamp[sentence_number]=data
      sentence_number+=1
      
      # if input_lang!=output_lang:
      
  except Exception as e:
    print(f"Error processing media: {e}")
  media_file = os.path.abspath(media_file)
  readable_json = json.dumps(timestamp, indent=2, ensure_ascii=False)
  if method=="Google AI Studio":
      prompt=prompt_maker(readable_json,output_lang,task)  
  if method=="Hunyuan-MT-7B Translator":
      timestamp=hunyuan_mt_translate(timestamp, input_lang, output_lang,task)
      readable_json = json.dumps(timestamp, indent=2, ensure_ascii=False)

          
  readable_json = json.dumps(timestamp, indent=2, ensure_ascii=False)
  return media_file,json_transcription,readable_json,prompt





def prompt_translation(language):
    """
    Generates a dubbing-friendly translation prompt for an .srt subtitle file.
    Tailored for natural speech and timing accuracy.
    """
    prompt = f"""
-------------- You are a professional subtitle translator for **video dubbing**.
Translate the following `.srt` subtitle file into **{language}** while preserving timing, meaning, and emotional tone.

Output in JSON format exactly like this:

```json
{{
  "sentence_number": {{
    "text": "original text",
    "dubbing": "natural, dubbing-friendly {language} translation",
    "start": speak start time,
    "end": speak end time,
    "speaker_id": speaker id
  }}
}}
```

**Guidelines for Translation:**

1. **Understand the full context** before translating — read the entire subtitle file first.
2. Translate into **natural, conversational {language}**, not a direct word-for-word translation.
6. Keep translations **roughly similar in length** to the original so lip movements sync naturally.
"""
    return prompt


def prompt_fix_grammar(language="English"):
    """
    Generates a dubbing-friendly grammar correction prompt for an .srt subtitle file.
    Tailored for natural speech and timing accuracy.
    """
    prompt = f"""
-------------- You are a professional subtitle editor for **video dubbing**.
Fix the grammar, spelling, and awkward phrasing in the following `.srt` subtitle file while preserving timing, meaning, and emotional tone.
Do NOT translate — keep everything in {language}.

Output in JSON format exactly like this:
```json
{{
  "sentence_number": {{
    "text": "original text",
    "dubbing": "natural, dubbing-friendly corrected {language} line",
    "start": speak start time,
    "end": speak end time,
    "speaker_id": speaker id
  }}
}}
```


**Guidelines for Grammar Fixing:**

1.  **Understand the full context** before editing — read the entire subtitle file first.
2.  Correct grammar, spelling, and phrasing errors while keeping the same meaning.
4.  Keep corrections **roughly similar in length** to the original so lip movements sync naturally.
"""
    return prompt



def prompt_rewrite_subtitles(language="English"):
    """
    Generates a professional prompt for rewriting subtitles (.srt) 
    to make them natural and dubbing-friendly, while maintaining timing, meaning, and emotion.
    """
    prompt = f"""
-------------- You are a professional **subtitle rewriter** specializing in **video dubbing**.
Your task is to rewrite the given `.srt` subtitle file to make it sound more natural, expressive, and dubbing-friendly — 
while preserving timing, context, emotional tone, and meaning.



Output in JSON format exactly like this:
```json
{{
  "sentence_number": {{
    "text": "original subtitle text",
    "dubbing": 'Rewrite the "text" in {language}' smooth, dubbing-optimized version,
    "start": start_time,
    "end": end_time,
    "speaker_id": speaker_id
  }}
}}
````

**Guidelines for Subtitle Rewriting:**

1. **Read the entire subtitle file** first to understand the full context and speaker dynamics.
2. Rewrite each line to sound natural in spoken {language} — as if performed by a voice actor.
3. Maintain the same meaning and tone, but adjust phrasing for smoother dubbing flow.
4. Keep the rewritten text **similar in length and pacing** to the original to ensure lip-sync compatibility.
5. Avoid robotic or overly formal language — make it conversational and emotionally authentic.
   """
    return prompt



def prompt_translate_and_rewrite(language):
    """
    Generates a dubbing-friendly prompt for translating AND rewriting an .srt subtitle file.
    The model should both translate and naturally rewrite each line for smooth, expressive dubbing.
    """
    prompt = f"""
-------------- You are a professional **subtitle translator and dialogue rewriter** for **video dubbing**.
Your job is to translate the given `.srt` subtitle file into **{language}**, 
and then rewrite each translated line so it sounds **natural, expressive, and dubbing-friendly** — 
while preserving timing, emotional tone, and the original meaning.

🧠 **Important clarification of "Rewrite":**
"Rewrite" means: keep the same meaning, tone, and intent as the original line,
but express it in more natural and conversational {language} — not word-for-word translation.
Make it sound like real spoken dialogue a voice actor would perform.

Output must be in JSON format exactly like this:
```json
{{
  "sentence_number": {{
    "text": "original subtitle text",
    "dubbing": "smooth, natural {language} version — rewritten for dubbing",
    "start": start_time,
    "end": end_time,
    "speaker_id": speaker_id
  }}
}}


**Guidelines for Translation + Rewriting:**

1. **Read the entire subtitle file** first to understand full context and tone.
2. Translate into **fluent, conversational {language}**, not literal or robotic text.
3. **Rewrite each translated line** to keep it natural, emotional, and dubbing-friendly.
4. Preserve the original **meaning, emotion, and pacing**.
5. Keep each rewritten line **close in length** to the original for better lip-sync.
6. Avoid overly formal or unnatural phrasing — it should sound like real speech.
   """
    return prompt


                                          
def prompt_maker(transcription,target_language, task="Translation"):
    txt_path="./temp.txt"
    if target_language=="Hindi":
        target_language="Hindi Devanagari"
     
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(transcription)
        if task == "Translation":
            f.write(prompt_translation(target_language))
        if task=="Fix Grammar":
            f.write(prompt_fix_grammar(target_language))
        if task=="Rewrite":
            f.write(prompt_rewrite_subtitles(target_language))
        if task=="Translate & Rewrite":
            f.write(prompt_translate_and_rewrite(target_language))
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


## How to use 
# from whisper_diarization import process_media
# media_file="/content/test.MP3"
# num_speakers=0
# remove_music=True
# input_lang="English"
# output_lang="English"
# method="Google AI Studio"
# task="English"
# make_small_segments=True
# media_file,json_transcription,readable_json,prompt=process_media(media_file,num_speakers, remove_music, make_small_segments, input_lang, output_lang,method,task)
# print(prompt)
