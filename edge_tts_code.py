#@title /content/Video-Dubbing/edge_tts_code.py
# %%writefile /content/Video-Dubbing/edge_tts_code.py
female_voice_list={'Vietnamese': 'vi-VN-HoaiMyNeural',
 'Bengali': 'bn-BD-NabanitaNeural',
 'Thai': 'th-TH-PremwadeeNeural',
 'English': "en-US-AvaMultilingualNeural", #'en-AU-NatashaNeural', #"en-IE-EmilyNeural"
 'Portuguese': 'pt-BR-FranciscaNeural',
 'Arabic': 'ar-AE-FatimaNeural',
 'Turkish': 'tr-TR-EmelNeural',
 'Spanish': 'es-AR-ElenaNeural',
 'Korean': 'ko-KR-SunHiNeural',
 'French': 'fr-BE-CharlineNeural',
 'Indonesian': 'id-ID-GadisNeural',
 'Russian': 'ru-RU-SvetlanaNeural',
 'Hindi': 'hi-IN-SwaraNeural',
 'Japanese': 'ja-JP-NanamiNeural',
 'Afrikaans': 'af-ZA-AdriNeural',
 'Amharic': 'am-ET-MekdesNeural',
 'Azerbaijani': 'az-AZ-BanuNeural',
 'Bulgarian': 'bg-BG-KalinaNeural',
 'Bosnian': 'bs-BA-VesnaNeural',
 'Catalan': 'ca-ES-JoanaNeural',
 'Czech': 'cs-CZ-VlastaNeural',
 'Welsh': 'cy-GB-NiaNeural',
 'Danish': 'da-DK-ChristelNeural',
 'German': 'de-AT-IngridNeural',
 'Greek': 'el-GR-AthinaNeural',
 'Irish': 'ga-IE-OrlaNeural',
 'Galician': 'gl-ES-SabelaNeural',
 'Gujarati': 'gu-IN-DhwaniNeural',
 'Hebrew': 'he-IL-HilaNeural',
 'Croatian': 'hr-HR-GabrijelaNeural',
 'Hungarian': 'hu-HU-NoemiNeural',
 'Icelandic': 'is-IS-GudrunNeural',
 'Italian': 'it-IT-ElsaNeural',
 'Javanese': 'jv-ID-SitiNeural',
 'Georgian': 'ka-GE-EkaNeural',
 'Kazakh': 'kk-KZ-AigulNeural',
 'Khmer': 'km-KH-SreymomNeural',
 'Kannada': 'kn-IN-SapnaNeural',
 'Lao': 'lo-LA-KeomanyNeural',
 'Lithuanian': 'lt-LT-OnaNeural',
 'Latvian': 'lv-LV-EveritaNeural',
 'Macedonian': 'mk-MK-MarijaNeural',
 'Malayalam': 'ml-IN-SobhanaNeural',
 'Mongolian': 'mn-MN-YesuiNeural',
 'Marathi': 'mr-IN-AarohiNeural',
 'Malay': 'ms-MY-YasminNeural',
 'Maltese': 'mt-MT-GraceNeural',
 'Burmese': 'my-MM-NilarNeural',
 'Norwegian Bokmål': 'nb-NO-PernilleNeural',
 'Nepali': 'ne-NP-HemkalaNeural',
 'Dutch': 'nl-BE-DenaNeural',
 'Polish': 'pl-PL-ZofiaNeural',
 'Pashto': 'ps-AF-LatifaNeural',
 'Romanian': 'ro-RO-AlinaNeural',
 'Sinhala': 'si-LK-ThiliniNeural',
 'Slovak': 'sk-SK-ViktoriaNeural',
 'Slovenian': 'sl-SI-PetraNeural',
 'Somali': 'so-SO-UbaxNeural',
 'Albanian': 'sq-AL-AnilaNeural',
 'Serbian': 'sr-RS-SophieNeural',
 'Sundanese': 'su-ID-TutiNeural',
 'Swedish': 'sv-SE-SofieNeural',
 'Swahili': 'sw-KE-ZuriNeural',
 'Tamil': 'ta-IN-PallaviNeural',
 'Telugu': 'te-IN-ShrutiNeural',
 'Chinese': 'zh-CN-XiaoxiaoNeural',
 'Ukrainian': 'uk-UA-PolinaNeural',
 'Urdu': 'ur-IN-GulNeural',
 'Uzbek': 'uz-UZ-MadinaNeural',
 'Zulu': 'zu-ZA-ThandoNeural'}
male_voice_list= {'Vietnamese': 'vi-VN-NamMinhNeural',
 'Bengali': 'bn-BD-PradeepNeural',
 'Thai': 'th-TH-NiwatNeural',
 'English': 'en-US-BrianMultilingualNeural', #"en-US-BrianNeural"
 'Portuguese': 'pt-BR-AntonioNeural',
 'Arabic': 'ar-AE-HamdanNeural',
 'Turkish': 'tr-TR-AhmetNeural',
 'Spanish': 'es-AR-TomasNeural',
 'Korean': 'ko-KR-HyunsuNeural',
 'French': 'fr-BE-GerardNeural',
 'Indonesian': 'id-ID-ArdiNeural',
 'Russian': 'ru-RU-DmitryNeural',
 'Hindi': 'hi-IN-MadhurNeural',
 'Japanese': 'ja-JP-KeitaNeural',
 'Afrikaans': 'af-ZA-WillemNeural',
 'Amharic': 'am-ET-AmehaNeural',
 'Azerbaijani': 'az-AZ-BabekNeural',
 'Bulgarian': 'bg-BG-BorislavNeural',
 'Bosnian': 'bs-BA-GoranNeural',
 'Catalan': 'ca-ES-EnricNeural',
 'Czech': 'cs-CZ-AntoninNeural',
 'Welsh': 'cy-GB-AledNeural',
 'Danish': 'da-DK-JeppeNeural',
 'German': 'de-AT-JonasNeural',
 'Greek': 'el-GR-NestorasNeural',
 'Irish': 'ga-IE-ColmNeural',
 'Galician': 'gl-ES-RoiNeural',
 'Gujarati': 'gu-IN-NiranjanNeural',
 'Hebrew': 'he-IL-AvriNeural',
 'Croatian': 'hr-HR-SreckoNeural',
 'Hungarian': 'hu-HU-TamasNeural',
 'Icelandic': 'is-IS-GunnarNeural',
 'Italian': 'it-IT-DiegoNeural',
 'Javanese': 'jv-ID-DimasNeural',
 'Georgian': 'ka-GE-GiorgiNeural',
 'Kazakh': 'kk-KZ-DauletNeural',
 'Khmer': 'km-KH-PisethNeural',
 'Kannada': 'kn-IN-GaganNeural',
 'Lao': 'lo-LA-ChanthavongNeural',
 'Lithuanian': 'lt-LT-LeonasNeural',
 'Latvian': 'lv-LV-NilsNeural',
 'Macedonian': 'mk-MK-AleksandarNeural',
 'Malayalam': 'ml-IN-MidhunNeural',
 'Mongolian': 'mn-MN-BataaNeural',
 'Marathi': 'mr-IN-ManoharNeural',
 'Malay': 'ms-MY-OsmanNeural',
 'Maltese': 'mt-MT-JosephNeural',
 'Burmese': 'my-MM-ThihaNeural',
 'Norwegian Bokmål': 'nb-NO-FinnNeural',
 'Nepali': 'ne-NP-SagarNeural',
 'Dutch': 'nl-BE-ArnaudNeural',
 'Polish': 'pl-PL-MarekNeural',
 'Pashto': 'ps-AF-GulNawazNeural',
 'Romanian': 'ro-RO-EmilNeural',
 'Sinhala': 'si-LK-SameeraNeural',
 'Slovak': 'sk-SK-LukasNeural',
 'Slovenian': 'sl-SI-RokNeural',
 'Somali': 'so-SO-MuuseNeural',
 'Albanian': 'sq-AL-IlirNeural',
 'Serbian': 'sr-RS-NicholasNeural',
 'Sundanese': 'su-ID-JajangNeural',
 'Swedish': 'sv-SE-MattiasNeural',
 'Swahili': 'sw-KE-RafikiNeural',
 'Tamil': 'ta-IN-ValluvarNeural',
 'Telugu': 'te-IN-MohanNeural',
 'Chinese': 'zh-CN-YunjianNeural',
 'Ukrainian': 'uk-UA-OstapNeural',
 'Urdu': 'ur-IN-SalmanNeural',
 'Uzbek': 'uz-UZ-SardorNeural',
 'Zulu': 'zu-ZA-ThembaNeural'}



import os
import re
import uuid
import subprocess
from pydub import AudioSegment





# ---------- temp filename ----------
def temp_tts_file_name(text, language="en"):
    save_folder = "./edge_tts"
    os.makedirs(save_folder, exist_ok=True)

    text = re.sub(r"[^a-zA-Z\s]", "", text).lower().strip().replace(" ", "_")
    if not text:
        text = "audio"

    truncated = text[:20]
    random_str = uuid.uuid4().hex[:8].upper()

    return f"{save_folder}/{truncated}_{language}_{random_str}"


# ---------- speed formatting ----------
def calculate_rate_string(speed):
    rate = (speed - 1) * 100
    sign = "+" if speed >= 1 else "-"
    return f"{sign}{abs(int(rate))}"


# ---------- main edge tts function ----------
def edge_tts_generate(text, language, voice_name="en-US-AvaMultilingualNeural", speed=1.0):
    """
    Edge TTS CLI wrapper:
    - No async
    - Saves WAV audio
    - Safe for pipelines / Gradio
    """

    # pick voice
    # voice = (
    #     male_voice_list.get(language)
    #     if gender.lower() == "male"
    #     else female_voice_list.get(language)
    # )

    # if not voice:
    #     raise ValueError(f"No voice configured for {language}")
    voice=voice_name
    base_path = temp_tts_file_name(text, language)
    mp3_path = base_path + ".mp3"
    wav_path = base_path + ".wav"

    cmd = [
        "edge-tts",
        f"--rate={calculate_rate_string(speed)}%",
        "--voice", voice,
        "--text", text,
        "--write-media", mp3_path,
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # convert mp3 → wav
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(wav_path, format="wav")

        os.remove(mp3_path)
        return wav_path

    except Exception as e:
        print("⚠️ Edge-TTS failed:", e)
        return None


# ---------- example run ----------
if __name__ == "__main__":
  #  from edge_tts_code import edge_tts_generate
  #  raw_path = edge_tts_generate(
  #       text="Hello",
  #       language="English",
  #       gender="Female",
  #       speed=1.0,
  #   )
    path = edge_tts_generate(
        text="Hello",
        language="English",
        gender="Female",
        speed=1.0,
    )

    print("Saved:", path)
