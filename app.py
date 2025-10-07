from tts_webui import tts_ui
from whisper_diarization_webui import transcript_ui
from dubbing_webui import dubbing_ui



import click
@click.command()
@click.option("--debug", is_flag=True, default=False, help="Enable debug mode.")
@click.option("--share", is_flag=True, default=False, help="Enable sharing of the interface.")
def run_demo(share,debug):
    demo1=tts_ui()
    demo2=transcript_ui()
    demo3=dubbing_ui()
    custom_css = """.gradio-container { font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; }"""
    interface = gr.TabbedInterface([demo1, demo2,demo3],["ChatterBox TTS","Whisper Transcription","Dubbing"],title="",theme=gr.themes.Soft(),css=custom_css)
    interface.queue(max_size=10).launch(share=share,debug=debug)
if __name__ == "__main__":
    run_demo()
