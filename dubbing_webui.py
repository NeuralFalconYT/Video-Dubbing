# %cd /content/Video-Dubbing/
import gradio as gr
import json
import os
import shutil
from dubbing_pipeline import dubbing,make_video
from utils import get_dubbing_json,get_speakers,restore_music

from tts import supported_languages
MAX_SPEAKERS = 10


# --- UI LOGIC FUNCTIONS ---
def extract_speakers_ui(media_file, have_music, llm_result_text):
    if not media_file or not os.path.exists(media_file):
        raise gr.Error("Please provide a valid media file path.")

    if not llm_result_text:
        raise gr.Error("Please paste the translation JSON to extract speakers.")
    try:
        llm_data = json.loads(llm_result_text)
    except json.JSONDecodeError:
        raise gr.Error("Invalid JSON format in the 'LLM Translation' box.")

    # Process JSON and detect speakers
    dubbing_json = get_dubbing_json(llm_data)
    speaker_voice= get_speakers(media_file, have_music, llm_data)
    speaker_voice = {int(k): v for k, v in speaker_voice.items()}  # normalize
    # print("Backend generated speakers:", speaker_voice)

    # Dynamic UI update
    speaker_updates = []
    for i in range(MAX_SPEAKERS):
        sid = int(i)
        if sid in speaker_voice:
            info = speaker_voice[sid]
            file_path = info.get("reference_audio")
            if file_path and os.path.exists(file_path):
                speaker_updates.append(gr.update(value=file_path, visible=True))
            else:
                speaker_updates.append(gr.update(value=None, visible=True))
        else:
            speaker_updates.append(gr.update(value=None, visible=False))

    speaker_summary = f"✅ Detected {len(speaker_voice)} speaker(s). You can replace their voices below."
    return dubbing_json, speaker_voice, gr.update(value=speaker_summary, visible=True), *speaker_updates


def start_dubbing_ui(
    media_file, language_name, have_music, want_subtitle, llm_result_text,
    exaggeration, cfg_weight, temp,need_video,recover_audio,
    dubbing_json_state, speaker_voice_state,
    *speaker_audios
):
    if not dubbing_json_state or not speaker_voice_state:
        raise gr.Error("Please extract speakers first before starting the dubbing process.")

    os.makedirs("./speaker_voice", exist_ok=True)

    # Copy default state
    updated_speaker_voice = {sid: info.copy() for sid, info in speaker_voice_state.items()}
    # print("raw updated_speaker_voice")
    # print(updated_speaker_voice)
    # Replace with current /tmp/gradio/... files if provided
    gradio_audio_paths=[]
    for i in speaker_audios:
      if i is not None:
        gradio_audio_paths.append(i)
    for i, audio_filepath in enumerate(gradio_audio_paths):
        sid = int(i)
        if sid in updated_speaker_voice and audio_filepath:
            try:
                ext = os.path.splitext(audio_filepath)[1] or ".wav"
                dest_path = f"./speaker_voice/{sid}{ext}"
                shutil.copy(audio_filepath, dest_path)
                updated_speaker_voice[sid]["reference_audio"] = dest_path
            except Exception as e:
                print(f"⚠️ Could not copy speaker {sid} audio: {e}")
        else:
            # Keep original speaker if no new upload
            if not updated_speaker_voice[sid].get("reference_audio"):
                updated_speaker_voice[sid]["reference_audio"] = f"./speaker_voice/{sid}.mp3"

    # print("✅ Final speaker voice map:", json.dumps(updated_speaker_voice, indent=2))

    # print(f"passing Data debug:")
    # print(f"media_file: {media_file}")
    # print(f"dubbing_json_state: {dubbing_json_state}")
    # print(f"updated_speaker_voice: {updated_speaker_voice}")
    # print(f"language_name: {language_name}")
    # print(f"exaggeration_input: {exaggeration}")
    # print(f"temperature_input: {temp}")
    # print(f"cfgw_input: {cfg_weight}")
    # print(f"want_subtitle: {want_subtitle}")
    dubbed_audio_path, dubbed_audio_file, returned_custom_srt, returned_default_srt, returned_word_srt, returned_shorts_srt = dubbing(
        media_file=media_file,
        dubbing_json=dubbing_json_state,
        speaker_voice=updated_speaker_voice,
        language_name=language_name,
        exaggeration_input=exaggeration,
        temperature_input=temp,
        cfgw_input=cfg_weight,
        want_subtile=want_subtitle
    )
    dubbed_audio_with_music=None
    if recover_audio:
        dubbed_audio_with_music = restore_music(media_file, dubbed_audio_path)
    video_path=None
    if need_video:
      if recover_audio:
        video_path=make_video(media_file,dubbed_audio_with_music,language_name)
      else:
        video_path=make_video(media_file,dubbed_audio_path,language_name)

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
        video_path
    )



def dubbing_ui():
  with gr.Blocks(theme=gr.themes.Soft()) as demo:
      gr.Markdown("# 🎙️ Video Dubbing Pipeline")
      gr.Markdown("Step 1: Provide your media file and settings. Step 2: Extract speakers. Step 3: Start Dubbing!")

      dubbing_json_state = gr.State()
      speaker_voice_state = gr.State()

      with gr.Row():
          with gr.Column(scale=1):
              gr.Markdown("### ⚙️ Inputs & Settings")
              media_file = gr.Textbox(label="Paste Media File Path",placeholder="/tmp/gradio/.....")
              language_name = gr.Dropdown(list(supported_languages.keys()), label="🌍 Select Language", value="Hindi")
              have_music = gr.Checkbox(value=False, label="Clean speaker voice from media file?")
              want_subtitle = gr.Checkbox(value=True, label="Generate Subtitles for the dubbed audio?")
              llm_result = gr.Textbox(label="Paste LLM Translation", max_lines=10)
              generate_speaker_btn = gr.Button("🚀 Step 1: Extract Speakers & Prepare", variant="primary")

              with gr.Accordion("Advanced TTS Options", open=False):
                  exaggeration = gr.Slider(0.25, 2, step=.05, label="Exaggeration", value=.5)
                  cfg_weight = gr.Slider(0.2, 1, step=.05, label="CFG/Pace", value=0.5)
                  temp = gr.Slider(0.05, 5, step=.05, label="Temperature", value=.8)
              with gr.Accordion("Video Maker", open=True):
                  recover_audio=gr.Checkbox(value=True, label="🎧 Restore background music and ambience ?")
                  need_video=gr.Checkbox(value=True, label="🎬 Make Video ?")

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



      generate_speaker_btn.click(
          fn=extract_speakers_ui,
          inputs=[media_file, have_music, llm_result],
          outputs=[dubbing_json_state, speaker_voice_state, speaker_summary, *speaker_audios]
      )

      dubbing_btn.click(
          fn=start_dubbing_ui,
          inputs=[
              media_file, language_name, have_music, want_subtitle, llm_result,
              exaggeration, cfg_weight, temp,need_video,recover_audio,
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
              video_path
          ]
      )
  return demo      
# demo=dubbing_ui()
# demo.launch(share=True, debug=True)
# from dubbing_webui import dubbing_ui
