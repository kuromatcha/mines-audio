# mines-TTS

ComfyUI text-to-speech workflows that clone a voice from a 12-second recording.

| Workflow | Language | Engine |
|---|---|---|
| **VoxCPM2 Thai Voice Clone** | Thai | VoxCPM2 + SiangTTS-Thai LoRA |
| **IndexTTS-2 English Voice Clone** | English | IndexTTS-2 (TTS-Audio-Suite) |

Both take a voice sample in any language, and both can pass the result through an RVC voice model (off by default).

## Requirements

- ComfyUI with two node packs, each at a tested commit and with a small patch from this repository: [setup guide](docs/setup.md).
- Tested on an RTX 5070 Ti (16 GB) with PyTorch 2.12 + CUDA 13.0 on Windows.
- Model files and voice recordings are not included.

## Quick start

1. Follow the [setup guide](docs/setup.md): node packs, patches, models.
2. Put your voice recording in ComfyUI's **input** folder.
3. Drag a file from [`workflows/`](workflows) into ComfyUI, pick your recording on **Speaker voice**, type the text and run.

## Docs

| | |
|---|---|
| [Setup](docs/setup.md) | Node packs, patches, models, first run, RVC |
| [Settings](docs/settings.md) | Voice sample, the values each workflow ships with, troubleshooting, the test script |

## Use voices with consent

Only clone your own voice or a voice whose owner has agreed to it.
