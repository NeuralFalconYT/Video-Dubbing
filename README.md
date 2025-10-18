# Video-Dubbing (Support Multi Speaker)
**Run on Colab:**  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NeuralFalconYT/Video-Dubbing/blob/main/Run_On_Colab.ipynb)

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

## 📌 Acknowledgments
### whisper-diarization-advanced:
The transcription with speaker diarization in this project is adapted from [whisper-diarization-advanced](https://github.com/rafaelgalle/whisper-diarization-advanced) by **[@rafaelgalle](https://github.com/rafaelgalle)**.
This forms the foundation for extracting speaker-labeled transcripts used in the video dubbing pipeline.

### Chatterbox:
This project uses the **Chatterbox** text-to-speech and voice cloning system, developed by [Resemble AI](https://github.com/resemble-ai).  

Original repository: [https://github.com/resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)

We integrate Chatterbox's multilingual TTS and voice cloning capabilities in this video dubbing project.  
All credit for the TTS model architecture, voice cloning algorithms, and base implementation goes to the Chatterbox team.





### ⚠️ Disclaimer

This project, **Video-Dubbing**, uses AI-based voice cloning and dubbing technologies.

* Do **not** use this software or any derived models to **impersonate individuals**, **create misleading content**, or **violate privacy, copyright, or consent laws**.
* The developers **do not endorse or support** any unethical, illegal, or harmful use of AI-generated voices.
* All prompts, models, and outputs should be used **responsibly** and in compliance with applicable laws and platform policies.
* Voices or likenesses of real individuals should only be used **with explicit permission**.

This project builds upon open-source work including [Chatterbox by Resemble AI](https://github.com/resemble-ai/chatterbox), which also cautions against misuse.


