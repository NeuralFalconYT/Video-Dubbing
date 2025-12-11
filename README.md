# Video-Dubbing (Support Multi Speaker)
**Run on Colab :**  

<!--[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NeuralFalconYT/Video-Dubbing/blob/main/colab.ipynb)-->

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NeuralFalconYT/Video-Dubbing/blob/main/Run_On_Colab.ipynb)
<p align="center">
  <a href="https://ko-fi.com/neuralfalcon">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" />
  </a>
</p>


### 1. Normal TTS with Subtitle
![1](https://github.com/user-attachments/assets/64b33aa9-67a6-4c20-8abb-9125699004bb)
### 2. Extract timestamps from audio or video with multi-speaker support and use Google AI Studio for translation and transcription into different languages.

![2](https://github.com/user-attachments/assets/ca41d03c-695c-4ad1-8035-edbcae127335)
### 3. Paste the prompt to https://aistudio.google.com/prompts/new_chat and use models/gemini-2.5-pro

![3](https://github.com/user-attachments/assets/42990786-2114-41f5-8891-584fa338ae6e)

### 4. Video Dubbing

![3](https://github.com/user-attachments/assets/0fcf7b60-2af2-48c3-a173-404b4c127678)




## Problem
I’m struggling to design an effective video dubbing logic.
The current implementation in ```audio_sync_pipeline.py``` needs a better approach for **video synchronization**  ensuring the dubbed voice matches the **original speech speed, rhythm, and natural flow**.
The goal is to achieve **smooth, natural timing** (speed up or slow down as needed) for perfect lip-sync and scene alignment.
There is a possible solution: when a tts audio is too long, we can use AI to shorten the dubbing sentence before generating the TTS voice clone again. However, this requires a local LLM or an LLM API, which means needing either a good GPU or a paid subscription. Both cost money, so it’s not feasible.


##  🔧 Recipe 

### **1. Whisper (Transcription)**

Fast, accurate speech to text using Faster-Whisper
🔗 [https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2)

### **2. Pyannote (Speaker Diarization)**

Identify multiple speakers in audio
🔗 [https://github.com/pyannote/pyannote-audio](https://github.com/pyannote/pyannote-audio)

### **3. Google AI Studio – Gemini 3 Pro Preview(Translation)**
Language translation
🔗 [https://aistudio.google.com/](https://aistudio.google.com/)

### **4. Chatterbox (Multilingual TTS + Voice Cloning)**
Generate cloned voices and multilingual audio
🔗 [https://github.com/resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)

### **5. FFmpeg (Audio/Video Processing)**
Trimming, mixing, converting, merging streams

### **6. Python 3.11 (Logic / Processing)**

### 7. ChatGPT (Code Assistance)



## A Basic Overview of How It Works:

<img width="1920" height="1080" alt="workflow" src="https://github.com/user-attachments/assets/fda19f82-d985-4178-9ee5-bec943171f8e" />


# 📌 Acknowledgments
### whisper-diarization-advanced:
The transcription with speaker diarization in this project is adapted from [whisper-diarization-advanced](https://github.com/rafaelgalle/whisper-diarization-advanced) by **[@rafaelgalle](https://github.com/rafaelgalle)**.
This forms the foundation for extracting speaker-labeled transcripts used in the video dubbing pipeline.

### Chatterbox:
This project uses the **Chatterbox** text-to-speech and voice cloning system, developed by [Resemble AI](https://github.com/resemble-ai).  

Original repository: [https://github.com/resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)

We integrate Chatterbox's multilingual TTS and voice cloning capabilities in this video dubbing project.  
All credit for the TTS model architecture, voice cloning algorithms, and base implementation goes to the Chatterbox team.







### ⚠️ Disclaimer

This project, **Video-Dubbing**, uses AI based voice cloning and dubbing technologies.

* Do **not** use this software or any derived models to **impersonate individuals**, **create misleading content**, or **violate privacy, copyright, or consent laws**.
* The developers **do not endorse or support** any unethical, illegal, or harmful use of AI generated voices.
* All prompts, models, and outputs should be used **responsibly** and in compliance with applicable laws and platform policies.
* Voices or likenesses of real individuals should only be used **with explicit permission**.
* The developers of this project are **not responsible for how users apply or misuse** this software. Users are fully accountable for their own actions.




