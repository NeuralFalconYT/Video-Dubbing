import gradio as gr

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





def prompt_translation(language):
    """
    Generates a dubbing-friendly translation prompt for an .srt subtitle file.
    Tailored for natural speech and timing accuracy.
    """
    prompt = f"""
-------------- You are a professional subtitle translator for **video dubbing**.
Translate the following `.srt` subtitle file into **{language}** while preserving timing, meaning, and emotional tone.
Output in JSON format exactly like this:
```json
{{
  "subtitle sequence number": {{
    "timestamp": "original timestamp",
    "actual subtitle text": "original English subtitle line",
    "dubbing": "natural, dubbing-friendly {language} translation"
  }}
}}
```
**Guidelines for Translation:**
1. **Understand the full context** before translating — read the entire subtitle file first.
2. Translate into **natural, conversational {language}**, not a direct word-for-word translation.
6. Keep translations **roughly similar in length** to the original so lip movements sync naturally.
"""
    return prompt


def prompt_fix_grammar(language="English"):
    """
    Generates a dubbing-friendly grammar correction prompt for an .srt subtitle file.
    Tailored for natural speech and timing accuracy.
    """
    prompt = f"""
-------------- You are a professional subtitle editor for **video dubbing**.
Fix the grammar, spelling, and awkward phrasing in the following `.srt` subtitle file while preserving timing, meaning, and emotional tone.  
Do NOT translate — keep everything in {language}.
Output in JSON format exactly like this:
```json
{{
"subtitle sequence number": {{
"timestamp": "original timestamp",
"actual subtitle text": "original {language} subtitle line",
"dubbing": "natural, dubbing-friendly corrected {language} line"
}}
}}
```
**Guidelines for Grammar Fixing:**
1.  **Understand the full context** before editing — read the entire subtitle file first.
2.  Correct grammar, spelling, and phrasing errors while keeping the same meaning.
4.  Keep corrections **roughly similar in length** to the original so lip movements sync naturally.
"""
    return prompt


def prompt_srt_to_romanized(language="Hindi"):
  """
  Generates a prompt for converting a .srt subtitle file
  from any language to a Romanized (Latin letters) version,
  preserving timing, meaning, punctuation, and formatting.
  """
  prompt = f"""
-------------- You are a professional subtitle editor tasked with converting subtitles to Romanized text.
Your task is to convert a `.srt` subtitle file from {language} to **Romanized {language}**, 
keeping everything exactly the same except using Latin letters for all words.
**Instructions:**
1. Preserve the original timestamp of each subtitle.
2. Keep the original meaning, punctuation, and formatting intact.
3. Convert **only the original subtitle text** to Roman letters, word by word.
4. Do not add, remove, or change any words.
5. Output in strict JSON format exactly like this:
```json
{{
"subtitle sequence number": {{
"timestamp": "original timestamp",
"original subtitle text": "original {language} subtitle line",
"dubbing": "Romanized, {language} line of original subtitle text"
}}
}}
````
Focus entirely on **accurate Romanization**; do not modify anything else.
"""
  return prompt



import pysrt

def prompt_maker(srt_path, target_language, task="Translation"):
    txt_path = srt_path.replace(".srt", ".txt")
    subs = pysrt.open(srt_path, encoding='utf-8')

    with open(txt_path, 'w', encoding='utf-8') as f:
        for sub in subs:
            f.write(f"{sub.index}\n")
            f.write(f"{sub.start} --> {sub.end}\n")
            f.write(f"{sub.text}\n\n")
        if task == "Translation":
            f.write(prompt_translation(target_language))
        if task=="Romanization":
            f.write(prompt_srt_to_romanized(target_language))
        else:
            f.write(prompt_fix_grammar(target_language))

    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # return both prompt text and original path
    return content, srt_path




import pysrt
import json 
import os 
def json_to_srt(json_script, srt_path):
    """
    Convert dubbing-friendly JSON back into .srt
    Uses original srt_path to name output <name>_dubbing.srt
    """
    os.makedirs("./dubbing_srt", exist_ok=True)

    base_name = os.path.basename(srt_path)
    name_no_ext, _ = os.path.splitext(base_name)
    output_srt_path = os.path.join("./dubbing_srt", f"{name_no_ext}_dubbing.srt")

    # Load JSON
    if isinstance(json_script, str):
        json_object = json.loads(json_script)
    else:
        json_object = json_script

    # Write to file
    with open(output_srt_path, "w", encoding="utf-8") as f:
        for i, (key, value) in enumerate(json_object.items(), start=1):
            f.write(f"{i}\n")
            f.write(f"{value['timestamp']}\n")
            f.write(f"{value['dubbing']}\n\n")

    return output_srt_path



def romanize():
    target_lang_list=LANGUAGE_CODE.keys()
    lang_list=['English','Hindi','Bengali']
    lang_list.extend(target_lang_list)
    with gr.Blocks() as demo:
        gr.Markdown("<center><h1 style='font-size: 32px;'>🎬 Subtitle Romanization Using LLM</h1></center>")

        # hidden state to keep original srt path
        srt_state = gr.State("")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Step 1: Generate Prompt")
                srt_file = gr.File(label="Upload .srt file generated by Whisper", file_types=[".srt"])
                task = gr.Dropdown(
                      ["Translation","Romanization","Fix Grammar [English to English for dubbing]"],
                      label="Select Task",
                      value="Romanization",
                  )
                language = gr.Dropdown(lang_list, label="Select the language you want to translate into", value="Hindi")
                generate_btn = gr.Button("Generate Prompt")
                output_prompt = gr.Textbox(
                    label="Copy & Paste this prompt in  https://aistudio.google.com/",
                    lines=20,
                    show_copy_button=True
                    
                )

            with gr.Column():
                gr.Markdown("### Step 2: Paste JSON & Convert Back to SRT")
                json_input = gr.Textbox(
                    label="Paste JSON script from https://aistudio.google.com/ ",
                    lines=20,
                    placeholder="Paste the JSON output here..."
                )
                convert_btn = gr.Button("Convert JSON → SRT")
                srt_file_out = gr.File(label="Download new .srt")

        # Button actions
        generate_btn.click(
            fn=prompt_maker,
            inputs=[srt_file, language, task],
            outputs=[output_prompt, srt_state],   
        )

        convert_btn.click(
            fn=json_to_srt,
            inputs=[json_input, srt_state],       
            outputs=srt_file_out,
        )

    return demo
(* from subtitle_romanize_ui import romanize *)
