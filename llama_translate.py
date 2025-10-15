import os
import requests
import urllib.request
import urllib.error
from tqdm.auto import tqdm
def download_file(url: str, download_file_path: str, redownload: bool = False) -> bool:
    """Download a single file with urllib + tqdm progress bar."""
    base_path = os.path.dirname(download_file_path)
    os.makedirs(base_path, exist_ok=True)

    # Skip if file already exists
    if os.path.exists(download_file_path):
        if redownload:
            os.remove(download_file_path)
            tqdm.write(f"♻️ Redownloading: {os.path.basename(download_file_path)}")
        elif os.path.getsize(download_file_path) > 0:
            tqdm.write(f"✔️ Skipped (already exists): {os.path.basename(download_file_path)}")
            return True

    # Try fetching metadata
    try:
        request = urllib.request.urlopen(url)
        total = int(request.headers.get("Content-Length", 0))
    except urllib.error.URLError as e:
        print(f"❌ Error: Unable to open URL: {url}")
        print(f"Reason: {e.reason}")
        return False

    # Download with progress bar
    with tqdm(
        total=total,
        desc=os.path.basename(download_file_path),
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as progress:
        try:
            urllib.request.urlretrieve(
                url,
                download_file_path,
                reporthook=lambda count, block_size, total_size: progress.update(block_size),
            )
        except urllib.error.URLError as e:
            print(f"❌ Error: Failed to download {url}")
            print(f"Reason: {e.reason}")
            return False

    tqdm.write(f"⬇️ Downloaded: {os.path.basename(download_file_path)}")
    return True


def llama_system_prompt(task, source_lang, target_lang):
    system_prompt = ""

    if task == "Translation":
        system_prompt = f"""
            You are a professional {source_lang} to {target_lang} dubbing translator. 
            Translate each line naturally, matching tone, emotion, and style as spoken in movies or web series. 
            Avoid word-for-word translation and output only fluent, authentic {target_lang} dialogue.
            Only return the translated text.
        """

    elif task == "Fix Grammar":
        system_prompt = f"""
        You are an expert in editing and refining {target_lang} text. 
        Fix grammar, spelling, and fluency issues while keeping the original tone and meaning. 
        Make the text sound natural, polished, and professional in {target_lang}. 
        Only return the corrected {target_lang} text.
    """

    elif task == "Rewrite":
        system_prompt = f"""
            You are a skilled {target_lang} content rewriter. 
            Rewrite the given text into clear, expressive, and cinematic {target_lang}, keeping the same meaning but improving tone, flow, and readability. 
            Avoid unnecessary words or repetition. 
            Only return the rewritten {target_lang} text.
        """
    elif task == "Translate & Rewrite":
        system_prompt = f"""
            You are a professional {source_lang} to {target_lang} dubbing translator and creative rewriter. 
            Translate the text into {target_lang} naturally, but also rewrite it to sound fluent, expressive, and cinematic — not a direct word-for-word translation. 
            Preserve all meaning, tone, and emotions from the original, but make it sound as if it were originally written in {target_lang}. 
            Only return the translated and rewritten {target_lang} text.
        """
    return " ".join(system_prompt.split())



def hunyuan_mt_translate(timestamp, source_lang="English", target_lang="Hindi",task="Translation"):
    try:
        from llama_cpp import Llama
        import gc
        import torch

        # Load model (your existing code)
        try:
            llm = Llama.from_pretrained(
                repo_id="mradermacher/Hunyuan-MT-7B-GGUF",
                filename="Hunyuan-MT-7B.Q4_K_S.gguf",
                device="cuda",
                n_ctx=4096,
                n_gpu_layers=-1,
                n_threads=8,
                n_batch=512,
                verbose=False
            )
        except:
            print("Trying to download without hf token")
            download_file_path = "./Hunyuan-MT-7B-GGUF/Hunyuan-MT-7B.Q4_K_M.gguf"
            download_file("https://huggingface.co/mradermacher/Hunyuan-MT-7B-GGUF/resolve/main/Hunyuan-MT-7B.Q4_K_M.gguf",
                          download_file_path, redownload=False)
            llm = Llama(
                model_path=download_file_path,
                device="cuda",
                n_ctx=4096,
                n_gpu_layers=-1,
                n_threads=8,
                n_batch=512,
                verbose=False
            )

        system_prompt=llama_system_prompt(task, source_lang, target_lang)
        def local_llm_translate(text, system_prompt):
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
                output = llm.create_chat_completion(messages=messages)
                res=output["choices"][0]["message"]["content"].strip()
                res=res.strip("**")
                res=res.strip('“”')
                return res
            except:
                return None

        # Process timestamps
        for key, entry in timestamp.items():
            original_text = entry['text']
            tran_text = local_llm_translate(original_text, system_prompt)
            entry['dubbing'] = tran_text if tran_text else original_text

        # Free memory
        del llm
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return timestamp

    except Exception as e:
        print("llama CPP not working")
        print(e)
        return timestamp
# from llama_translate import hunyuan_mt_translate
# hunyuan_mt_translate(timestamp, source_lang="English", target_lang="Hindi")
