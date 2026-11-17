# mines-txt2voi

ComfyUI text-to-speech workflows that clone a voice from a short recording: **Thai** with VoxCPM2 and the SiangTTS Thai LoRA, and **English** with IndexTTS-2. Both can pass the result through an RVC voice model.

| Workflow | Language | Engine | Voice sample |
|---|---|---|---|
| **VoxCPM2 Thai Voice Clone** | Thai | VoxCPM2 + SiangTTS-Thai LoRA | 12 s clip, any language |
| **IndexTTS-2 English Voice Clone** | English | IndexTTS-2 (TTS-Audio-Suite) | 12 s clip, any language |

Tested on an RTX 5070 Ti (16 GB) with torch 2.12 + CUDA 13.0 on Windows. Model files and voice recordings are not included.

## Install

1. **Node packs** (clone into `ComfyUI/custom_nodes/`):
   - [ComfyUI-VoxCPM2](https://github.com/Saganaki22/ComfyUI-VoxCPM2) (tested at `0e52a6c`)
   - [TTS-Audio-Suite](https://github.com/diodiogod/TTS-Audio-Suite) (tested at `99f0873`; run its `install.py`)
2. **Patches** (required, see below):
   ```
   git -C custom_nodes/ComfyUI-VoxCPM2 apply path/to/mines-txt2voi/patches/ComfyUI-VoxCPM2.patch
   git -C custom_nodes/TTS-Audio-Suite apply path/to/mines-txt2voi/patches/TTS-Audio-Suite.patch
   ```
3. **Models**:
   - VoxCPM2 → `models/tts/VoxCPM/VoxCPM2/` (`model.safetensors`, `audiovae.pth`) from [openbmb/VoxCPM2](https://huggingface.co/openbmb/VoxCPM2)
   - SiangTTS Thai LoRA → `models/loras/SiangTTS-Thai/` (`lora_weights.safetensors`, `lora_config.json`)
   - IndexTTS-2 and its helper models download on first run into `models/TTS/IndexTTS/` (about 8.3 GB)
4. Put your voice recording in ComfyUI's **input** folder, restart ComfyUI and drag a workflow from [`workflows/`](workflows) onto the canvas.

## Patches

| Patch | Fixes |
|---|---|
| `ComfyUI-VoxCPM2.patch` | LoRA rank 64 / alpha 128 to match SiangTTS (node default 32/16 loads it wrong) · 1-D attention mask rejected by torch 2.12 (`IndexError`) · saving through torchaudio needs torchcodec/FFmpeg (`ImportError`), uses soundfile instead |
| `TTS-Audio-Suite.patch` | IndexTTS-2 cut off the last syllable; pads the end with silence codes so the voice fades out |

Updating either node pack overwrites the patch; re-apply it afterwards.

## Settings

**Voice sample**: Trim Audio Duration takes 12 s of continuous speech (start at a part where you speak clearly and at the pace you want; the clone copies the pace). A clean mic needs no denoising: Vocal Removal and Voice Fixer were tried and made it worse (Voice Fixer filled the pauses with noise). Turn off any noise gate when recording.

**Thai (VoxCPM2)**

| Setting | Value | Why |
|---|---|---|
| voice_description | empty | the tone comes from your sample; `very slow pace, calm and relaxed, soft voice` slows speech ~25% |
| cfg_value | 2.0 | higher sounds harsh |
| inference_timesteps | 16 | cleaner than 10 |
| enable_denoiser | off | strips breath and texture |
| seed | fixed | same character on every line |
| retry_threshold | 12 | avoids false "badcase" retries |

**English (IndexTTS-2)**

| Setting | Value | Why |
|---|---|---|
| Emotion clip and sliders | bypassed | blending them with the voice distorts it |
| emotion_alpha | 1.0 | |
| temperature | 0.7 | steadier pronunciation |
| use_fp16 | off | half precision adds crackle |
| seed | fixed | |

**RVC**: put a `.pth` in `models/TTS/RVC/` (index in `models/TTS/RVC/.index/`), select the muted RVC nodes and press Ctrl+M. Train one with [Applio](https://github.com/IAHispano/Applio).

## Troubleshooting

| Problem | Fix |
|---|---|
| Speaks too fast | Fewer words per run; a slower part of the recording; Thai: the slow-pace description above |
| Distorted English | Check emotion nodes are bypassed, use_fp16 off, temperature 0.7 |
| Last word cut off (English) | Apply `TTS-Audio-Suite.patch` and restart ComfyUI |
| "badcase" retries (Thai) | Raise retry_threshold to 15 |
| Settings revert | An open ComfyUI tab saved over the file: close the tab without saving and reopen the workflow |

## Tools

[`tools/queue_test.py`](tools/queue_test.py) queues one test line in a running ComfyUI and reports the length, peak, clipping and whether the ending is cut off:

```
python tools/queue_test.py thai "สวัสดีค่ะ" --voice my_voice.wav --start 34.5
python tools/queue_test.py english "Hello there." --voice my_voice.wav
```

## Use voices with consent

Only clone your own voice or a voice whose owner has agreed to it.
