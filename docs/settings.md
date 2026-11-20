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

### English (IndexTTS-2.5)

| Setting | In the workflow | Notes |
|---|---|---|
| Emotion clip | bypassed | |
| Emotion sliders | connected: Calm 0.4, Melancholic 0.2 | **Open.** Earlier recommendation: bypass the sliders too (select the node, Ctrl+B), because blending them with the voice distorted it. |
| `model_path` | IndexTTS-2.5 | Was IndexTTS-2. The values below were tuned on IndexTTS-2 and have not been re-tested on 2.5. |
| `language` | English | 2.5 only. |
| `duration_factor` | 1.0 | 2.5 only. 1.1-1.25 slows the speech. |
| `emotion_alpha` | 1.0 | |
| `temperature` | 0.8 | **Open.** Earlier recommendation: 0.7 for steadier pronunciation. |
| `use_fp16` | on | **Open.** On 2.5 this means BF16. Earlier recommendation (on IndexTTS-2, FP16): off, because half precision added crackle. |
| `seed` | fixed | |

## Troubleshooting

| Problem | Fix |
|---|---|
| Speaks too fast | Fewer words per run, or a slower part of the recording. English: `duration_factor` 1.1-1.25. Thai: the slow-pace `voice_description` above. |
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
- The script uses its own fixed values, not the workflow files: Thai `cfg_value` 2.0 and an empty description; English IndexTTS-2.5, `temperature` 0.7, `use_fp16` off, no emotion input.
- Results are saved under `output/tts_tests/`.
