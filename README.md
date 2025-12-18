

# 🎙️ Video-Dubbing (Multi-Speaker AI Dubbing System)

Run complete AI dubbing pipelines with **speaker diarization**, **voice cloning**, **translation**, **rewriting**, **grammar correction**, **translation & rewriting**, **background restoration**, and **automatic subtitles**  with support for **multi-speaker videos** and dubbing in 🌐 **23 languages**. 

---

## 🚀 Run on Google Colab

Run the full pipeline on a **free T4 GPU**:
<!--[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NeuralFalconYT/Video-Dubbing/blob/main/colab.ipynb)-->

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NeuralFalconYT/Video-Dubbing/blob/main/Run_On_Colab.ipynb)

<p align="center">
  <a href="https://ko-fi.com/neuralfalcon">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" />
  </a>
</p>

---

# ✨ Features
## 🌐 Supports 23 languages

## 🎧 Voice & Audio Processing
### **• Normal Voice Cloning with Subtitles**

Clone the speaker’s voice and generate accurate subtitles from the processed audio.

### **• Video Dubbing with Background Music/Noise Restoration**

Dub videos in any supported AI voice while restoring the original **background music** or **ambient noise** for a natural feel.
Subtitles are automatically generated for the dubbed output.


---

## 🌍 How This App Uses Premium LLMs for Translation Without Spending $0 on APIs

* The app generates a **ready-to-use prompt** for translation or rewriting.
* The user simply **copies the prompt** and pastes it into a **free AI platform** (Google AI Studio, ChatGPT, etc.).
* The translated or rewritten text is then **pasted back into the app**.
* This enables the use of **premium LLM quality** without any paid API calls or subscriptions.
* For longer videos, the app also provides **local translation** (Hunyuan-MT-7B-GGUF) or **Google Translate support**, though these options may not match the quality of the latest advanced LLMs.

---

# 📝 Dubbing Modes

This dubbing pipeline supports multiple text-processing modes:

### **1. Translation**

Translate text from one language to another ideal for multilingual dubbing.

### **2. Fix Grammar**

Correct grammar, spelling, and sentence structure without changing the meaning.
Used when the speaker’s grammar is incorrect but the content should remain the same.

### **3. Rewrite**

Rewrite sentences into clean, natural, professionally phrased speech.
Useful when the original audio has broken grammar, slang, or unclear phrasing.

### **4. Translate & Rewrite**

Translate the video **and** produce polished, natural sentences in the target language.
Best for high-quality international dubbing.

---

# 🔧 Technology Stack (Recipe)

### **1. Facebook Demucs — Music/Noise Separation**

Separates vocals from background music or ambient noise.
🔗 [https://github.com/facebookresearch/demucs](https://github.com/facebookresearch/demucs)

### **2. Whisper (Faster-Whisper) — Transcription & Subtitle Generation**

Fast, accurate speech-to-text for large videos.
🔗 [https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2)

### **3. Pyannote — Speaker Diarization**

Detects and identifies multiple speakers.
🔗 [https://github.com/pyannote/pyannote-audio](https://github.com/pyannote/pyannote-audio)

### **4. Google AI Studio (Gemini 3 Pro Preview) (But you can use any AI models) — Translation & Rewriting**
High-quality translation and text rewriting using Gemini models, as they support longer text generation.
🔗 [https://aistudio.google.com/](https://aistudio.google.com/)

### **5. Hunyuan-MT-7B-GGUF — Offline Translation**

Local GPU-friendly multilingual translation model.
🔗 [https://huggingface.co/mradermacher/Hunyuan-MT-7B-GGUF](https://huggingface.co/mradermacher/Hunyuan-MT-7B-GGUF)

### **6. Google Translate (Optional)**

Simple API-based translation.
🔗 [https://pypi.org/project/googletrans/](https://pypi.org/project/googletrans/)

### **7. Chatterbox Multilingual TTS — Voice Cloning**

Generate cloned voices and multilingual synthetic speech.
🔗 [https://github.com/resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)

### **8. FFmpeg — Audio/Video Processing**

Trimming, merging, format conversion, audio mixing.
🔗 [https://www.ffmpeg.org/](https://www.ffmpeg.org/)

### **9. Python 3.11 & Supporting Libraries**

Logic, processing, audio manipulation, ML pipelines.

### **10. Gradio — User Interface**

Builds the interactive web UI for your application.
🔗 [https://www.gradio.app/](https://www.gradio.app/)

### **11. Google Colab (Free T4 GPU)**

Run the full dubbing system on free cloud GPU.

### **12. ChatGPT — Code Assistance & Logic Refinement**

Helpful for debugging, writing utilities, and optimizing logic.

---

# 🧠 Processing Workflow

<img width="1920" height="1080" alt="workflow" src="https://github.com/user-attachments/assets/fda19f82-d985-4178-9ee5-bec943171f8e" />



---

# 🧩 Technical Challenges

### **Problem 1: Imperfect Dubbing Synchronization**

The current dubbing logic in `audio_sync_pipeline.py` achieves roughly **70% accuracy** and struggles to perfectly synchronize the AI-generated voice with the original speech.
Key issues include:

* ✔️ **Incorrect speech speed**
* ✔️ **Mismatch in rhythm and pacing**
* ✔️ **Lack of natural timing variations**

The goal is for the TTS output to **match real human timing**, creating smooth, natural, and believable dubbing.

#### **Potential Solution**

If the generated TTS audio is **too long**, an LLM could be used to **shorten or compress the rewritten sentence** before regenerating speech.
However, this approach has limitations:

* Requires a **local LLM** (needs a strong GPU), **or**
* Requires a **paid API**,
  Both of which may be impractical for many users.
#### ✅ Redubbing support has been added, but the current user interface is still rough. This feature is designed for manual copy-paste LLM prompts (Gemini, ChatGPT, or other LLMs), allowing sentence shortening without relying on paid API calls.
---

### **Problem 2: No Emotion Matching in Dubbing**

The current system does **not analyze or replicate emotional tone** from the original speakers.
This leads to flat or inappropriate emotions in the dubbed audio.

For example:

* If the original speaker sounds **sad**, the dubbed version should also sound sad.
* If the speaker is **excited, angry, or calm**, the dubbing should reflect that emotion.

#### **Why This Happens**

* Chatterbox multilingual TTS **does not support emotional voice generation**.
* The pipeline does **not perform emotion detection** on the input audio segments.

#### **Potential Solution**

* Detect emotions in each audio segment (e.g., *happy, sad, angry, neutral*).
* Replace Chatterbox with a **voice-cloning tts model that supports emotional control**.
* Apply the detected emotion to the cloned voice during TTS generation.

This would produce far more natural and expressive dubbing results.

---




# 🖼️ App Screenshots

### 1. Normal Voice Clone TTS with Subtitles

![1](https://github.com/user-attachments/assets/64b33aa9-67a6-4c20-8abb-9125699004bb)

### 2. Multi-Speaker Timestamp Extraction + Translation

![2](https://github.com/user-attachments/assets/ca41d03c-695c-4ad1-8035-edbcae127335)

### 3. Using Google AI Studio(We can use any LLMS) for Prompt-Based Translation

![3](https://github.com/user-attachments/assets/42990786-2114-41f5-8891-584fa338ae6e)

### 4. Video Dubbing Output

![3](https://github.com/user-attachments/assets/0fcf7b60-2af2-48c3-a173-404b4c127678)

---

# 📌 Acknowledgments

### **Whisper-Diarization-Advanced**

Based on the implementation by **[@rafaelgalle](https://github.com/rafaelgalle)**.
🔗 [https://github.com/rafaelgalle/whisper-diarization-advanced](https://github.com/rafaelgalle/whisper-diarization-advanced)

### **Chatterbox by Resemble AI**

Used for multilingual text-to-speech and voice cloning.
🔗 [https://github.com/resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)

---
Here’s a clean, professional **credit section** acknowledging Chatterbox and emphasizing that your project depends on it:

---

## 🙏 Credits

### **Chatterbox (Resemble AI)**

This project would not be possible without **Chatterbox**, the open-source multilingual TTS and voice cloning system developed by Resemble AI.

Chatterbox provides the core text-to-speech and voice cloning capabilities that make high-quality multilingual dubbing achievable in this project.

🔗 [https://github.com/resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)

---


# ⚠️ Disclaimer

This project uses AI-based voice cloning & dubbing technologies.
Users **must** follow responsible and ethical usage guidelines:

* Do **not** impersonate individuals without permission.
* Do **not** create deceptive or harmful content.
* Respect **privacy**, **copyright**, and **local laws**.
* You are fully responsible for how you use this tool.



