#@title Whisper Transcription with speaker diarization

# %%writefile /content/Video-Dubbing/whisper_diarization.py
import sys
sys.path.append("./STT/")

from pipeline import WhisperDiarizationPipeline
import torch
import gc
import re
import os
import json
import uuid
from deep_translator import GoogleTranslator

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
def speech_to_text(audio_path,language_name=None,number_of_speakers=None):
  lang_code = LANGUAGE_CODE.get(language_name, None)
  if number_of_speakers==0:
    number_of_speakers=None
  # Detect device and compute type automatically
  if torch.cuda.is_available():
    device = "cuda"        # Use GPU if available
    compute_type = "float16"  # Use faster, lower-precision computation on GPU
  elif torch.backends.mps.is_available():
      device = "mps"         # Apple GPU (Metal)
      compute_type = "float16"
  else:
      device = "cpu"         # Fallback to CPU
      compute_type = "int8"  # Low-memory, quantized CPU computation

  # Initialize Whisper + Diarization pipeline
  pipeline = WhisperDiarizationPipeline(
      device=device,  # hardware to run model on
      compute_type=compute_type,  # model precision / speed
      model_name="deepdml/faster-whisper-large-v3-turbo-ct2"  # model variant
  )

  # Run prediction on the audio file
  result = pipeline.predict(
      file_string=None,             # Optional: raw audio as base64 string (not used here)
      file_url=None,                # Optional: URL of audio file to download (not used)
      file_path=audio_path,  # Path to local audio file
      num_speakers=number_of_speakers,  # Number of speakers; None = auto-detect
      translate=False,              # True = convert audio to English; False = keep original language
      language=lang_code,                # Force transcription in a specific language; None = auto-detect
      prompt=None,                  # Optional text prompt for better transcription context
      preprocess=0,                 # Audio preprocessing level (0 = none, 1-4 = increasing filtering/denoise)
      highpass_freq=45,             # High-pass filter frequency (Hz) to remove low rumble
      lowpass_freq=8000,            # Low-pass filter frequency (Hz) to remove high-frequency noise
      prop_decrease=0.3,            # Noise reduction proportion (higher = more aggressive)
      stationary=True,              # Assume background noise is stationary (True/False)
      target_dBFS=-18.0             # Normalize audio loudness to this dBFS level
  )
  del pipeline
  gc.collect()
  if torch.cuda.is_available():
    torch.cuda.empty_cache()
  # print(result.to_dict())
  return result.to_dict()



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

def process_media(media_file,num_speakers, input_lang, output_lang,method,task):
  json_transcription,readable_json,prompt=None,None,None
  try:
    res = speech_to_text(media_file,language_name="English",number_of_speakers=num_speakers)
    json_transcription=save_json(res)
    timestamp={}
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
        if method=="Using Google Translator":
          trans_text=translate_text(text, input_lang,output_lang),
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
      readable_json = json.dumps(timestamp, indent=2, ensure_ascii=False)
      if input_lang!=output_lang:
        if method=="LLM Translation":
          prompt=prompt_maker(readable_json,output_lang,task)
  except Exception as e:
    print(f"Error processing media: {e}")

  return json_transcription,readable_json,prompt





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

def prompt_maker(transcription,target_language, task="Translation"):
    txt_path="./temp.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(transcription)
        if task == "Translation":
            f.write(prompt_translation(target_language))
        else:
            f.write(prompt_fix_grammar(target_language))

    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content
