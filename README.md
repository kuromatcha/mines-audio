# mines-audio

ComfyUI audio workflows: voice cloning (text to speech) and music.

## Voice

Clone a voice from a 12-second recording.

| Workflow | Language | Engine |
|---|---|---|
| **VoxCPM2 Thai Voice Clone** | Thai | VoxCPM2 + SiangTTS-Thai LoRA |
| **IndexTTS-2.5 English Voice Clone** | English, Japanese | IndexTTS-2.5 (TTS-Audio-Suite) |

Both take a voice sample in any language, and both can pass the result through an RVC voice model (off by default).

## Music

| Workflow | Makes |
|---|---|
| **Mine's Stable Audio 3** | Instrumentals, game BGM and sound effects, at an exact length |
| **Mine's YuE2** | Songs with vocals, from an editable score |
| **Mine's MiniMax Music 3** | Full songs with vocals |

Built-in ComfyUI nodes only. Model licences differ: see [music](docs/music.md).

## Requirements

- Voice: ComfyUI with two node packs, each at a tested commit and with a small patch from this repository: [setup guide](docs/setup.md).
- Music: ComfyUI 0.45.6 or newer and the model files: [music](docs/music.md).
- Tested on 16 GB GPUs (RTX 5070 Ti, RTX 5060 Ti) with PyTorch 2.12 + CUDA 13.0 on Windows.
- Model files and voice recordings are not included.

## Quick start

Voice:

1. Follow the [setup guide](docs/setup.md): node packs, patches, models.
2. Put your voice recording in ComfyUI's **input** folder.
3. Drag a voice workflow from [`workflows/`](workflows) into ComfyUI, pick your recording on **Speaker voice**, type the text and run.

Music:

1. Download the models for the workflow you want ([music](docs/music.md)).
2. Drag it from [`workflows/`](workflows) into ComfyUI, write the prompt and run.

## Docs

| | |
|---|---|
| [Setup](docs/setup.md) | Voice: node packs, patches, models, first run, RVC |
| [Settings](docs/settings.md) | Voice: voice sample, the values each workflow ships with, troubleshooting, the test script |
| [Music](docs/music.md) | Models, which workflow to use, tested speed, prompt tips, loops |

## Use voices with consent

Only clone your own voice or a voice whose owner has agreed to it.
