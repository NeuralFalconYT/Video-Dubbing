def get_edge_tts_voices(speaker_voice, language="English"):
    edge_voice_list = {
        'Afrikaans': {'female': ['af-ZA-AdriNeural'], 'male': ['af-ZA-WillemNeural']},
        'Albanian': {'female': ['sq-AL-AnilaNeural'], 'male': ['sq-AL-IlirNeural']},
        'Amharic': {'female': ['am-ET-MekdesNeural'], 'male': ['am-ET-AmehaNeural']},
        'Arabic': {
            'female': ['ar-AE-FatimaNeural', 'ar-SA-ZariyahNeural', 'ar-EG-SalmaNeural'], 
            'male': ['ar-AE-HamdanNeural', 'ar-SA-HamedNeural', 'ar-EG-ShakirNeural']
        },
        'Azerbaijani': {'female': ['az-AZ-BanuNeural'], 'male': ['az-AZ-BabekNeural']},
        'Bengali': {
            'female': ['bn-BD-NabanitaNeural', 'bn-IN-TanishaaNeural'], 
            'male': ['bn-BD-PradeepNeural', 'bn-IN-BashkarNeural']
        },
        'Bosnian': {'female': ['bs-BA-VesnaNeural'], 'male': ['bs-BA-GoranNeural']},
        'Bulgarian': {'female': ['bg-BG-KalinaNeural'], 'male': ['bg-BG-BorislavNeural']},
        'Burmese': {'female': ['my-MM-NilarNeural'], 'male': ['my-MM-ThihaNeural']},
        'Catalan': {'female': ['ca-ES-JoanaNeural'], 'male': ['ca-ES-EnricNeural']},
        'Chinese': {
            'female': ['zh-CN-XiaoxiaoNeural', 'zh-CN-XiaoyiNeural'], 
            'male': ['zh-CN-YunjianNeural', 'zh-CN-YunxiNeural', 'zh-CN-YunyangNeural']
        },
        'Croatian': {'female': ['hr-HR-GabrijelaNeural'], 'male': ['hr-HR-SreckoNeural']},
        'Czech': {'female': ['cs-CZ-VlastaNeural'], 'male': ['cs-CZ-AntoninNeural']},
        'Danish': {'female': ['da-DK-ChristelNeural'], 'male': ['da-DK-JeppeNeural']},
        'Dutch': {
            'female': ['nl-BE-DenaNeural', 'nl-NL-ColetteNeural', 'nl-NL-FennaNeural'], 
            'male': ['nl-BE-ArnaudNeural', 'nl-NL-MaartenNeural']
        },
        'English': {
            'female': ['en-US-AvaMultilingualNeural', 'en-US-AriaNeural', 'en-US-JennyNeural', 'en-GB-LibbyNeural', 'en-GB-SoniaNeural'], 
            'male': ['en-US-BrianMultilingualNeural', 'en-US-ChristopherNeural', 'en-US-GuyNeural', 'en-GB-RyanNeural', 'en-GB-ThomasNeural']
        },
        'Estonian': {'female': ['et-EE-AnuNeural'], 'male': ['et-EE-KertNeural']},
        'Faroese': {'female': [], 'male': []},
        'Finnish': {'female': ['fi-FI-NooraNeural'], 'male': ['fi-FI-HarriNeural']},
        'French': {
            'female': ['fr-BE-CharlineNeural', 'fr-FR-DeniseNeural', 'fr-FR-EloiseNeural'], 
            'male': ['fr-BE-GerardNeural', 'fr-FR-HenriNeural']
        },
        'Galician': {'female': ['gl-ES-SabelaNeural'], 'male': ['gl-ES-RoiNeural']},
        'Georgian': {'female': ['ka-GE-EkaNeural'], 'male': ['ka-GE-GiorgiNeural']},
        'German': {
            'female': ['de-AT-IngridNeural', 'de-DE-AmalaNeural', 'de-DE-KatjaNeural'], 
            'male': ['de-AT-JonasNeural', 'de-DE-ConradNeural', 'de-DE-KillianNeural']
        },
        'Greek': {'female': ['el-GR-AthinaNeural'], 'male': ['el-GR-NestorasNeural']},
        'Gujarati': {'female': ['gu-IN-DhwaniNeural'], 'male': ['gu-IN-NiranjanNeural']},
        'Hebrew': {'female': ['he-IL-HilaNeural'], 'male': ['he-IL-AvriNeural']},
        'Hindi': {'female': ['hi-IN-SwaraNeural'], 'male': ['hi-IN-MadhurNeural']},
        'Hungarian': {'female': ['hu-HU-NoemiNeural'], 'male': ['hu-HU-TamasNeural']},
        'Icelandic': {'female': ['is-IS-GudrunNeural'], 'male': ['is-IS-GunnarNeural']},
        'Indonesian': {'female': ['id-ID-GadisNeural'], 'male': ['id-ID-ArdiNeural']},
        'Irish': {'female': ['ga-IE-OrlaNeural'], 'male': ['ga-IE-ColmNeural']},
        'Italian': {'female': ['it-IT-ElsaNeural', 'it-IT-IsabellaNeural'], 'male': ['it-IT-DiegoNeural']},
        'Japanese': {'female': ['ja-JP-NanamiNeural'], 'male': ['ja-JP-KeitaNeural']},
        'Javanese': {'female': ['jv-ID-SitiNeural'], 'male': ['jv-ID-DimasNeural']},
        'Kannada': {'female': ['kn-IN-SapnaNeural'], 'male': ['kn-IN-GaganNeural']},
        'Kazakh': {'female': ['kk-KZ-AigulNeural'], 'male': ['kk-KZ-DauletNeural']},
        'Khmer': {'female': ['km-KH-SreymomNeural'], 'male': ['km-KH-PisethNeural']},
        'Korean': {'female': ['ko-KR-SunHiNeural'], 'male': ['ko-KR-HyunsuNeural', 'ko-KR-InJoonNeural']},
        'Lao': {'female': ['lo-LA-KeomanyNeural'], 'male': ['lo-LA-ChanthavongNeural']},
        'Latvian': {'female': ['lv-LV-EveritaNeural'], 'male': ['lv-LV-NilsNeural']},
        'Lithuanian': {'female': ['lt-LT-OnaNeural'], 'male': ['lt-LT-LeonasNeural']},
        'Macedonian': {'female': ['mk-MK-MarijaNeural'], 'male': ['mk-MK-AleksandarNeural']},
        'Malay': {'female': ['ms-MY-YasminNeural'], 'male': ['ms-MY-OsmanNeural']},
        'Malayalam': {'female': ['ml-IN-SobhanaNeural'], 'male': ['ml-IN-MidhunNeural']},
        'Maltese': {'female': ['mt-MT-GraceNeural'], 'male': ['mt-MT-JosephNeural']},
        'Marathi': {'female': ['mr-IN-AarohiNeural'], 'male': ['mr-IN-ManoharNeural']},
        'Mongolian': {'female': ['mn-MN-YesuiNeural'], 'male': ['mn-MN-BataaNeural']},
        'Nepali': {'female': ['ne-NP-HemkalaNeural'], 'male': ['ne-NP-SagarNeural']},
        'Norwegian': {'female': ['nb-NO-PernilleNeural'], 'male': ['nb-NO-FinnNeural']},
        'Norwegian Bokmål': {'female': ['nb-NO-PernilleNeural'], 'male': ['nb-NO-FinnNeural']},
        'Norwegian Nynorsk': {'female': [], 'male': []},
        'Pashto': {'female': ['ps-AF-LatifaNeural'], 'male': ['ps-AF-GulNawazNeural']},
        'Persian': {'female': ['fa-IR-DilaraNeural'], 'male': ['fa-IR-FaridNeural']},
        'Polish': {'female': ['pl-PL-ZofiaNeural'], 'male': ['pl-PL-MarekNeural']},
        'Portuguese': {
            'female': ['pt-BR-FranciscaNeural', 'pt-PT-RaquelNeural'], 
            'male': ['pt-BR-AntonioNeural', 'pt-PT-DuarteNeural']
        },
        'Romanian': {'female': ['ro-RO-AlinaNeural'], 'male': ['ro-RO-EmilNeural']},
        'Russian': {'female': ['ru-RU-SvetlanaNeural'], 'male': ['ru-RU-DmitryNeural']},
        'Serbian': {'female': ['sr-RS-SophieNeural'], 'male': ['sr-RS-NicholasNeural']},
        'Sinhala': {'female': ['si-LK-ThiliniNeural'], 'male': ['si-LK-SameeraNeural']},
        'Slovak': {'female': ['sk-SK-ViktoriaNeural'], 'male': ['sk-SK-LukasNeural']},
        'Slovenian': {'female': ['sl-SI-PetraNeural'], 'male': ['sl-SI-RokNeural']},
        'Somali': {'female': ['so-SO-UbaxNeural'], 'male': ['so-SO-MuuseNeural']},
        'Spanish': {
            'female': ['es-AR-ElenaNeural', 'es-ES-ElviraNeural', 'es-MX-DaliaNeural'], 
            'male': ['es-AR-TomasNeural', 'es-ES-AlvaroNeural', 'es-MX-JorgeNeural']
        },
        'Sundanese': {'female': ['su-ID-TutiNeural'], 'male': ['su-ID-JajangNeural']},
        'Swahili': {'female': ['sw-KE-ZuriNeural', 'sw-TZ-RehemaNeural'], 'male': ['sw-KE-RafikiNeural', 'sw-TZ-DaudiNeural']},
        'Swedish': {'female': ['sv-SE-SofieNeural'], 'male': ['sv-SE-MattiasNeural']},
        'Tamil': {'female': ['ta-IN-PallaviNeural'], 'male': ['ta-IN-ValluvarNeural']},
        'Telugu': {'female': ['te-IN-ShrutiNeural'], 'male': ['te-IN-MohanNeural']},
        'Thai': {'female': ['th-TH-PremwadeeNeural'], 'male': ['th-TH-NiwatNeural']},
        'Turkish': {'female': ['tr-TR-EmelNeural'], 'male': ['tr-TR-AhmetNeural']},
        'Ukrainian': {'female': ['uk-UA-PolinaNeural'], 'male': ['uk-UA-OstapNeural']},
        'Urdu': {
            'female': ['ur-IN-GulNeural', 'ur-PK-UzmaNeural'], 
            'male': ['ur-IN-SalmanNeural', 'ur-PK-AsadNeural']
        },
        'Uzbek': {'female': ['uz-UZ-MadinaNeural'], 'male': ['uz-UZ-SardorNeural']},
        'Vietnamese': {'female': ['vi-VN-HoaiMyNeural'], 'male': ['vi-VN-NamMinhNeural']},
        'Welsh': {'female': ['cy-GB-NiaNeural'], 'male': ['cy-GB-AledNeural']},
        'Zulu': {'female': ['zu-ZA-ThandoNeural'], 'male': ['zu-ZA-ThembaNeural']}
    }

    # FALLBACK: If language is not found, default to English
    if language not in edge_voice_list:
        print(f"Warning: Edge TTS language '{language}' not found. Defaulting to English.")
        language = "English"

    female_list = edge_voice_list[language]["female"]
    male_list = edge_voice_list[language]["male"]

    # FALLBACK: If language exists but list is empty (e.g. Faroese), fallback to English lists
    if not female_list:
        female_list = edge_voice_list["English"]["female"]
    if not male_list:
        male_list = edge_voice_list["English"]["male"]

    female_idx = 0
    male_idx = 0

    for spk_id, meta in speaker_voice.items():
        gender = meta.get("gender", "").lower()

        # FALLBACK: If gender is unknown/missing, default to female
        if gender not in ["female", "male"]:
            print(f"Warning: Unknown gender '{gender}' for speaker {spk_id}. Defaulting to female.")
            gender = "female"

        if gender == "female":
            voice = female_list[female_idx % len(female_list)]
            female_idx += 1
        elif gender == "male":
            voice = male_list[male_idx % len(male_list)]
            male_idx += 1

        speaker_voice[spk_id]['voice_name'] = voice

    return speaker_voice



def get_kokoro_tts_voices(speaker_voice, language="English"):
    kokoro_voice_list = {
        "English": {
            "female": [
                "af_heart", "af_bella", "af_nicole", "af_aoede", "af_alloy",
                "af_kore", "af_sarah", "af_nova", "af_sky", "af_jessica", "af_river"
            ],
            "male": [
                "am_fenrir", "am_michael", "am_puck", "am_echo", "am_eric",
                "am_liam", "am_onyx", "am_adam", "am_santa"
            ]
        },
        "Spanish": {
            "female": ["ef_dora"],
            "male": ["em_alex", "em_santa"]
        },
        "French": {
            "female": ["ff_siwis"],
            "male": ['ff_siwis']
        },
        "Hindi": {
            "female": ["hf_alpha", "hf_beta"],
            "male": ["hm_omega", "hm_psi"]
        },
        "Italian": {
            "female": ["if_sara"],
            "male": ["im_nicola"]
        },
        "Japanese": {
            "female": ["jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro"],
            "male": ["jm_kumo"]
        },
        "Portuguese": {
            "female": ["pf_dora"],
            "male": ["pm_alex", "pm_santa"]
        },
        "Chinese": {
            "female": ["zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi"],
            "male": ["zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"]
        }
    }

    # FALLBACK: If language is not found, default to English
    if language not in kokoro_voice_list:
        print(f"Warning: Kokoro TTS language '{language}' not found. Defaulting to English.")
        language = "English"

    female_list = kokoro_voice_list[language]["female"]
    male_list = kokoro_voice_list[language]["male"]

    # FALLBACK: Fallback to English lists if empty
    if not female_list:
        female_list = kokoro_voice_list["English"]["female"]
    if not male_list:
        male_list = kokoro_voice_list["English"]["male"]

    female_idx = 0
    male_idx = 0

    for spk_id, meta in speaker_voice.items():
        gender = meta.get("gender", "").lower()

        # FALLBACK: If gender is unknown/missing, default to female
        if gender not in ["female", "male"]:
            print(f"Warning: Unknown gender '{gender}' for speaker {spk_id}. Defaulting to female.")
            gender = "female"

        if gender == "female":
            voice = female_list[female_idx % len(female_list)]
            female_idx += 1
        elif gender == "male":
            voice = male_list[male_idx % len(male_list)]
            male_idx += 1

        speaker_voice[spk_id]['voice_name'] = voice
        
    return speaker_voice


def get_voice_name(speaker_voice, language="English", voice_model="Edge TTS"):
    if voice_model == "Kokoro":
        speaker_voice = get_kokoro_tts_voices(speaker_voice, language)
    elif voice_model == "Edge TTS":
        speaker_voice = get_edge_tts_voices(speaker_voice, language)
    return speaker_voice
# from find_voice import get_voice_name
# speaker_voice = {
#     0: {'reference_audio': './speaker_voice/0.mp3', 'fixed_seed': 44913, 'avg_talk_speed': 1.31, 'gender': 'female'},
#     1: {'reference_audio': './speaker_voice/1.mp3', 'fixed_seed': 44913, 'avg_talk_speed': 1.31, 'gender': 'male'},
#     2: {'reference_audio': './speaker_voice/2.mp3', 'fixed_seed': 44913, 'avg_talk_speed': 1.31, 'gender': 'male'}
# }
# get_voice_name(speaker_voice, language="English",voice_model = "Kokoro")
