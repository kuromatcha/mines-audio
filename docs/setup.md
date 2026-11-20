# Setup

1. [Install the node packs](#1-install-the-node-packs)
2. [Apply the patches](#2-apply-the-patches)
3. [Download the models](#3-download-the-models)
4. [First run](#4-first-run)
5. [RVC voice model (optional)](#5-rvc-voice-model-optional)

Tested on an RTX 5070 Ti (16 GB) with PyTorch 2.12 + CUDA 13.0 on Windows.

## 1. Install the node packs

Clone both into `ComfyUI/custom_nodes/`. Both workflows use TTS-Audio-Suite (its RVC nodes are in the Thai workflow too); only the Thai workflow uses ComfyUI-VoxCPM2.

| Pack | Tested commit | Needed by |
|---|---|---|
| [ComfyUI-VoxCPM2](https://github.com/Saganaki22/ComfyUI-VoxCPM2) | `0e52a6c` | Thai workflow |
| [TTS-Audio-Suite](https://github.com/diodiogod/TTS-Audio-Suite) | `99f0873` | Both workflows |

```sh
cd ComfyUI/custom_nodes
git clone https://github.com/Saganaki22/ComfyUI-VoxCPM2.git
git -C ComfyUI-VoxCPM2 checkout 0e52a6c
git clone https://github.com/diodiogod/TTS-Audio-Suite.git
git -C TTS-Audio-Suite checkout 99f0873
```

Then run TTS-Audio-Suite's `install.py` with ComfyUI's Python.

The patches in step 2 are made for these commits. On a newer commit they may not apply.

## 2. Apply the patches

Clone this repository anywhere, then run from `ComfyUI/custom_nodes/`:

```sh
git -C ComfyUI-VoxCPM2 apply path/to/mines-audio/patches/ComfyUI-VoxCPM2.patch
git -C TTS-Audio-Suite apply path/to/mines-audio/patches/TTS-Audio-Suite.patch
```

| Patch | What it fixes |
|---|---|
| `ComfyUI-VoxCPM2.patch` | Loads the LoRA at rank 64 / alpha 128, which is what SiangTTS uses (the node's default 32 / 16 loads it wrong). |
| | Reshapes a 1-D attention mask that PyTorch 2.12 rejects (`IndexError`). |
| | Saves the voice sample with `soundfile` instead of torchaudio, which needs torchcodec and FFmpeg (`ImportError`). |
| `TTS-Audio-Suite.patch` | IndexTTS-2 cut off the last syllable. The patch pads the end with silence codes so the voice fades out. It only changes IndexTTS-2; the workflow now uses IndexTTS-2.5, which does not drop the last code, so this part matters only if you switch `model_path` back to IndexTTS-2. |
| | The **model_path** list showed every downloaded model twice (`IndexTTS-2.5` and `local:IndexTTS-2.5`). The patch hides the `local:` copy of the built-in names; the plain name loads the same folder without downloading. |

Updating either node pack removes its patch. Apply it again afterwards.

## 3. Download the models

Folders are inside `ComfyUI/models/`.

| Model | Folder | Files | Source |
|---|---|---|---|
| VoxCPM2 | `tts/VoxCPM/VoxCPM2/` | `model.safetensors`, `audiovae.pth` | [openbmb/VoxCPM2](https://huggingface.co/openbmb/VoxCPM2) |
| SiangTTS Thai LoRA | `loras/SiangTTS-Thai/` | `lora_weights.safetensors`, `lora_config.json` | |
| IndexTTS-2.5 | `TTS/IndexTTS/IndexTTS-2.5/` | downloaded automatically on the first run, about 5.5 GB (pinned revision `ba2480d`) | [IndexTeam/IndexTTS-2.5](https://huggingface.co/IndexTeam/IndexTTS-2.5) |
| IndexTTS helpers | `TTS/IndexTTS/` (`w2v-bert-2.0`, `campplus`, `bigvgan_v2_22khz_80band_256x`) | downloaded automatically on the first run, about 2.8 GB | |

## 4. First run

1. Put your voice recording in ComfyUI's **input** folder and restart ComfyUI.
2. Drag a workflow from [`workflows/`](../workflows) onto the canvas.
3. On **Speaker voice**, pick your recording. The workflows ship with the placeholder name `my_voice.wav`.
4. On **Trim speaker clip**, set `start_index` to the second where 12 s of clear, continuous speech begins.
5. Type the text and run. The result plays in the **Preview** node.

What to record and which values to use: [settings](settings.md).

## 5. RVC voice model (optional)

The RVC nodes are muted in both workflows.

1. Put the model's `.pth` file in `models/TTS/RVC/` and its index file in `models/TTS/RVC/.index/`.
2. Pick it on **Your RVC model** (placeholder name: `my_voice_model.pth`).
3. Select the four muted RVC nodes and press **Ctrl+M**.

You can train a model with [Applio](https://github.com/IAHispano/Applio).
