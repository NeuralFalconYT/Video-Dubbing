# %cd /content/Video-Dubbing/

# %%writefile /content/Video-Dubbing/whisper_diarization_webui.py
from whisper_diarization import process_media,LANGUAGE_CODE
import gradio as gr
source_lang_list = ['Automatic', "English", "Hindi", "Bengali"]
available_language = LANGUAGE_CODE.keys()
source_lang_list.extend(available_language)

target_lang_list = ["English", "Hindi", "Bengali"]
target_lang_list.extend(available_language)




def update_target_lang(selected_src):
    """Update target language automatically when source changes."""
    if selected_src == "Automatic":
        return "English"
    else:
        return selected_src


def transcript_ui():
    with gr.Blocks() as demo:
        gr.HTML("""
        <div style="text-align: center; margin: 20px auto; max-width: 800px;">
            <h1 style="font-size: 2.5em; margin-bottom: 10px;">🎬 Audio or video Transcription Generator </h1>
            <p style="font-size: 1.2em; color: #555; margin-bottom: 15px;">If you have a large video, upload the audio instead, it's much faster to upload.</p>
        </div>
        """)

        with gr.Row():
            with gr.Column():
                upload_media = gr.File(label="Upload Audio or Video File")
                number_of_speakers = gr.Slider(
                        minimum=0,
                        maximum=10,
                        value=0,
                        step=1,
                        label="Number of Speakers [0 means auto-detect]"
                    )
                remove_music = gr.Checkbox(label="Clean Audio First", value=True)
                small_chunk=gr.Checkbox(label="Make Segments Smaller", value=True)
                input_lang = gr.Dropdown(label="Source Language", choices=source_lang_list, value="English")
                generate_btn = gr.Button("🚀 Generate Transcription", variant="primary")
                with gr.Accordion("⚙️ Translate Parameter", open=True):
                    method = gr.Radio(
                                      choices=["Don't Translate", "Using Google Translator", "Hunyuan-MT-7B Translator","Google AI Studio"],
                                      value="Google AI Studio",
                                      label="Select Translate Method",
                                  )
                    output_lang = gr.Dropdown(label="Translate Into", choices=target_lang_list, value="English")
                    task = gr.Dropdown(
                        ["Translation", "Fix Grammar", "Rewrite","Translate & Rewrite"],
                        label="Select Task",
                        value="Translation",
                    )


            with gr.Column():
              media_file=gr.Textbox(label="Media File Path",show_copy_button=True)
              json_file = gr.File(label="Json Transcription")
              transcript_box = gr.Textbox(label="Transcription", lines=5,max_lines=8,show_copy_button=True)
              llm_translate=gr.Textbox(
                                       label="LLM Translation Prompt Copy & Paste this prompt in https://aistudio.google.com/",
                                       lines=5,show_copy_button=True)

        generate_btn.click(
            fn=process_media,
            inputs=[upload_media,number_of_speakers,remove_music, small_chunk,input_lang, output_lang,method,task],
            outputs=[media_file,json_file, transcript_box,llm_translate]
        )

        input_lang.change(
            fn=update_target_lang,
            inputs=input_lang,
            outputs=output_lang
        )


    return demo

# demo=transcript_ui()
# demo.launch(share=True,debug=True)     

# from whisper_diarization_webui import transcript_ui
# demo=transcript_ui()
# demo.launch(share=True,debug=True)  
