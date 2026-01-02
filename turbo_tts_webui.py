# %cd /content/Video-Dubbing
from turbo_tts import generate
from STT.subtitle import subtitle_maker
import gradio as gr


def gradio_turbo_tts( text,
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
    subtitle=False,
    mp3_bitrate="192k" ):
  audio_path,_=generate(
                text,
                audio_prompt_path,
                temperature,
                seed_num,
                min_p,
                top_p,
                top_k,
                repetition_penalty,
                norm_loudness,
                remove_silence,
                output_format,
                minimum_silence,  
                mp3_bitrate
            )
  whisper_default_srt, multiline_srt, word_srt, shorts_srt=None,None,None,None
  if subtitle and audio_path:
    source_lang, target_lang="English","English"
    whisper_default_srt, translated_srt_path, multiline_srt, word_srt, shorts_srt, txt_path,sentence_json,word_json, transcript= subtitle_maker(
    audio_path, source_lang, target_lang)
  return audio_path,audio_path, whisper_default_srt, multiline_srt, word_srt, shorts_srt

  

def turbo_tts_ui():
  EVENT_TAGS = [
      "[clear throat]", "[sigh]", "[shush]", "[cough]", "[groan]",
      "[sniff]", "[gasp]", "[chuckle]", "[laugh]"
  ]

  CUSTOM_CSS = """
  .tag-container {
      display: flex !important;
      flex-wrap: wrap !important;
      gap: 8px !important;
      margin-top: 5px !important;
      margin-bottom: 10px !important;
      border: none !important;
      background: transparent !important;
  }
  .tag-btn {
      min-width: fit-content !important;
      width: auto !important;
      height: 32px !important;
      font-size: 13px !important;
      background: #eef2ff !important;
      border: 1px solid #c7d2fe !important;
      color: #3730a3 !important;
      border-radius: 6px !important;
      padding: 0 10px !important;
      margin: 0 !important;
      box-shadow: none !important;
  }
  .tag-btn:hover {
      background: #c7d2fe !important;
      transform: translateY(-1px);
  }
  .gradio-container 
  { font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; }
  """

  INSERT_TAG_JS = """
  (tag_val, current_text) => {
      const textarea = document.querySelector('#main_textbox textarea');
      if (!textarea) return current_text + " " + tag_val;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      let prefix = " ";
      let suffix = " ";
      if (start === 0) prefix = "";
      else if (current_text[start - 1] === ' ') prefix = "";
      if (end < current_text.length && current_text[end] === ' ') suffix = "";
      return current_text.slice(0, start) + prefix + tag_val + suffix + current_text.slice(end);
  }
  """


  with gr.Blocks(theme=gr.themes.Soft(), css=CUSTOM_CSS) as demo:
      gr.HTML("""
          <div style="text-align: center; margin: 20px auto; max-width: 800px;">
              <h1 style="font-size: 2.5em; margin-bottom: 5px;">⚡ Chatterbox Turbo</h1>
          </div>""")
      with gr.Row():
          with gr.Column():
              text = gr.Textbox(
                  value="Oh, that's hilarious! [chuckle] Um anyway, we do have a new model in store. It's the SkyNet T-800 series and it's got basically everything. Including AI integration with ChatGPT and all that jazz. Would you like me to get some prices for you?",
                  label="Text to synthesize",
                  max_lines=5,
                  elem_id="main_textbox"
              )

              with gr.Row(elem_classes=["tag-container"]):
                  for tag in EVENT_TAGS:
                      btn = gr.Button(tag, elem_classes=["tag-btn"])
                      btn.click(
                          fn=None,
                          inputs=[btn, text],
                          outputs=text,
                          js=INSERT_TAG_JS
                      )

              ref_wav = gr.Audio(
                  sources=["upload", "microphone"],
                  type="filepath",
                  label="Reference Audio File",
                  value="https://storage.googleapis.com/chatterbox-demo-samples/turbo/2.wav",
              )

              run_btn = gr.Button("Generate ⚡", variant="primary")
              with gr.Accordion("Audio Settings", open=False):
                with gr.Row():
                    output_format = gr.Radio(
                        choices=["wav", "mp3"],
                        value="wav",
                        label="Output Audio Format",
                    )
                    need_subtitle = gr.Checkbox(label="Want Subtitle ? ", value=False)
                with gr.Row():
                    rm_silence = gr.Checkbox(
                        value=False,
                        label="Remove Silence From Audio"
                    )

                    min_silence = gr.Number(
                        label="Keep Silence Upto (seconds)",
                        value=0.05
                    )

              with gr.Accordion("Advanced Options", open=False):
                  seed_num = gr.Number(value=0, label="Random seed (0 for random)")
                  temp = gr.Slider(0.05, 2.0, step=.05, label="Temperature", value=0.8)
                  top_p = gr.Slider(0.00, 1.00, step=0.01, label="Top P", value=0.95)
                  top_k = gr.Slider(0, 1000, step=10, label="Top K", value=1000)
                  repetition_penalty = gr.Slider(1.00, 2.00, step=0.05, label="Repetition Penalty", value=1.2)
                  min_p = gr.Slider(0.00, 1.00, step=0.01, label="Min P (Set to 0 to disable)", value=0.00)
                  norm_loudness = gr.Checkbox(value=True, label="Normalize Loudness (-27 LUFS)")

          with gr.Column():
              audio_output = gr.Audio(label="Output Audio")
              audio_file = gr.File(label="Download Audio")
              with gr.Accordion("Subtitles", open=False):
                whisper_default_subtitle=gr.File(label="Whisper Default Subtitle")
                multiline_subtitle=gr.File(label="Multiline Subtitles For Horizontal Video")
                word_subtitle=gr.File(label="Word Level Subtitle")
                shorts_subtitle=gr.File(label="Subtitle For Verticale Video")
          
      run_btn.click(
          fn=gradio_turbo_tts,
          inputs=[
              text,
              ref_wav,
              temp,
              seed_num,
              min_p,
              top_p,
              top_k,
              repetition_penalty,
              norm_loudness,
              rm_silence,
              output_format,
              min_silence,
              need_subtitle

          ],
          outputs=[audio_output,
                   audio_file,
                   whisper_default_subtitle,
                   multiline_subtitle,
                   word_subtitle,
                   shorts_subtitle
                   ]
      )
  return demo
# if __name__ == "__main__":
#     demo=turbo_tts_ui()
#     demo.queue().launch(
#         share=True,
#         debug=True

#     )


# import click
# @click.command()
# @click.option("--debug", is_flag=True, default=False, help="Enable debug mode.")
# @click.option("--share", is_flag=True, default=False, help="Enable sharing of the interface.")
# def main(debug, share):
#     demo=turbo_tts_ui()
#     demo.queue().launch(debug=debug, share=share)
# if __name__ == "__main__":
#     main()    
