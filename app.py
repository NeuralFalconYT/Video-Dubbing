# https://github.com/NeuralFalconYT
# /content/Video-Dubbing/app.py
import gradio as gr
from tts_webui import tts_ui
from turbo_tts_webui import turbo_tts_ui
from whisper_diarization_webui import transcript_ui
from dubbing_webui import dubbing_ui
from subtitle_romanize_ui import romanize

import logging, warnings
logging.disable(logging.CRITICAL)
warnings.filterwarnings("ignore")




custom_css = """
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


import click
@click.command()
@click.option("--debug", is_flag=True, default=False, help="Enable debug mode.")
@click.option("--share", is_flag=True, default=False, help="Enable sharing of the interface.")
def run_demo(share,debug):
    global custom_css
    demo1=tts_ui()
    demo2=turbo_tts_ui()
    demo3=transcript_ui()
    demo4=dubbing_ui()
    demo5=romanize()
    interface = gr.TabbedInterface([demo1, demo2,demo3,demo4,demo5],["Chatterbox Multilingual TTS","Chatterbox Turbo TTS","Whisper Transcription","Dubbing","Subtitle Romanize"],title="",theme=gr.themes.Soft(),css=custom_css)
    interface.queue(max_size=10).launch(share=share,debug=debug)
if __name__ == "__main__":
    run_demo()
