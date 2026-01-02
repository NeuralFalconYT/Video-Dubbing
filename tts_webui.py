#@title  /content/Video-Dubbing/tts_webui.py

# %%writefile /content/Video-Dubbing/tts_webui.py
from tts import clone_voice_streaming,supported_languages
from STT.subtitle import subtitle_maker
from turbo_tts import unload_turbo_model

def tts_only(
              text,
              audio_prompt_path_input,
              lang_name="English",
              exaggeration_input=0.5,
              temperature_input=0.8,
              seed_num_input=0,
              cfgw_input=0.5,
              remove_silence=False,
              subtitle=False,
              stereo=False,
              low_gpu=True
          ):
  if low_gpu:
    unload_turbo_model()
  audio_path=clone_voice_streaming(
      text,
      audio_prompt_path_input,
      lang_name,
      exaggeration_input,
      temperature_input,
      seed_num_input,
      cfgw_input,
      stereo,
      remove_silence,
  )
  whisper_default_srt, multiline_srt, word_srt, shorts_srt=None,None,None,None
  if subtitle and audio_path:
    source_lang, target_lang=lang_name,lang_name
    whisper_default_srt, translated_srt_path, multiline_srt, word_srt, shorts_srt, txt_path,sentence_json,word_json, transcript= subtitle_maker(
    audio_path, source_lang, target_lang)
  return audio_path,audio_path, whisper_default_srt, multiline_srt, word_srt, shorts_srt



LANGUAGE_CONFIG = {
    "ar": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/ar_f/ar_prompts2.flac",
        "text": "في الشهر الماضي، وصلنا إلى معلم جديد بمليارين من المشاهدات على قناتنا على يوتيوب."
    },
    "da": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/da_m1.flac",
        "text": "Sidste måned nåede vi en ny milepæl med to milliarder visninger på vores YouTube-kanal."
    },
    "de": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/de_f1.flac",
        "text": "Letzten Monat haben wir einen neuen Meilenstein erreicht: zwei Milliarden Aufrufe auf unserem YouTube-Kanal."
    },
    "el": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/el_m.flac",
        "text": "Τον περασμένο μήνα, φτάσαμε σε ένα νέο ορόσημο με δύο δισεκατομμύρια προβολές στο κανάλι μας στο YouTube."
    },
    "en": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "text": "Last month, we reached a new milestone with two billion views on our YouTube channel."
    },
    "es": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/es_f1.flac",
        "text": "El mes pasado alcanzamos un nuevo hito: dos mil millones de visualizaciones en nuestro canal de YouTube."
    },
    "fi": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/fi_m.flac",
        "text": "Viime kuussa saavutimme uuden virstanpylvään kahden miljardin katselukerran kanssa YouTube-kanavallamme."
    },
    "fr": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/fr_f1.flac",
        "text": "Le mois dernier, nous avons atteint un nouveau jalon avec deux milliards de vues sur notre chaîne YouTube."
    },
    "he": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/he_m1.flac",
        "text": "בחודש שעבר הגענו לאבן דרך חדשה עם שני מיליארד צפיות בערוץ היוטיוב שלנו."
    },
    "hi": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/hi_f1.flac",
        "text": "पिछले महीने हमने एक नया मील का पत्थर छुआ: हमारे YouTube चैनल पर दो अरब व्यूज़।"
    },
    "it": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/it_m1.flac",
        "text": "Il mese scorso abbiamo raggiunto un nuovo traguardo: due miliardi di visualizzazioni sul nostro canale YouTube."
    },
    "ja": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/ja/ja_prompts1.flac",
        "text": "先月、私たちのYouTubeチャンネルで二十億回の再生回数という新たなマイルストーンに到達しました。"
    },
    "ko": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/ko_f.flac",
        "text": "지난달 우리는 유튜브 채널에서 이십억 조회수라는 새로운 이정표에 도달했습니다."
    },
    "ms": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/ms_f.flac",
        "text": "Bulan lepas, kami mencapai pencapaian baru dengan dua bilion tontonan di saluran YouTube kami."
    },
    "nl": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/nl_m.flac",
        "text": "Vorige maand bereikten we een nieuwe mijlpaal met twee miljard weergaven op ons YouTube-kanaal."
    },
    "no": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/no_f1.flac",
        "text": "Forrige måned nådde vi en ny milepæl med to milliarder visninger på YouTube-kanalen vår."
    },
    "pl": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/pl_m.flac",
        "text": "W zeszłym miesiącu osiągnęliśmy nowy kamień milowy z dwoma miliardami wyświetleń na naszym kanale YouTube."
    },
    "pt": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/pt_m1.flac",
        "text": "No mês passado, alcançámos um novo marco: dois mil milhões de visualizações no nosso canal do YouTube."
    },
    "ru": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/ru_m.flac",
        "text": "В прошлом месяце мы достигли нового рубежа: два миллиарда просмотров на нашем YouTube-канале."
    },
    "sv": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/sv_f.flac",
        "text": "Förra månaden nådde vi en ny milstolpe med två miljarder visningar på vår YouTube-kanal."
    },
    "sw": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/sw_m.flac",
        "text": "Mwezi uliopita, tulifika hatua mpya ya maoni ya bilioni mbili kweny kituo chetu cha YouTube."
    },
    "tr": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/tr_m.flac",
        "text": "Geçen ay YouTube kanalımızda iki milyar görüntüleme ile yeni bir dönüm noktasına ulaştık."
    },
    "zh": {
        "audio": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/zh_f2.flac",
        "text": "上个月，我们达到了一个新的里程碑. 我们的YouTube频道观看次数达到了二十亿次，这绝对令人难以置信。"
    },
}
def default_audio_for_ui(lang_name):
  lang_code=supported_languages[lang_name]
  return LANGUAGE_CONFIG[lang_code]['audio']


def default_text_for_ui(lang_name):
  lang_code=supported_languages[lang_name]
  return LANGUAGE_CONFIG.get(lang_code, {}).get("text", "")

def resolve_audio_prompt(language_name: str, provided_path: str | None) -> str | None:
    """
    Decide which audio prompt to use:
    - If user provided a path (upload/mic/url), use it.
    - Else, fall back to language-specific default (if any).
    """
    language_id=supported_languages[language_name]
    if provided_path and str(provided_path).strip():
        return provided_path
    return LANGUAGE_CONFIG.get(language_id, {}).get("audio")
import gradio as gr
def tts_ui():
  custom_css = """.gradio-container { font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; }"""
  with gr.Blocks(theme=gr.themes.Soft(),css=custom_css) as demo:
      gr.HTML("""
        <div style="text-align: center; margin: 20px auto; max-width: 800px;">
            <h1 style="font-size: 2.5em; margin-bottom: 5px;">🎙️ Chatterbox Multilingual </h1>
        </div>""")
      with gr.Row():
          with gr.Column():
              initial_lang = "English"
              text = gr.Textbox(
                  value=default_text_for_ui(initial_lang),
                  label="Text to synthesize (No Limit)",
                  max_lines=5
              )

              language_id = gr.Dropdown(
                  choices=list(supported_languages.keys()),
                  value=initial_lang,
                  label="Language",
                  info="Select the language for text-to-speech synthesis"
              )

              ref_wav = gr.Audio(
                  sources=["upload", "microphone"],
                  type="filepath",
                  label="Reference Audio File (Optional)",
                  value=default_audio_for_ui(initial_lang)
              )
              run_btn = gr.Button("Generate", variant="primary")
              with gr.Row():
                Remove_Silence_button = gr.Checkbox(label="Remove Silence", value=False)
                need_subtitle = gr.Checkbox(label="Want Subtitle ? ", value=False)

              with gr.Accordion("More options", open=False):
                gr.Markdown(
                    "💡 **Note**: Ensure that the reference clip matches the specified language tag. Otherwise, language transfer outputs may inherit the accent of the reference clip's language. To mitigate this, set the CFG weight to 0.",
                    elem_classes=["audio-note"]
                )

                exaggeration = gr.Slider(
                    0.25, 2, step=.05, label="Exaggeration (Neutral = 0.5, extreme values can be unstable)", value=.5
                )
                cfg_weight = gr.Slider(
                    0.2, 1, step=.05, label="CFG/Pace", value=0.5
                )


                seed_num = gr.Number(value=0, label="Random seed (0 for random)")
                temp = gr.Slider(0.05, 5, step=.05, label="Temperature", value=.8)


          with gr.Column():
              audio_output = gr.Audio(label="Play Audio")
              audio_file = gr.File(label="Download Audio")
              with gr.Accordion("Subtitles", open=False):
                whisper_default_subtitle=gr.File(label="Whisper Default Subtitle")
                multiline_subtitle=gr.File(label="Multiline Subtitles For Horizontal Video")
                word_subtitle=gr.File(label="Word Level Subtitle")
                shorts_subtitle=gr.File(label="Subtitle For Verticale Video")
          def on_language_change(lang, current_ref, current_text):
              return default_audio_for_ui(lang), default_text_for_ui(lang)

          language_id.change(
              fn=on_language_change,
              inputs=[language_id, ref_wav, text],
              outputs=[ref_wav, text],
              show_progress=False
          )

      run_btn.click(
          fn=tts_only,
          inputs=[
              text,
              ref_wav,
              language_id,
              exaggeration,
              temp,
              seed_num,
              cfg_weight,
              Remove_Silence_button,
              need_subtitle,

          ],
          outputs=[audio_output,
                   audio_file,
                   whisper_default_subtitle,
                   multiline_subtitle,
                   word_subtitle,
                   shorts_subtitle
                   ],
      )
  return demo
# demo=tts_ui()
# demo.launch(share=True,debug=True)

## How to use 
# from tts_webui import tts_ui
# demo=tts_ui()
# demo.launch(share=True,debug=True)
