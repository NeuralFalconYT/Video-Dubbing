# Code written by me, organized with the help of AI.
"""
A comprehensive toolkit for generating and translating subtitles from media files.

This module provides functionalities to:
1. Download AI models from Hugging Face without requiring a token.
2. Transcribe audio from media files using a high-performance Whisper model.
3. Generate multiple formats of SRT subtitles (default, professional multi-line, word-level, and shorts-style).
4. Translate subtitles into different languages.
5. Orchestrate the entire process through a simple-to-use main function.
"""

# ==============================================================================
# --- 1. IMPORTS
# ==============================================================================

import os
import re
import gc
import uuid
import math
import shutil
import string
import requests
import urllib.request
import urllib.error

import torch
import pysrt
from tqdm.auto import tqdm
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator


# ==============================================================================
# --- 2. CONSTANTS & CONFIGURATION
# ==============================================================================

# Folder paths for storing generated files and temporary audio
SUBTITLE_FOLDER = "./generated_subtitle"
TEMP_FOLDER = "./subtitle_audio"

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


# ==============================================================================
# --- 3. FILE & MODEL DOWNLOADING UTILITIES
# ==============================================================================

def download_file(url, download_file_path, redownload=False):
    """Download a single file with urllib and a tqdm progress bar."""
    base_path = os.path.dirname(download_file_path)
    os.makedirs(base_path, exist_ok=True)

    if os.path.exists(download_file_path):
        if redownload:
            os.remove(download_file_path)
            tqdm.write(f"♻️ Redownloading: {os.path.basename(download_file_path)}")
        elif os.path.getsize(download_file_path) > 0:
            tqdm.write(f"✔️ Skipped (already exists): {os.path.basename(download_file_path)}")
            return True

    try:
        request = urllib.request.urlopen(url)
        total = int(request.headers.get('Content-Length', 0))
    except urllib.error.URLError as e:
        print(f"❌ Error: Unable to open URL: {url}")
        print(f"Reason: {e.reason}")
        return False

    with tqdm(total=total, desc=os.path.basename(download_file_path), unit='B', unit_scale=True, unit_divisor=1024) as progress:
        try:
            urllib.request.urlretrieve(
                url,
                download_file_path,
                reporthook=lambda count, block_size, total_size: progress.update(block_size)
            )
        except urllib.error.URLError as e:
            print(f"❌ Error: Failed to download {url}")
            print(f"Reason: {e.reason}")
            return False

    tqdm.write(f"⬇️ Downloaded: {os.path.basename(download_file_path)}")
    return True


def download_model(repo_id, download_folder="./", redownload=False):
    """
    Downloads all files from a Hugging Face repository using the public API,
    avoiding the need for a Hugging Face token for public models.
    """
    if not download_folder.strip():
        download_folder = "."

    api_url = f"https://huggingface.co/api/models/{repo_id}"
    model_name = repo_id.split('/')[-1]
    download_dir = os.path.abspath(f"{download_folder.rstrip('/')}/{model_name}")
    os.makedirs(download_dir, exist_ok=True)

    print(f"📂 Download directory: {download_dir}")

    try:
        response = requests.get(api_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching repo info: {e}")
        return None

    data = response.json()
    files_to_download = [f["rfilename"] for f in data.get("siblings", [])]

    if not files_to_download:
        print(f"⚠️ No files found in repo '{repo_id}'.")
        return None

    print(f"📦 Found {len(files_to_download)} files in repo '{repo_id}'. Checking cache...")

    for file in tqdm(files_to_download, desc="Processing files", unit="file"):
        file_url = f"https://huggingface.co/{repo_id}/resolve/main/{file}"
        file_path = os.path.join(download_dir, file)
        download_file(file_url, file_path, redownload=redownload)

    return download_dir


# ==============================================================================
# --- 4. CORE TRANSCRIPTION & PROCESSING LOGIC
# ==============================================================================

def get_language_name(code):
    """Retrieves the full language name from its code."""
    for name, value in LANGUAGE_CODE.items():
        if value == code:
            return name
    return None

def clean_file_name(file_path):
    """Generates a clean, unique file name to avoid path issues."""
    dir_name = os.path.dirname(file_path)
    base_name, extension = os.path.splitext(os.path.basename(file_path))

    cleaned_base = re.sub(r'[^a-zA-Z\d]+', '_', base_name)
    cleaned_base = re.sub(r'_+', '_', cleaned_base).strip('_')
    random_uuid = uuid.uuid4().hex[:6]

    return os.path.join(dir_name, f"{cleaned_base}_{random_uuid}{extension}")

def format_segments(segments):
    """Formats the raw segments from Whisper into structured lists."""
    sentence_timestamp = []
    words_timestamp = []
    speech_to_text = ""

    for i in segments:
        text = i.text.strip()
        sentence_id = len(sentence_timestamp)
        sentence_timestamp.append({
            "id": sentence_id,
            "text": text,
            "start": i.start,
            "end": i.end,
            "words": []
        })
        speech_to_text += text + " "

        for word in i.words:
            word_data = {
                "word": word.word.strip(),
                "start": word.start,
                "end": word.end
            }
            sentence_timestamp[sentence_id]["words"].append(word_data)
            words_timestamp.append(word_data)

    return sentence_timestamp, words_timestamp, speech_to_text.strip()

def get_audio_file(uploaded_file):
    """Copies the uploaded media file to a temporary location for processing."""
    temp_path = os.path.join(TEMP_FOLDER, os.path.basename(uploaded_file))
    cleaned_path = clean_file_name(temp_path)
    shutil.copy(uploaded_file, cleaned_path)
    return cleaned_path

def whisper_subtitle(uploaded_file, source_language):
    """
    Main transcription function. Loads the model, transcribes the audio,
    and generates subtitle files.
    """
    # 1. Configure device and model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if torch.cuda.is_available() else "int8"
    model_dir = download_model(
        "deepdml/faster-whisper-large-v3-turbo-ct2",
        download_folder="./",
        redownload=False
    )
    model = WhisperModel(model_dir, device=device, compute_type=compute_type)
    # model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2",device=device, compute_type=compute_type)


    # 2. Process audio file
    audio_file_path = get_audio_file(uploaded_file)

    # 3. Transcribe
    detected_language = source_language
    if source_language == "Automatic":
        segments, info = model.transcribe(audio_file_path, word_timestamps=True)
        detected_lang_code = info.language
        detected_language = get_language_name(detected_lang_code)
    else:
        lang_code = LANGUAGE_CODE[source_language]
        segments, _ = model.transcribe(audio_file_path, word_timestamps=True, language=lang_code)

    sentence_timestamps, word_timestamps, transcript_text = format_segments(segments)

    # 4. Cleanup
    if os.path.exists(audio_file_path):
        os.remove(audio_file_path)
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 5. Prepare output file paths
    base_filename = os.path.splitext(os.path.basename(uploaded_file))[0][:30]
    srt_base = f"{SUBTITLE_FOLDER}/{base_filename}_{detected_language}.srt"
    clean_srt_path = clean_file_name(srt_base)
    txt_path = clean_srt_path.replace(".srt", ".txt")
    word_srt_path = clean_srt_path.replace(".srt", "_word_level.srt")
    custom_srt_path = clean_srt_path.replace(".srt", "_Multiline.srt")
    shorts_srt_path = clean_srt_path.replace(".srt", "_shorts.srt")

    # 6. Generate all subtitle files
    generate_srt_from_sentences(sentence_timestamps, srt_path=clean_srt_path)
    word_level_srt(word_timestamps, srt_path=word_srt_path)
    shorts_json=write_sentence_srt(
        word_timestamps, output_file=shorts_srt_path, max_lines=1,
        max_duration_s=2.0, max_chars_per_line=17
    )
    sentence_json=write_sentence_srt(
        word_timestamps, output_file=custom_srt_path, max_lines=2,
        max_duration_s=7.0, max_chars_per_line=38
    )

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(transcript_text)

    return (
        clean_srt_path, custom_srt_path, word_srt_path, shorts_srt_path,
        txt_path, transcript_text, sentence_json,shorts_json,detected_language
    )


# ==============================================================================
# --- 5. SUBTITLE GENERATION & FORMATTING
# ==============================================================================

def convert_time_to_srt_format(seconds):
    """Converts seconds to the standard SRT time format (HH:MM:SS,ms)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = round((seconds - int(seconds)) * 1000)

    if milliseconds == 1000:
        milliseconds = 0
        secs += 1
        if secs == 60:
            secs, minutes = 0, minutes + 1
            if minutes == 60:
                minutes, hours = 0, hours + 1

    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

def split_line_by_char_limit(text, max_chars_per_line=38):
    """Splits a string into multiple lines based on a character limit."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if not current_line:
            current_line = word
        elif len(current_line + " " + word) <= max_chars_per_line:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def merge_punctuation_glitches(subtitles):
    """Cleans up punctuation artifacts at the boundaries of subtitle entries."""
    if not subtitles:
        return []

    cleaned = [subtitles[0]]
    for i in range(1, len(subtitles)):
        prev = cleaned[-1]
        curr = subtitles[i]

        prev_text = prev["text"].rstrip()
        curr_text = curr["text"].lstrip()

        match = re.match(r'^([,.:;!?]+)(\s*)(.+)', curr_text)
        if match:
            punct, _, rest = match.groups()
            if not prev_text.endswith(tuple(punct)):
                prev["text"] = prev_text + punct
            curr_text = rest.strip()

        unwanted_chars = ['"', '“', '”', ';', ':']
        for ch in unwanted_chars:
            curr_text = curr_text.replace(ch, '')
        curr_text = curr_text.strip()

        if not curr_text or re.fullmatch(r'[.,!?]+', curr_text):
            prev["end"] = curr["end"]
            continue

        curr["text"] = curr_text
        prev["text"] = prev["text"].replace('"', '').replace('“', '').replace('”', '')
        cleaned.append(curr)

    return cleaned

import json
def write_sentence_srt(
    word_level_timestamps, output_file="subtitles_professional.srt", max_lines=2,
    max_duration_s=7.0, max_chars_per_line=38, hard_pause_threshold=0.5,
    merge_pause_threshold=0.4
):
    """Creates professional-grade SRT files and a corresponding timestamp.json file."""
    if not word_level_timestamps:
        return

    # Phase 1: Generate draft subtitles based on timing and length rules
    draft_subtitles = []
    i = 0
    while i < len(word_level_timestamps):
        start_time = word_level_timestamps[i]["start"]
        
        # We'll now store the full word objects, not just the text
        current_word_objects = []
        
        j = i
        while j < len(word_level_timestamps):
            entry = word_level_timestamps[j]
            
            # Create potential text from the word objects
            potential_words = [w["word"] for w in current_word_objects] + [entry["word"]]
            potential_text = " ".join(potential_words)

            if len(split_line_by_char_limit(potential_text, max_chars_per_line)) > max_lines: break
            if (entry["end"] - start_time) > max_duration_s and current_word_objects: break

            if j > i:
                prev_entry = word_level_timestamps[j-1]
                pause = entry["start"] - prev_entry["end"]
                if pause >= hard_pause_threshold: break
                if prev_entry["word"].endswith(('.','!','?')): break

            # Append the full word object
            current_word_objects.append(entry)
            j += 1

        if not current_word_objects:
            current_word_objects.append(word_level_timestamps[i])
            j = i + 1

        text = " ".join([w["word"] for w in current_word_objects])
        end_time = word_level_timestamps[j - 1]["end"]
        
        # Include the list of word objects in our draft subtitle
        draft_subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": text,
            "words": current_word_objects
        })
        i = j

    # Phase 2: Post-process to merge single-word "orphan" subtitles
    if not draft_subtitles: return
    final_subtitles = [draft_subtitles[0]]
    for k in range(1, len(draft_subtitles)):
        prev_sub = final_subtitles[-1]
        current_sub = draft_subtitles[k]
        is_orphan = len(current_sub["text"].split()) == 1
        pause_from_prev = current_sub["start"] - prev_sub["end"]

        if is_orphan and pause_from_prev < merge_pause_threshold:
            merged_text = prev_sub["text"] + " " + current_sub["text"]
            if len(split_line_by_char_limit(merged_text, max_chars_per_line)) <= max_lines:
                prev_sub["text"] = merged_text
                prev_sub["end"] = current_sub["end"]
                
                # Merge the word-level data as well
                prev_sub["words"].extend(current_sub["words"])
                continue

        final_subtitles.append(current_sub)

    final_subtitles = merge_punctuation_glitches(final_subtitles)
    print(final_subtitles)
    # ==============================================================================
    # NEW CODE BLOCK: Generate JSON data and write files
    # ==============================================================================
    
    # This dictionary will hold the data for our JSON file
    timestamps_data = {}
    
    # Phase 3: Write the final SRT file (and prepare JSON data)
    with open(output_file, "w", encoding="utf-8") as f:
        for idx, sub in enumerate(final_subtitles, start=1):
            # --- SRT Writing (Unchanged) ---
            text = sub["text"].replace(" ,", ",").replace(" .", ".")
            formatted_lines = split_line_by_char_limit(text, max_chars_per_line)
            start_time_str = convert_time_to_srt_format(sub['start'])
            end_time_str = convert_time_to_srt_format(sub['end'])
            
            f.write(f"{idx}\n")
            f.write(f"{start_time_str} --> {end_time_str}\n")
            f.write("\n".join(formatted_lines) + "\n\n")
            
            # --- JSON Data Population (New) ---
            # Create the list of word dictionaries for the current subtitle
            word_data = []
            for word_obj in sub["words"]:
                word_data.append({
                    "word": word_obj["word"],
                    "start": convert_time_to_srt_format(word_obj["start"]),
                    "end": convert_time_to_srt_format(word_obj["end"])
                })
            
            # Add the complete entry to our main dictionary
            timestamps_data[str(idx)] = {
                "text": "\n".join(formatted_lines),
                "start": start_time_str,
                "end": end_time_str,
                "words": word_data
            }

    # Write the collected data to the JSON file
    json_output_file = output_file.replace(".srt",".json")
    with open(json_output_file, "w", encoding="utf-8") as f_json:
        json.dump(timestamps_data, f_json, indent=4, ensure_ascii=False)
        
    print(f"Successfully generated SRT file: {output_file}")
    print(f"Successfully generated JSON file: {json_output_file}")
    return json_output_file

def write_subtitles_to_file(subtitles, filename="subtitles.srt"):
    """Writes a dictionary of subtitles to a standard SRT file."""
    with open(filename, 'w', encoding='utf-8') as f:
        for id, entry in subtitles.items():
            if entry['start'] is None or entry['end'] is None:
                print(f"Skipping subtitle ID {id} due to missing timestamps.")
                continue
            start_time = convert_time_to_srt_format(entry['start'])
            end_time = convert_time_to_srt_format(entry['end'])
            f.write(f"{id}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{entry['text']}\n\n")

def word_level_srt(words_timestamp, srt_path="word_level_subtitle.srt", shorts=False):
    """Generates an SRT file with one word per subtitle entry."""
    punctuation = re.compile(r'[.,!?;:"\–—_~^+*|]')
    with open(srt_path, 'w', encoding='utf-8') as srt_file:
        for i, word_info in enumerate(words_timestamp, start=1):
            start = convert_time_to_srt_format(word_info['start'])
            end = convert_time_to_srt_format(word_info['end'])
            word = re.sub(punctuation, '', word_info['word'])
            if word.strip().lower() == 'i': word = "I"
            if not shorts: word = word.replace("-", "")
            srt_file.write(f"{i}\n{start} --> {end}\n{word}\n\n")

def generate_srt_from_sentences(sentence_timestamp, srt_path="default_subtitle.srt"):
    """Generates a standard SRT file from sentence-level timestamps."""
    with open(srt_path, 'w', encoding='utf-8') as srt_file:
        for index, sentence in enumerate(sentence_timestamp, start=1):
            start = convert_time_to_srt_format(sentence['start'])
            end = convert_time_to_srt_format(sentence['end'])
            srt_file.write(f"{index}\n{start} --> {end}\n{sentence['text']}\n\n")


# ==============================================================================
# --- 6. TRANSLATION UTILITIES
# ==============================================================================

def translate_text(text, source_language, destination_language):
    """Translates a single block of text using GoogleTranslator."""
    source_code = LANGUAGE_CODE[source_language]
    target_code = LANGUAGE_CODE[destination_language]
    if destination_language == "Chinese":
        target_code = 'zh-CN'

    translator = GoogleTranslator(source=source_code, target=target_code)
    return str(translator.translate(text.strip()))

def translate_subtitle(subtitles, source_language, destination_language):
    """Translates the text content of a pysrt Subtitle object."""
    translated_text_dump = ""
    for sub in subtitles:
        translated_text = translate_text(sub.text, source_language, destination_language)
        sub.text = translated_text
        translated_text_dump += translated_text.strip() + " "
    return subtitles, translated_text_dump.strip()


# ==============================================================================
# --- 7. MAIN ORCHESTRATOR FUNCTION
# ==============================================================================

def subtitle_maker(media_file, source_lang, target_lang):
    """
    The main entry point to generate and optionally translate subtitles.

    Args:
        media_file (str): Path to the input media file.
        source_lang (str): The source language ('Automatic' for detection).
        target_lang (str): The target language for translation.

    Returns:
        A tuple containing paths to all generated files and the transcript text.
    """

    try:
        (
            default_srt, custom_srt, word_srt, shorts_srt,
            txt_path, transcript, sentence_json,word_json,detected_lang
        ) = whisper_subtitle(media_file, source_lang)
    except Exception as e:
        print(f"❌ An error occurred during transcription: {e}")
        return (None, None, None, None, None, None,None,None, f"Error: {e}")

    translated_srt_path = None
    if detected_lang and detected_lang != target_lang:
        print(f"TRANSLATING from {detected_lang} to {target_lang}")
        original_subs = pysrt.open(default_srt, encoding='utf-8')
        translated_subs, _ = translate_subtitle(original_subs, detected_lang, target_lang)
        base_name, ext = os.path.splitext(os.path.basename(default_srt))
        translated_filename = f"{base_name}_to_{target_lang}{ext}"
        translated_srt_path = os.path.join(SUBTITLE_FOLDER, translated_filename)
        translated_subs.save(translated_srt_path, encoding='utf-8')

    
    return (
        default_srt, translated_srt_path, custom_srt, word_srt,
        shorts_srt, txt_path,sentence_json,word_json, transcript
    )


# ==============================================================================
# --- 8. INITIALIZATION
# ==============================================================================
os.makedirs(SUBTITLE_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)


# from subtitle import subtitle_maker

# media_file = "video.mp4"
# source_lang = "English"
# target_lang = "English"

#   default_srt, translated_srt_path, custom_srt, word_srt, shorts_srt, txt_path,sentence_json,word_json, transcript= subtitle_maker(
#     media_file, source_lang, target_lang
# )
# If source_lang and target_lang are the same, translation will be skipped.

# default_srt      -> Original subtitles generated directly by Whisper-Large-V3-Turbo-CT2
# translated_srt   -> Translated subtitles (only generated if source_lang ≠ target_lang, 
#                      e.g., English → Hindi)
# custom_srt       -> Modified version of default subtitles with shorter segments 
#                      (better readability for horizontal videos, Maximum 38 characters per segment. )
# word_srt         -> Word-level timestamps (useful for creating YouTube Shorts/Reels)
# shorts_srt       -> Optimized subtitles for vertical videos (displays 3–4 words at a time , Maximum 17 characters per segment.)
# txt_path         -> Full transcript as plain text (useful for video summarization or for asking questions about the video or audio data with other LLM tools)
# sentence_json,word_json --> To Generate .ass file later
# transcript       -> Transcript text directly returned by the function, if you just need the transcript

# All functionality is contained in a single file, making it portable 
# and reusable across multiple projects for different purposes.
