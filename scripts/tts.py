#@title /content/Video-Dubbing/tts.py
# %%writefile /content/Video-Dubbing/tts.py
import sys
import os
# chatterbox=f"{os.getcwd()}/chatterbox/src"
# sys.path.append(chatterbox)


import sys
import os

# Get absolute path of the root project folder
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /content/Video-Dubbing
CHATTERBOX_SRC = os.path.join(ROOT_DIR, "chatterbox", "src")

# Add chatterbox/src to sys.path if not already present
if CHATTERBOX_SRC not in sys.path:
    sys.path.append(CHATTERBOX_SRC)

print("✅ Added to sys.path:", CHATTERBOX_SRC)



from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
import tempfile
import random
import numpy as np
import torch

from sentencex import segment
import re
from tqdm.auto import tqdm
import os
import shutil
import soundfile as sf
import uuid
from pydub import AudioSegment
from pydub.silence import split_on_silence
import random
temp_audio_dir="./cloned_voices"
os.makedirs(temp_audio_dir, exist_ok=True)




DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = None
def get_or_load_model():
    """Loads the ChatterboxMultilingualTTS model if it hasn't been loaded already,
    and ensures it's on the correct device."""
    global MODEL
    if MODEL is None:
        print("Model not loaded, initializing...")
        try:
            MODEL = ChatterboxMultilingualTTS.from_pretrained(DEVICE)
            if hasattr(MODEL, 'to') and str(MODEL.device) != DEVICE:
                MODEL.to(DEVICE)
            print(f"Model loaded successfully. Internal device: {getattr(MODEL, 'device', 'N/A')}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    return MODEL


def set_seed(seed: int):
    """Sets the random seed for reproducibility across torch, numpy, and random."""
    torch.manual_seed(seed)
    if DEVICE == "cuda":
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)


def generate_tts_audio(
    text_input: str,
    language_id: str,
    audio_prompt_path_input: str = None,
    exaggeration_input: float = 0.5,
    temperature_input: float = 0.8,
    seed_num_input: int = 0,
    cfgw_input: float = 0.5
) -> tuple[int, np.ndarray]:
    """
    Generate high-quality speech audio from text using Chatterbox Multilingual model with optional reference audio styling.
    Supported languages: English, French, German, Spanish, Italian, Portuguese, and Hindi.

    This tool synthesizes natural-sounding speech from input text. When a reference audio file
    is provided, it captures the speaker's voice characteristics and speaking style. The generated audio
    maintains the prosody, tone, and vocal qualities of the reference speaker, or uses default voice if no reference is provided.

    Args:
        text_input (str): The text to synthesize into speech (maximum 300 characters)
        language_id (str): The language code for synthesis (eg. en, fr, de, es, it, pt, hi)
        audio_prompt_path_input (str, optional): File path or URL to the reference audio file that defines the target voice style. Defaults to None.
        exaggeration_input (float, optional): Controls speech expressiveness (0.25-2.0, neutral=0.5, extreme values may be unstable). Defaults to 0.5.
        temperature_input (float, optional): Controls randomness in generation (0.05-5.0, higher=more varied). Defaults to 0.8.
        seed_num_input (int, optional): Random seed for reproducible results (0 for random generation). Defaults to 0.
        cfgw_input (float, optional): CFG/Pace weight controlling generation guidance (0.2-1.0). Defaults to 0.5, 0 for language transfer.

    Returns:
        tuple[int, np.ndarray]: A tuple containing the sample rate (int) and the generated audio waveform (numpy.ndarray)
    """
    current_model = get_or_load_model()

    if current_model is None:
        raise RuntimeError("TTS model is not loaded.")

    if seed_num_input != 0:
        set_seed(int(seed_num_input))

    print(f"Generating audio for text: '{text_input[:50]}...'")

    # Handle optional audio prompt
    chosen_prompt = audio_prompt_path_input or default_audio_for_ui(language_id)

    generate_kwargs = {
        "exaggeration": exaggeration_input,
        "temperature": temperature_input,
        "cfg_weight": cfgw_input,
    }
    if chosen_prompt:
        generate_kwargs["audio_prompt_path"] = chosen_prompt
        print(f"Using audio prompt: {chosen_prompt}")
    else:
        print("No audio prompt provided; using default voice.")

    wav = current_model.generate(
        text_input,  #max 300 chars
        language_id=language_id,
        **generate_kwargs
    )
    print("Audio generation complete.")
    return current_model.sr, wav.squeeze(0).numpy()



supported_languages = {
    "English": "en",
    "Hindi": "hi",
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Danish": "da",
    "Dutch": "nl",
    "Finnish": "fi",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Hebrew": "he",
    "Italian": "it",
    "Malay": "ms",
    "Norwegian": "no",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Swahili": "sw",
    "Swedish": "sv",
    "Turkish": "tr"
}
def word_split(text, char_limit=300):
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + (1 if current_chunk else 0) <= char_limit:
            current_chunk += (" " if current_chunk else "") + word
        else:
            chunks.append(current_chunk)
            current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def split_into_chunks(text,lang_code, max_char_limit=300):
    global supported_languages
    if len(text)>=300:
      print("⚠️ The text is too long. Breaking it into smaller pieces so the voice generation works correctly.")
      raw_sentences = list(segment(lang_code, text))

      # Flattened list of sentence-level word chunks
      sentence_chunks = []
      for sen in raw_sentences:
          sentence_chunks.extend(word_split(sen, char_limit=max_char_limit))

      chunks = []
      temp_str = ""

      for sentence in sentence_chunks:
          if len(temp_str) + len(sentence) + (1 if temp_str else 0) <= max_char_limit:
              temp_str += (" " if temp_str else "") + sentence
          else:
              chunks.append(temp_str)
              temp_str = sentence

      if temp_str:
          chunks.append(temp_str)

      return chunks
    else:
      return [text]


def clean_text(text):
    # Define replacement rules
    replacements = {
        "–": " ",  # Replace en-dash with space
        "—": " ",  #
        "-": " ",  # Replace hyphen with space
        "**": " ", # Replace double asterisks with space
        "*": " ",  # Replace single asterisk with space
        "#": " ",  # Replace hash with space
    }

    # Apply replacements
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove emojis using regex (covering wide range of Unicode characters)
    emoji_pattern = re.compile(
        r'[\U0001F600-\U0001F64F]|'  # Emoticons
        r'[\U0001F300-\U0001F5FF]|'  # Miscellaneous symbols and pictographs
        r'[\U0001F680-\U0001F6FF]|'  # Transport and map symbols
        r'[\U0001F700-\U0001F77F]|'  # Alchemical symbols
        r'[\U0001F780-\U0001F7FF]|'  # Geometric shapes extended
        r'[\U0001F800-\U0001F8FF]|'  # Supplemental arrows-C
        r'[\U0001F900-\U0001F9FF]|'  # Supplemental symbols and pictographs
        r'[\U0001FA00-\U0001FA6F]|'  # Chess symbols
        r'[\U0001FA70-\U0001FAFF]|'  # Symbols and pictographs extended-A
        r'[\U00002702-\U000027B0]|'  # Dingbats
        r'[\U0001F1E0-\U0001F1FF]'   # Flags (iOS)
        r'', flags=re.UNICODE)

    text = emoji_pattern.sub(r'', text)

    # Remove multiple spaces and extra line breaks
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def tts_file_name(text, language="en"):
    global temp_audio_dir
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
    file_name = f"{temp_audio_dir}/{truncated_text}_{language}_{random_string}.wav"
    return file_name
def remove_silence_function(file_path,minimum_silence=50):
    # Extract file name and format from the provided path
    output_path = file_path.replace(".wav", "_no_silence.wav")
    audio_format = "wav"
    # Reading and splitting the audio file into chunks
    sound = AudioSegment.from_file(file_path, format=audio_format)
    audio_chunks = split_on_silence(sound,
                                    min_silence_len=100,
                                    silence_thresh=-45,
                                    keep_silence=minimum_silence)
    # Putting the file back together
    combined = AudioSegment.empty()
    for chunk in audio_chunks:
        combined += chunk
    combined.export(output_path, format=audio_format)
    return output_path

def clone_voice( text,
                audio_prompt_path_input,
    lang_name="English",
    exaggeration_input= 0.5,
    temperature_input= 0.8,
    seed_num_input = 0,
    cfgw_input= 0.5):
    global supported_languages
    language_id=supported_languages.get(lang_name,"en")
    text = clean_text(text)
    chunks = split_into_chunks(text,language_id, max_char_limit=300)
    temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
    temp_files = []
    for idx, chunk in tqdm(enumerate(chunks), total=len(chunks), desc="Generating audio"):

      # print(len(chunk))
      # print(chunk)
      # print(chunk_path)
      try:
        chunk_path = os.path.join(temp_dir, f"chunk_{idx:03}.wav")
        sr, audio =generate_tts_audio(
            chunk,
            language_id,
            audio_prompt_path_input,
            exaggeration_input,
            temperature_input,
            seed_num_input,
            cfgw_input
        )
        sf.write(chunk_path, audio, sr)
        print(sr)
        temp_files.append(chunk_path)
      except Exception as e:
        print(f"⚠️ [Chunk {idx}] Generation failed: {e}")
        print(f"Text: {chunk}")
        print(f"Length: {len(chunk)}")
        continue  # Skip failed chunk
            # Merge all valid chunks
    final_audio = []
    for file_path in temp_files:
      try:
        data, _ = sf.read(file_path)
        final_audio.append(data)
      except Exception as e:
        print(f"💀 [Merging] Failed to read chunk: {file_path} ({e})")
    final_path=None
    if final_audio:
      final_audio = np.concatenate(final_audio)
      final_path = tts_file_name(text,language_id)
      sf.write(final_path, final_audio, sr)
    else:
      raise RuntimeError("All audio chunk generations failed.")
    shutil.rmtree(temp_dir)
    return final_path


def clone_voice_streaming(
    text,
    audio_prompt_path_input,
    lang_name="English",
    exaggeration_input=0.5,
    temperature_input=0.8,
    seed_num_input=0,
    cfgw_input=0.5,
    stereo=False,
    remove_silence=False,
):
    if not os.path.exists(audio_prompt_path_input):
      print("⚠️ Reference Audio File Not Found")
      print(audio_prompt_path_input)
      return None
    if seed_num_input == 0:
        seed_num_input = random.randint(1, 999999)
        print(f"🔑 Auto-generated seed: {seed_num_input}")
    language_id = supported_languages.get(lang_name, "en")
    text = clean_text(text)
    chunks = split_into_chunks(text, language_id, max_char_limit=300)

    final_path = tts_file_name(text, language_id)
    samplerate = 24000  # fixed
    channels = 2 if stereo else 1

    # Open final file for writing, append each chunk
    with sf.SoundFile(final_path, mode='w', samplerate=samplerate, channels=channels, subtype='PCM_16') as f:
        for idx, chunk in tqdm(enumerate(chunks), total=len(chunks), desc="Generating audio"):
            try:
                sr, audio = generate_tts_audio(
                    chunk,
                    language_id,
                    audio_prompt_path_input,
                    exaggeration_input,
                    temperature_input,
                    seed_num_input,
                    cfgw_input
                )

                # Convert to 2D array if necessary
                if audio.ndim == 1:
                    if stereo:
                        audio = np.stack([audio, audio], axis=1)  # duplicate channel
                    else:
                        audio = audio[:, None]  # mono 2D array

                f.write(audio)
            except Exception as e:
                print(f"⚠️ [Chunk {idx}] Generation failed: {e}")
                continue
    if remove_silence:
      return remove_silence_function(final_path,minimum_silence=50)
    else:
      return final_path

##Test 
# %cd /content/Video-Dubbing/
# from tts import clone_voice_streaming

# text = "Elias Thorne lived a life defined by precise lines. As the unofficial, self-appointed cartographer of Port Blossom—a tiny, grey-stone village clinging to the cliff face of the Cornish coast—his days were spent tracing the shifting boundaries of the familiar. His maps were not for navigation, but for contemplation: the subtle drift of the shingle beach after a winter storm, the forgotten network of Roman foundations beneath the old church, the precise length of Mrs. Gable’s prize-winning marrow."  # @param {type: "string"}
# reference_voice = '/content/test.mp3'  # @param {type: "string"}

# output_path=clone_voice_streaming(
#     text,
#     reference_voice,
#     lang_name="English",
#     exaggeration_input=0.5,
#     temperature_input=0.8,
#     seed_num_input=0,
#     cfgw_input=0.5,
#     stereo=False,
#     remove_silence=False,
# )
# from IPython.display import clear_output
# clear_output()
# print(output_path)

# from google.colab import files
# files.download(output_path)


# #For Subtitle
# from STT.subtitle import subtitle_maker

# media_file = output_path
# source_lang = "English"
# target_lang = "English"

# default_srt, translated_srt_path, custom_srt, word_srt, shorts_srt, txt_path,sentence_json,word_json, transcript= subtitle_maker(
#     media_file, source_lang, target_lang
# )
# clear_output()
# print(custom_srt)
