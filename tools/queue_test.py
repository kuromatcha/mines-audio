"""Queue one test line in a running ComfyUI and report how it came out.

    python tools/queue_test.py thai "สวัสดีค่ะ" --voice my_voice.wav
    python tools/queue_test.py english "Hello there." --voice my_voice.wav --start 34.5

The voice file must be in ComfyUI's input folder. The result is saved under
output/tts_tests/ and checked for clipping and a cut-off ending.
"""
import argparse, io, json, time, urllib.parse, urllib.request

import numpy as np
import soundfile as sf


def thai_prompt(a):
    return {
        "2": {"class_type": "VoxCPM2_Clone", "inputs": {
            "model_name": "VoxCPM2", "lora_name": "SiangTTS-Thai\\lora_weights.safetensors",
            "voice_description": a.description, "text": a.text, "reference_audio": ["trim", 0],
            "prompt_text": "", "cfg_value": 2.0, "inference_timesteps": 16, "max_tokens": 4096,
            "normalize_text": True, "enable_denoiser": False, "seed": a.seed, "force_offload": False,
            "dtype": "auto", "device": "cuda", "enable_asr": False, "retry_max_attempts": 3,
            "retry_threshold": 12.0, "torch_compile": False}},
    }


def english_prompt(a):
    return {
        "engine": {"class_type": "IndexTTSEngineNode", "inputs": {
            "model_path": "IndexTTS-2.5", "device": "cuda", "emotion_alpha": 1.0, "use_random": False,
            "max_text_tokens_per_segment": 120, "interval_silence": 300, "temperature": 0.7, "top_p": 0.8,
            "top_k": 30, "do_sample": True, "length_penalty": 0.0, "num_beams": 3, "repetition_penalty": 10.0,
            "max_mel_tokens": 1500, "use_fp16": False, "use_deepspeed": False, "use_cuda_kernel": "auto"}},
        "2": {"class_type": "UnifiedTTSTextNode", "inputs": {
            "TTS_engine": ["engine", 0], "text": a.text, "narrator_voice": "none", "seed": a.seed,
            "opt_narrator": ["trim", 0], "enable_chunking": True, "max_chars_per_chunk": 400,
            "chunk_combination_method": "auto", "silence_between_chunks_ms": 100,
            "enable_audio_cache": False, "batch_size": 0}},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("language", choices=["thai", "english"])
    p.add_argument("text")
    p.add_argument("--voice", required=True, help="voice recording, a file in ComfyUI's input folder")
    p.add_argument("--start", type=float, default=1.0, help="where the 12 s voice sample starts (s)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--description", default="", help="Thai only: VoxCPM voice description")
    p.add_argument("--server", default="http://127.0.0.1:8188")
    a = p.parse_args()

    prompt = thai_prompt(a) if a.language == "thai" else english_prompt(a)
    prompt["load"] = {"class_type": "LoadAudio", "inputs": {"audio": a.voice}}
    prompt["trim"] = {"class_type": "TrimAudioDuration", "inputs": {"audio": ["load", 0], "start_index": a.start, "duration": 12.0}}
    prompt["save"] = {"class_type": "SaveAudio", "inputs": {"audio": ["2", 0], "filename_prefix": f"tts_tests/{a.language}"}}

    req = urllib.request.Request(f"{a.server}/prompt", data=json.dumps({"prompt": prompt}).encode(),
                                 headers={"Content-Type": "application/json"})
    pid = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
    print("queued", pid)
    while True:
        h = json.loads(urllib.request.urlopen(f"{a.server}/history/{pid}").read())
        if pid in h:
            break
        time.sleep(3)
    if h[pid]["status"]["status_str"] != "success":
        raise SystemExit(json.dumps(h[pid]["status"]["messages"], ensure_ascii=False)[-1500:])

    for out in h[pid]["outputs"].values():
        for f in out.get("audio", []):
            if f["subfolder"] != "tts_tests":
                continue
            path = f"output/{f['subfolder']}/{f['filename']}"
            query = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f["subfolder"], "type": "output"})
            x, sr = sf.read(io.BytesIO(urllib.request.urlopen(f"{a.server}/view?{query}").read()), dtype="float32")
            x = x if x.ndim == 1 else x.mean(axis=1)
            hop = sr // 20
            end_db = 20 * np.log10(np.sqrt((x[-2 * hop:-hop] ** 2).mean()) + 1e-9)
            clipped = int((np.abs(x) >= 0.999).sum())
            print(f"{path}\n  {len(x) / sr:.2f}s, peak {np.abs(x).max():.2f}, clipped samples {clipped}, "
                  f"level just before the end {end_db:.0f} dB {'(cut off?)' if end_db > -40 else '(fades out)'}")


if __name__ == "__main__":
    main()
