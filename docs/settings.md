# Settings

## Voice sample

**Trim speaker clip** takes 12 s of continuous speech from your recording.

- Start at a part where you speak clearly and at the pace you want. The clone copies the pace.
- A clean microphone needs no denoising. Vocal Removal and Voice Fixer were tried and made the result worse (Voice Fixer filled the pauses with noise).
- Turn off any noise gate when recording.

## Values in the workflows

The **In the workflow** column is what the files in [`workflows/`](../workflows) contain now. Where an earlier test recommended a different value, it is in the notes. Those rows are marked **open**: the two values have not been compared again yet.

### Thai (VoxCPM2)

| Setting | In the workflow | Notes |
|---|---|---|
| `voice_description` | `a female` | **Open.** Earlier recommendation: empty, so the tone comes only from the sample. `very slow pace, calm and relaxed, soft voice` slows speech by about 25%. |
| `cfg_value` | 2.5 | **Open.** Earlier recommendation: 2.0; higher sounded harsh. |
| `inference_timesteps` | 16 | Cleaner than 10. |
| `enable_denoiser` | off | The denoiser strips breath and texture. |
| `seed` | fixed | The same character on every line. |
| `retry_threshold` | 12 | Avoids false "badcase" retries. |

### English and Japanese (IndexTTS-2.5)

The same workflow speaks both: set `language` to English or Japanese. Values tested over 4 seeds in each language, with a clean 12 s voice sample.

| Setting | In the workflow | Notes |
|---|---|---|
| Emotion clip | bypassed | |
| Emotion sliders | connected: Happy 0.2, Calm 0.4 | Soft and warm. Bypass the node (Ctrl+B) for a neutral read. |
| `emotion_alpha` | 0.65 | Keeps the voice likeness. |
| `model_path` | IndexTTS-2.5 | |
| `language` | English | Or Japanese. |
| `duration_factor` | 1.0 | Keep it at 1.0 with pause tags (see below). |
| `temperature`, `top_p`, `top_k`, `num_beams` | 0.8, 0.8, 31, 3 | |
| `use_fp16` | on | On 2.5 this means BF16. |
| `seed` | fixed | |
| Text | sentences separated by `[pause:0.8s]` | See below. |

### Pacing

- **Voice sample:** use 12 s of continuous speech with no silence at the start and no break longer than about 0.6 s. The clone copies the sample's rhythm: a sample with 1-1.5 s gaps gave 14-18 s of dead air on 3 of 4 seeds, with the words squeezed into the rest (up to 4.5 words/s). Set **Trim speaker clip** `start_index` to where such a stretch begins.
- **Sentence pauses:** IndexTTS-2.5 has no setting for the gap between sentences, and `max_text_tokens_per_segment` (minimum 50) is too large to split short text. Put a pause tag between sentences instead, for example `Long day, hm? [pause:0.8s] It's okay...`. Any length works (`[pause:0.4s]`, `[pause:1s]`).
- **Speed with pause tags:** keep `duration_factor` at 1.0. Each tagged sentence is generated on its own and already comes out slower; 1.3 made the speech drag. Raise it to 1.1 only if it still sounds rushed.

Measured with `[pause:0.8s]` and `duration_factor` 1.0:

| Language | Pace | Gap between sentences | Dead air |
|---|---|---|---|
| English | 2.5-3.4 words/s | 0.6-1.0 s | none |
| Japanese | 4.6-6.2 morae/s | 0.8-1.6 s | none |

Japanese gaps come out longer; use `[pause:0.5s]` for Japanese if they feel too long.

### Japanese text

- Set `language` to Japanese and type normally, kanji included. With `TTS-Audio-Suite.patch`, every kanji word is read through the dictionary; without it the model read many kanji with Chinese readings (近く as *jinku*, 今夜 as *jinya*).
- 私 reads as わたくし. Write `<私|わたし>` (or just わたし) for わたし. Any word can be given a reading this way: `<今夜|こんや>`.
- A leading 「あ…」 tends to come out as a sigh (「ふぅ…」, 「うーん」).

## Troubleshooting

| Problem | Fix |
|---|---|
| Long dead air in the middle, or speech too fast (English, Japanese) | The voice sample has long gaps. Move **Trim speaker clip** to 12 s of continuous speech ([pacing](#pacing)). |
| Sentences run together (English, Japanese) | Put `[pause:0.8s]` between sentences, keep `duration_factor` at 1.0. |
| Speaks too slowly with pause tags | Set `duration_factor` back to 1.0. |
| Japanese kanji read with Chinese readings | Apply `TTS-Audio-Suite.patch`. If it is applied and still happens, ComfyUI is reusing an engine loaded before the patch: use **Unload Models** in ComfyUI or quit and restart it. |
| Speaks too fast (Thai) | Fewer words per run, or a slower part of the recording, or the slow-pace `voice_description` above. |
| Distorted English | Bypass the emotion sliders, turn `use_fp16` off, set `temperature` to 0.7. |
| Last word cut off (English) | Only seen on IndexTTS-2: apply `TTS-Audio-Suite.patch` ([setup](setup.md#2-apply-the-patches)) and restart ComfyUI. |
| "badcase" retries (Thai) | Raise `retry_threshold` to 15. |
| Settings revert | An open ComfyUI tab saved over the file. Close the tab without saving and reopen the workflow. |

## Test script

[`tools/queue_test.py`](../tools/queue_test.py) queues one line in a running ComfyUI and reports the length, the peak level, clipping and whether the ending is cut off.

```sh
python tools/queue_test.py thai "สวัสดีค่ะ" --voice my_voice.wav --start 34.5
python tools/queue_test.py english "Hello there." --voice my_voice.wav
```

- `--voice` is a file in ComfyUI's input folder. `--start` is the second where the 12 s sample begins (default 1).
- `--server` sets ComfyUI's address (default `http://127.0.0.1:8188`).
- Run it with a Python that has `numpy` and `soundfile` (`pip install soundfile`).
- The script uses its own fixed values, not the workflow files: Thai `cfg_value` 2.0 and an empty description; English IndexTTS-2.5, `temperature` 0.7, `use_fp16` off, no emotion input, no pause tags.
- Results are saved under `output/tts_tests/`.
