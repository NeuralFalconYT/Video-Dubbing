from kokoro import KPipeline
import soundfile as sf
kokoro_pipeline=None
import re 
import uuid 
import os 
def temp_tts_file_name(text, language="en"):
    save_folder="./kokoro_tts"
    os.makedirs(save_folder,exist_ok=True)
    # Clean and process the text
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Keep only letters and spaces
    text = text.lower().strip().replace(" ", "_")

    # Ensure the text is not empty
    if not text:
        text = "audio"

    # Truncate to first 20 characters for filename
    truncated_text = text[:20]

    # Sanitize and format the language tag
    language = re.sub(r'\s+', '_', language.strip().lower()) if language else "unknown"

    # Generate random suffix
    random_string = uuid.uuid4().hex[:8].upper()

    # Construct the filename
    file_name = f"{save_folder}/{truncated_text}_{language}_{random_string}.wav"
    return file_name


def run_kokoro_tts(text,language="American English",voice='af_heart',speed=1.0):
  global kokoro_pipeline
  language_map_local = {
  "English": "en",
  "Hindi": "hi",
  "Spanish": "es",
  "French": "fr",
  "Italian": "it",
  "Brazilian Portuguese": "pt",
  "Japanese": "ja",
  "Mandarin Chinese": "zh-CN"
  }

  language_map = {
    "English":"a",
    "American English": "a",
    "British English": "b",
    "Hindi": "h",
    "Spanish": "e",
    "French": "f",
    "Italian": "i",
    "Brazilian Portuguese": "p",
    "Japanese": "j",
    "Mandarin Chinese": "z"
}

  lang_code=language_map.get(language,"a")
  if kokoro_pipeline is None:
    kokoro_pipeline = KPipeline(lang_code=lang_code)
  lang_code=language_map_local.get(language,"en")
  file_name=temp_tts_file_name(text, language=lang_code)
  generator = kokoro_pipeline(text, voice=voice,speed=speed)
  for i, (gs, ps, audio) in enumerate(generator):
    sf.write(file_name, audio, 24000)
  return file_name
