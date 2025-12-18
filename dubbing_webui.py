# %cd /content/Video-Dubbing/

import gradio as gr
import json
import os
import shutil
from dubbing_pipeline import dubbing,make_video
from utils import get_dubbing_json,get_speakers,restore_music

from tts import supported_languages
MAX_SPEAKERS = 10


# --- CORRECTED AND IMPROVED FUNCTION ---

# --- FINAL, IMPROVED FUNCTION with Progress Bar and Disabled Inputs ---

def extract_speakers_ui(media_file, have_music, llm_result_text, progress=gr.Progress()):
    if not media_file or not os.path.exists(media_file):
        raise gr.Error("Please provide a valid media file path.")
    if not llm_result_text:
        raise gr.Error("Please paste the translation JSON to extract speakers.")

    # --- Stage 1: Fast initial processing and first UI update ---
    try:
        progress(0, desc="Parsing JSON and preparing...")
        llm_data = json.loads(llm_result_text)
        dubbing_json = get_dubbing_json(llm_data)
        speaker_ids = sorted(list(set(int(item["speaker_id"]) for item in dubbing_json.values())))
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise gr.Error(f"Invalid JSON format or structure: {e}")

    initial_updates = []
    initial_speaker_voice_state = {sid: {} for sid in speaker_ids}

    display_id=1  
    for i in range(MAX_SPEAKERS):
        if i in speaker_ids:
            # Make component visible BUT NOT INTERACTIVE
            initial_updates.append(
                gr.update(
                    visible=True,
                    value=None,
                    label=f"🎤 Speaker {display_id} (Extracting voice...)",
                    interactive=False  # <-- THIS IS THE KEY CHANGE
                )
            )
            display_id+=1
        else:
            initial_updates.append(gr.update(visible=False))

    # YIELD the first update: show disabled components and a processing message
    processing_summary = f"Found {len(speaker_ids)} speaker(s). Please wait while their voices are extracted..."
    yield dubbing_json, initial_speaker_voice_state, gr.update(value=processing_summary, visible=True), *initial_updates


    # --- Stage 2: Slow background processing with progress tracking ---
    progress(0.5, desc="Extracting speaker voices from media. This may take a minute...")
    speaker_voice = get_speakers(media_file, have_music, llm_data)
    speaker_voice = {int(k): v for k, v in speaker_voice.items()}
    progress(1, desc="Extraction Complete!")


    # --- Stage 3: Final UI update with results ---
    final_updates = []
    for i in range(MAX_SPEAKERS):
        if i in speaker_voice:
            info = speaker_voice[i]
            file_path = info.get("reference_audio")
            # Update component with the audio file and MAKE IT INTERACTIVE
            final_updates.append(
                gr.update(
                    value=file_path,
                    label=f"🎤 Speaker {i} (Reference)",
                    interactive=True # <-- MAKE IT USABLE AGAIN
                )
            )
        else:
            final_updates.append(gr.update()) # No change

    # YIELD the final update: populate the audio components and show the final message
    final_summary = f"✅ Detected {len(speaker_voice)} speaker(s). You can replace their voices below."
    yield dubbing_json, speaker_voice, gr.update(value=final_summary, visible=True), *final_updates





# --- FIXED FUNCTION ---
def start_dubbing_ui(
    media_file, language_name, have_music, want_subtitle, llm_result_text,
    exaggeration, cfg_weight, temp,need_video,recover_audio,redub
    dubbing_json_state, speaker_voice_state,
    *speaker_audios
):
    if not dubbing_json_state or not speaker_voice_state:
        raise gr.Error("Please extract speakers first before starting the dubbing process.")

    os.makedirs("./speaker_voice", exist_ok=True)

    # Copy the initial state to a new dictionary that we will modify.
    updated_speaker_voice = {sid: info.copy() for sid, info in speaker_voice_state.items()}

    # The 'speaker_audios' variable is a tuple containing the file paths from the
    # MAX_SPEAKERS gr.Audio components. The index of the tuple corresponds to the speaker ID.
    # This loop iterates from sid = 0 to 9.
    for sid, audio_filepath in enumerate(speaker_audios):
        # We only need to do something if this speaker ID was actually detected.
        if sid in updated_speaker_voice:
            # If the user has uploaded a new audio file for this speaker in the UI...
            if audio_filepath:
                try:
                    # Define a consistent destination path for the speaker's reference audio.
                    ext = os.path.splitext(audio_filepath)[1] or ".wav"
                    dest_path = f"./speaker_voice/{sid}{ext}"
                    # Copy the file from the Gradio temp directory to our speaker voice directory.
                    shutil.copy(audio_filepath, dest_path)
                    # Update the dictionary to point to this new, copied file.
                    updated_speaker_voice[sid]["reference_audio"] = dest_path
                except Exception as e:
                    print(f"⚠️ Could not copy user-provided audio for speaker {sid}: {e}")
            # If audio_filepath is None, it means the user didn't upload a new file.
            # In this case, we simply rely on the original reference audio that's already
            # in 'updated_speaker_voice' from the initial extraction step. No action is needed.

    # Now call the main dubbing function with the correctly updated speaker voice mapping.
    dubbed_audio_path, dubbed_audio_file, returned_custom_srt, returned_default_srt, returned_word_srt, returned_shorts_srt ,redubbing_prompt= dubbing(
        media_file=media_file,
        dubbing_json=dubbing_json_state,
        speaker_voice=updated_speaker_voice,
        language_name=language_name,
        exaggeration_input=exaggeration,
        temperature_input=temp,
        cfgw_input=cfg_weight,
        want_subtile=want_subtitle,
        redub=redub,
    )

    dubbed_audio_with_music=None
    if recover_audio:
        dubbed_audio_with_music = restore_music(media_file, dubbed_audio_path)

    video_path=None
    if need_video:
      if recover_audio and dubbed_audio_with_music:
        video_path=make_video(media_file,dubbed_audio_with_music,language_name)
      else:
        video_path=make_video(media_file,dubbed_audio_path,language_name)
    drive_folder="/content/gdrive/MyDrive/Video_Dubbing"
    if os.path.exists(drive_folder):
        folder_name=os.path.splitext(os.path.basename(dubbed_audio_path))[0]
        folder_name=folder_name[:20]
        new_folder=f"{drive_folder}/{folder_name}/"
        os.makedirs(new_folder, exist_ok=True)
        for i in [dubbed_audio_path,dubbed_audio_with_music,returned_custom_srt,video_path,returned_default_srt,returned_word_srt,returned_shorts_srt]:
            try:
                shutil.copy(i,new_folder)
            except Exception as e:
                print(e)
                pass
        
    return (
        dubbed_audio_path,
        dubbed_audio_with_music,
        returned_custom_srt,
        video_path,
        returned_default_srt,
        returned_word_srt,
        returned_shorts_srt,
        dubbed_audio_file,
        dubbed_audio_with_music,
        video_path,
        redubbing_prompt
    )


def dubbing_ui():
  with gr.Blocks() as demo:
      gr.Markdown("# 🎙️ Video Dubbing Pipeline")
      gr.Markdown("Step 1: Provide your media file and settings. Step 2: Extract speakers. Step 3: Start Dubbing!")

      dubbing_json_state = gr.State()
      speaker_voice_state = gr.State()

      with gr.Row():
          with gr.Column(scale=1):
              gr.Markdown("### ⚙️ Inputs & Settings")
              media_file = gr.Textbox(label="Paste Media File Path",placeholder="/tmp/gradio/.....")
              language_name = gr.Dropdown(list(supported_languages.keys()), label="🌍 Select Language", value="Hindi")
              have_music = gr.Checkbox(value=True, label="Clean speaker voice from media file?")
              llm_result = gr.Textbox(label="Paste LLM Translation", max_lines=10)
              generate_speaker_btn = gr.Button("🚀 Step 1: Extract Speakers [Wait for a minutes]", variant="primary")

              with gr.Accordion("Advanced TTS Options", open=False):
                  exaggeration = gr.Slider(0.25, 2, step=.05, label="Exaggeration", value=.5)
                  cfg_weight = gr.Slider(0.2, 1, step=.05, label="CFG/Pace", value=0.5)
                  temp = gr.Slider(0.05, 5, step=.05, label="Temperature", value=.8)
              with gr.Accordion("Video Maker", open=True):
                  recover_audio=gr.Checkbox(value=True, label="🎧 Restore background music and ambience ?")
                  need_video=gr.Checkbox(value=True, label="🎬 Make Video ?")
                  want_subtitle = gr.Checkbox(value=True, label="Generate Subtitles for the dubbed audio?")
              with gr.Accordion("Redub", open=False):
                      redub = gr.Checkbox(value=True,label="🎬 Redub due to long TTS")

          with gr.Column(scale=2):
              gr.Markdown("### 🗣️ Speaker Reference Audio")
              speaker_summary = gr.Markdown(visible=False)
              gr.Markdown("Detected speaker reference audio clips will appear below. Replace them if you want custom voices.")
              speaker_audios = [
                  gr.Audio(label=f"🎤 Speaker {i} (Reference)", visible=False, interactive=True, type="filepath")
                  for i in range(MAX_SPEAKERS)
              ]

              dubbing_btn = gr.Button("🎬 Step 2: Start Dubbing", variant="primary")

              gr.Markdown("### 🎉 Outputs")
              output_audio = gr.Audio(interactive=False, label="🎧 Dubbed Audio Output", autoplay=False)
              output_audio_music = gr.Audio(interactive=False, label="🎵 Dubbed Voice + Restored Background & Ambience", autoplay=False)
              custom_level_srt = gr.File(label="🗂️ Multi line srt")
              display_video=gr.Video(label="📽️ Video")

              with gr.Accordion("📦Download Others Subtitle Format", open=False):
                  default_srt = gr.File(label="📝 Default SRT (Whisper-style)")
                  word_level_srt = gr.File(label="🔤 Word-Level SRT")
                  shorts_srt = gr.File(label="📱 Vertical Video SRT")
              with gr.Accordion("📦Download Audio & Video File [For colab]", open=False):
                  output_audio_file = gr.File(label="🎵 Download Dubbed Audio")
                  output_audio_music_file= gr.File(label="🎶 Download Dubbed Voice + Restored Background & Ambience")
                  video_path = gr.File(label="🎞️ Download Video")
              with gr.Accordion("✍️ Redub Prompt (TTS too long)", open=False):
                  redub_prompt=gr.Textbox(
                                       label="LLM Redubbing Prompt Copy & Paste this prompt in https://aistudio.google.com/",
                                       lines=5,show_copy_button=True)

      generate_speaker_btn.click(
          fn=extract_speakers_ui,
          inputs=[media_file, have_music, llm_result],
          outputs=[dubbing_json_state, speaker_voice_state, speaker_summary, *speaker_audios]
      )

      dubbing_btn.click(
          fn=start_dubbing_ui,
          inputs=[
              media_file, language_name, have_music, want_subtitle, llm_result,
              exaggeration, cfg_weight, temp,need_video,recover_audio,redub,
              dubbing_json_state, speaker_voice_state,
              *speaker_audios
          ],
          outputs=[
              output_audio,
              output_audio_music,
              custom_level_srt,
              display_video,
              default_srt,
              word_level_srt,
              shorts_srt,
              output_audio_file,
              output_audio_music_file,
              video_path,
              redub_prompt
          ]
      )
  return demo

  

# from dubbing_webui import dubbing_ui
# demo=dubbing_ui()
# demo.launch(share=True, debug=True) 
