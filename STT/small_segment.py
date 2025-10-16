from sentencex import segment

def segment_split(
    final_segments,
    language="en",
    max_chars=100,
    minimum_gap=0.05,
    allow_same_start_end_merge=True,
    max_chars_merge=120,
):
    """
    1. Try sentencex-based natural splitting first.
    2. Fallback to timestamp-based forced split if needed.
    3. Optionally merge adjacent segments when end==start (if text stays under max_chars_merge).
    4. Preserve timestamps perfectly for dubbing alignment.
    """
    cjk_languages = ("zh", "ja", "ko")
    if language in cjk_languages:
      max_chars=10
      max_chars_merge=20
    # print(f"Language: {language}")
    # print(f"max_chars {max_chars}")
    # print(f"max_chars {max_chars_merge}")
    all_new_segments = []

    for seg in final_segments:
        text = seg.get("text", "").strip()
        words = seg.get("words", [])
        speaker = seg.get("speaker", "SPEAKER_00")

        if not words:
            all_new_segments.append(seg)
            continue

        # --- Step 1: try sentence-based segmentation
        if language and len(text) > 20:
            try:
                sentences = list(segment(language, text))
            except Exception:
                sentences = [text]
        else:
            sentences = [text]

        # --- Step 2: fallback if too long or not punctuated
        if len(sentences) == 1 and len(sentences[0]) > max_chars:
            all_new_segments.extend(_force_split_by_words(seg, language,max_chars, minimum_gap))
            continue

        # --- Step 3: build sentence-based subsegments with timestamps
        sentence_segments = []
        wi = 0
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            sent_words, sent_start, sent_end = [], None, None

            while wi < len(words):
                w = words[wi]
                if sent_start is None:
                    sent_start = w["start"]
                sent_end = w["end"]
                sent_words.append(w)
                wi += 1

                # stop roughly when the sentence length matches
                if len("".join([x["word"] for x in sent_words])) >= len(sent.replace(" ", "")):
                    break

            sentence_segments.append({
                "speaker": speaker,
                "start": sent_start,
                "end": sent_end,
                "text": sent,
                "words": sent_words,
            })

        # --- Step 4: check lengths & fallback-split if necessary
        for s in sentence_segments:
            if len(s["text"]) > max_chars:
                all_new_segments.extend(_force_split_by_words(s, max_chars, minimum_gap))
            else:
                s["duration"] = round(s["end"] - s["start"], 3)
                all_new_segments.append(s)

    # --- Step 5: optional merging for continuous segments
    if allow_same_start_end_merge:
        all_new_segments = _merge_same_boundary_segments(
            all_new_segments,
            language,
            max_chars_merge=max_chars_merge,
        )

    return all_new_segments


# ---------- helpers ----------

def _force_split_by_words(seg, language,max_chars=90, minimum_gap=0.05):
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
            # current["text"] += " " + w["word"]
            if language in ["zh", "ja", "ko"]:  # CJK languages
                current["text"] += w["word"]   # no space
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


def _merge_same_boundary_segments(segments, language,max_chars_merge=120):
    """Merge consecutive segments where end == next.start and speakers match."""
    if not segments:
        return segments

    merged = []
    current = segments[0]

    for i in range(1, len(segments)):
        nxt = segments[i]
        can_merge = (
            abs(current["end"] - nxt["start"]) < 1e-3  # exact or near-identical time boundary
            and current["speaker"] == nxt["speaker"]
        )

        potential_len = len(current["text"]) + 1 + len(nxt["text"])
        if can_merge and potential_len <= max_chars_merge:
            # Merge safely
            # current["text"] = (current["text"].rstrip() + " " + nxt["text"].lstrip()).strip()
            if language in ["zh", "ja", "ko"]:
                current["text"] += nxt["text"]  # no space
            else:
                current["text"] = (current["text"].rstrip() + " " + nxt["text"].lstrip()).strip()
            current["end"] = nxt["end"]
            current["words"].extend(nxt["words"])
        else:
            current["duration"] = round(current["end"] - current["start"], 3)
            merged.append(current)
            current = nxt

    # finalize last
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
