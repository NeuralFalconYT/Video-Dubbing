# %%writefile /content/Video-Dubbing/turbo_tts.py
# %cd /content/Video-Dubbing/
import sys
import os
chatterbox=f"{os.getcwd()}/chatterbox/src"
sys.path.append(chatterbox)




import random
import numpy as np
import torch
from chatterbox.tts_turbo import ChatterboxTurboTTS
from tts import unload_multilingual_model
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = None
def get_or_load_model():
    """Loads the ChatterboxMultilingualTTS model if it hasn't been loaded already,
    and ensures it's on the correct device."""
    global MODEL
    if MODEL is None:
        print("Model not loaded, initializing...")
        try:
            MODEL = ChatterboxTurboTTS.from_pretrained(DEVICE)
            if hasattr(MODEL, 'to') and str(MODEL.device) != DEVICE:
                MODEL.to(DEVICE)
            print(f"Model loaded successfully. Internal device: {getattr(MODEL, 'device', 'N/A')}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    return MODEL

import gc

def unload_turbo_model():
    global MODEL
    if MODEL is not None:
        print("🧹 Unloading Turbo model...")
        del MODEL
        MODEL = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        print("✅ Turbo model fully unloaded")


# MODEL = ChatterboxTurboTTS.from_pretrained("cuda" )



def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)

# def generate(
#         text,
#         audio_prompt_path,
#         temperature,
#         seed_num,
#         min_p,
#         top_p,
#         top_k,
#         repetition_penalty,
#         norm_loudness
# ):
#     if seed_num != 0:
#         set_seed(int(seed_num))

#     wav = MODEL.generate(
#         text,
#         audio_prompt_path=audio_prompt_path,
#         temperature=temperature,
#         min_p=min_p,
#         top_p=top_p,
#         top_k=int(top_k),
#         repetition_penalty=repetition_penalty,
#         norm_loudness=norm_loudness,
#     )

#     return (MODEL.sr, wav.squeeze(0).cpu().numpy())


from sentencex import segment
import re
import uuid
import shutil
temp_audio_dir="./cloned_voices"
os.makedirs(temp_audio_dir, exist_ok=True)

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
    file_name=file_name.replace("__","_")
    return file_name


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

def split_into_chunks(text,lang_code="en", max_char_limit=300):
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
import soundfile as sf
from tqdm.auto import tqdm
from pydub import AudioSegment
from pydub.silence import split_on_silence
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


       
def generate(
    text,
    audio_prompt_path,
    temperature,
    seed_num,
    min_p,
    top_p,
    top_k,
    repetition_penalty,
    norm_loudness,
    remove_silence=False,
    output_format="wav",
    minimum_silence=0.05,  
    mp3_bitrate="192k",
    low_gpu=True
):   
    if low_gpu:
      unload_multilingual_model()
    minimum_silence = int(minimum_silence * 1000)
    turbo_model = get_or_load_model() 
    assert output_format in ["wav", "mp3"], "output_format must be 'wav' or 'mp3'"

    # -------------------------
    # Seed
    # -------------------------
    if seed_num != 0:
        set_seed(int(seed_num))

    # -------------------------
    # Text processing
    # -------------------------
    text = clean_text(text)
    chunks = split_into_chunks(text, "en", max_char_limit=300)

    if not chunks:
        raise ValueError("No text chunks produced")

    # -------------------------
    # Paths
    # -------------------------
    base_path = tts_file_name(text)
    wav_path = base_path.replace(".mp3", ".wav").replace(".wav", ".wav")
    final_path = (
        wav_path if output_format == "wav"
        else wav_path.replace(".wav", ".mp3")
    )

    sr = MODEL.sr
    channels = 1

    # -------------------------
    # Stream WAV to disk
    # -------------------------
    with sf.SoundFile(
        wav_path,
        mode="w",
        samplerate=sr,
        channels=channels,
        subtype="PCM_16",
    ) as out_f:
        for idx, chunk in enumerate(chunks):
        # for idx, chunk in tqdm(
        #     enumerate(chunks),
        #     total=len(chunks),
        #     desc="Generating audio (streaming)",
        # ):
            try:
                print(f"Generating chunk {idx+1}/{len(chunks)}")
                # print(f"Text: {chunk}")
                wav = turbo_model.generate(
                    chunk,
                    audio_prompt_path=audio_prompt_path,
                    temperature=temperature,
                    min_p=min_p,
                    top_p=top_p,
                    top_k=int(top_k),
                    repetition_penalty=repetition_penalty,
                    norm_loudness=norm_loudness,
                )

                audio = wav.squeeze(0).detach().cpu().numpy()

                if audio.size == 0:
                    raise ValueError("Empty audio chunk")

                audio = audio.astype(np.float32)

                out_f.write(audio)

                del wav, audio
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            except Exception as e:
                # print(f"⚠️ Chunk {idx} failed | len={len(chunk)} | {e}")
                # gr.Warning(f"⚠️ Audio generation failed.", duration=5)
                continue

    # -------------------------
    # Convert to MP3 if needed
    # -------------------------
    if output_format == "mp3":
        audio = AudioSegment.from_wav(wav_path)
        audio.export(final_path, format="mp3", bitrate=mp3_bitrate)
        os.remove(wav_path)
    if not os.path.exists(final_path):
      return None,None
    else:    
      if remove_silence:
        final_path=remove_silence_function(final_path,minimum_silence=minimum_silence)
      return final_path,final_path


# import gradio as gr


# def turbo_tts_ui():
#   EVENT_TAGS = [
#       "[clear throat]", "[sigh]", "[shush]", "[cough]", "[groan]",
#       "[sniff]", "[gasp]", "[chuckle]", "[laugh]"
#   ]

#   CUSTOM_CSS = """
#   .tag-container {
#       display: flex !important;
#       flex-wrap: wrap !important;
#       gap: 8px !important;
#       margin-top: 5px !important;
#       margin-bottom: 10px !important;
#       border: none !important;
#       background: transparent !important;
#   }
#   .tag-btn {
#       min-width: fit-content !important;
#       width: auto !important;
#       height: 32px !important;
#       font-size: 13px !important;
#       background: #eef2ff !important;
#       border: 1px solid #c7d2fe !important;
#       color: #3730a3 !important;
#       border-radius: 6px !important;
#       padding: 0 10px !important;
#       margin: 0 !important;
#       box-shadow: none !important;
#   }
#   .tag-btn:hover {
#       background: #c7d2fe !important;
#       transform: translateY(-1px);
#   }
#   .gradio-container 
#   { font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; }
#   """

#   INSERT_TAG_JS = """
#   (tag_val, current_text) => {
#       const textarea = document.querySelector('#main_textbox textarea');
#       if (!textarea) return current_text + " " + tag_val;
#       const start = textarea.selectionStart;
#       const end = textarea.selectionEnd;
#       let prefix = " ";
#       let suffix = " ";
#       if (start === 0) prefix = "";
#       else if (current_text[start - 1] === ' ') prefix = "";
#       if (end < current_text.length && current_text[end] === ' ') suffix = "";
#       return current_text.slice(0, start) + prefix + tag_val + suffix + current_text.slice(end);
#   }
#   """


#   with gr.Blocks(theme=gr.themes.Soft(), css=CUSTOM_CSS) as demo:
#       gr.HTML("""
#           <div style="text-align: center; margin: 20px auto; max-width: 800px;">
#               <h1 style="font-size: 2.5em; margin-bottom: 5px;">⚡ Chatterbox Turbo</h1>
#           </div>""")
#       with gr.Row():
#           with gr.Column():
#               text = gr.Textbox(
#                   value="Oh, that's hilarious! [chuckle] Um anyway, we do have a new model in store. It's the SkyNet T-800 series and it's got basically everything. Including AI integration with ChatGPT and all that jazz. Would you like me to get some prices for you?",
#                   label="Text to synthesize",
#                   max_lines=5,
#                   elem_id="main_textbox"
#               )

#               with gr.Row(elem_classes=["tag-container"]):
#                   for tag in EVENT_TAGS:
#                       btn = gr.Button(tag, elem_classes=["tag-btn"])
#                       btn.click(
#                           fn=None,
#                           inputs=[btn, text],
#                           outputs=text,
#                           js=INSERT_TAG_JS
#                       )

#               ref_wav = gr.Audio(
#                   sources=["upload", "microphone"],
#                   type="filepath",
#                   label="Reference Audio File",
#                   value="https://storage.googleapis.com/chatterbox-demo-samples/turbo/2.wav",
#               )

#               run_btn = gr.Button("Generate ⚡", variant="primary")
#               with gr.Accordion("Audio Settings", open=False):
#                 with gr.Row():
#                     output_format = gr.Radio(
#                         choices=["wav", "mp3"],
#                         value="wav",
#                         label="Output Audio Format",
#                     )

#                     rm_silence = gr.Checkbox(
#                         value=False,
#                         label="Remove Silence From Audio"
#                     )

#                     min_silence = gr.Number(
#                         label="Keep Silence Upto (seconds)",
#                         value=0.05
#                     )

#               with gr.Accordion("Advanced Options", open=False):
#                   seed_num = gr.Number(value=0, label="Random seed (0 for random)")
#                   temp = gr.Slider(0.05, 2.0, step=.05, label="Temperature", value=0.8)
#                   top_p = gr.Slider(0.00, 1.00, step=0.01, label="Top P", value=0.95)
#                   top_k = gr.Slider(0, 1000, step=10, label="Top K", value=1000)
#                   repetition_penalty = gr.Slider(1.00, 2.00, step=0.05, label="Repetition Penalty", value=1.2)
#                   min_p = gr.Slider(0.00, 1.00, step=0.01, label="Min P (Set to 0 to disable)", value=0.00)
#                   norm_loudness = gr.Checkbox(value=True, label="Normalize Loudness (-27 LUFS)")

#           with gr.Column():
#               audio_output = gr.Audio(label="Output Audio")
#               audio_download= gr.File(label="Download Audio")



#       run_btn.click(
#           fn=generate,
#           inputs=[
#               text,
#               ref_wav,
#               temp,
#               seed_num,
#               min_p,
#               top_p,
#               top_k,
#               repetition_penalty,
#               norm_loudness,
#               rm_silence,
#               output_format,
#               min_silence,
#           ],
#           outputs=[audio_output,audio_download]
#       )
#   return demo
# if __name__ == "__main__":
#     demo=turbo_tts_ui()
#     demo.queue().launch(
#         share=True,
#         debug=True

#     )


# # import click
# # @click.command()
# # @click.option("--debug", is_flag=True, default=False, help="Enable debug mode.")
# # @click.option("--share", is_flag=True, default=False, help="Enable sharing of the interface.")
# # def main(debug, share):
# #     demo=turbo_tts_ui()
# #     demo.queue().launch(debug=debug, share=share)
# # if __name__ == "__main__":
# #     main()    
