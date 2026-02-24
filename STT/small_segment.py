import re
from sentencex import segment


def segment_split(
    final_segments,
    language="en",
    max_chars=100,
    minimum_gap=0.05,
    allow_same_start_end_merge=True,
    max_chars_merge=120,
):


    cjk_languages = ("zh", "ja", "ko")
    if language in cjk_languages:
        max_chars = 10
        max_chars_merge = 20

    all_new_segments = []

    for seg in final_segments:
        text = seg.get("text", "").strip()
        words = seg.get("words", [])
        speaker = seg.get("speaker", "SPEAKER_00")

        if not words:
            all_new_segments.append(seg)
            continue

        # --- Step 1: sentencex segmentation
        if language and len(text) > 20:
            try:
                sentences = list(segment(language, text))
            except Exception:
                sentences = [text]
        else:
            sentences = [text]

        # --- Step 2: fallback if single long sentence
        if len(sentences) == 1 and len(sentences[0]) > max_chars:
            all_new_segments.extend(
                _force_split_by_words(seg, language, max_chars, minimum_gap)
            )
            continue

        # --- Step 3: SAFE sentence-word alignment
        sentence_segments = []
        wi = 0

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            sent_words = []
            sent_start, sent_end = None, None

            sent_norm = re.sub(r"\s+", "", sent).lower()
            accumulated = ""

            while wi < len(words):
                w = words[wi]

                clean_word = re.sub(r"\s+", "", w["word"]).lower()
                accumulated += clean_word

                if sent_start is None:
                    sent_start = w["start"]

                sent_end = w["end"]
                sent_words.append(w)
                wi += 1

                if accumulated.startswith(sent_norm) or accumulated == sent_norm:
                    break

            if sent_words:
                sentence_segments.append({
                    "speaker": speaker,
                    "start": sent_start,
                    "end": sent_end,
                    "text": sent,
                    "words": sent_words,
                })

        # --- SAFETY: append leftover words if any
        if wi < len(words):
            remaining_words = words[wi:]
            sentence_segments.append({
                "speaker": speaker,
                "start": remaining_words[0]["start"],
                "end": remaining_words[-1]["end"],
                "text": " ".join(w["word"] for w in remaining_words),
                "words": remaining_words,
            })

        # --- Step 4: length checks
        for s in sentence_segments:
            if len(s["text"]) > max_chars:
                all_new_segments.extend(
                    _force_split_by_words(s, language, max_chars, minimum_gap)
                )
            else:
                s["duration"] = round(s["end"] - s["start"], 3)
                all_new_segments.append(s)

    # --- Step 5: optional merge
    if allow_same_start_end_merge:
        all_new_segments = _merge_same_boundary_segments(
            all_new_segments,
            language,
            max_chars_merge=max_chars_merge,
        )

    return all_new_segments


# ---------- helpers ----------


def _force_split_by_words(seg, language, max_chars=90, minimum_gap=0.05):
    words = seg["words"]
    if not words:
        return [seg]

    new_segments = []
    speaker = seg.get("speaker", "SPEAKER_00")

    current = {
        "speaker": speaker,
        "start": words[0]["start"],
        "end": words[0]["end"],
        "text": words[0]["word"],
        "words": [words[0]],
    }

    def finalize(s):
        s["duration"] = round(s["end"] - s["start"], 3)
        new_segments.append(s.copy())

    for i in range(1, len(words)):
        w = words[i]
        gap = w["start"] - current["end"]
        potential_len = len(current["text"]) + 1 + len(w["word"])

        if gap <= minimum_gap and potential_len <= max_chars:
            if language in ["zh", "ja", "ko"]:
                current["text"] += w["word"]
            else:
                current["text"] += " " + w["word"]

            current["end"] = w["end"]
            current["words"].append(w)
        else:
            finalize(current)
            current = {
                "speaker": speaker,
                "start": w["start"],
                "end": w["end"],
                "text": w["word"],
                "words": [w],
            }

    finalize(current)
    return new_segments



def _merge_same_boundary_segments(segments, language, max_chars_merge=120):
    if not segments:
        return segments

    merged = []
    current = segments[0]

    for nxt in segments[1:]:
        can_merge = (
            abs(current["end"] - nxt["start"]) < 1e-3
            and current["speaker"] == nxt["speaker"]
        )

        potential_len = len(current["text"]) + 1 + len(nxt["text"])

        if can_merge and potential_len <= max_chars_merge:
            if language in ["zh", "ja", "ko"]:
                current["text"] += nxt["text"]
            else:
                current["text"] = (
                    current["text"].rstrip() + " " + nxt["text"].lstrip()
                ).strip()

            current["end"] = nxt["end"]
            current["words"].extend(nxt["words"])
        else:
            current["duration"] = round(current["end"] - current["start"], 3)
            merged.append(current)
            current = nxt

    current["duration"] = round(current["end"] - current["start"], 3)
    merged.append(current)

    return merged

# 3️⃣ Call the function
# from small_segment import segment_split
# segments = segment_split(
#     final_segments,
#     language=lang_code,
#     max_chars=80,
#     minimum_gap=0.05,
#     allow_same_start_end_merge=True,  
#     max_chars_merge=90,               
# )
