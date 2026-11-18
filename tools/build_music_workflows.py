"""Build Mine's YuE2 / Stable Audio 3 / MiniMax Music 3 in the layout of the Mine's workflows.

Usage: python -I tools/build_music_workflows.py workflows

Top level: one row at y=0 (settings subgraph node · Result · brown Guide note), 960 high, 40 px gaps, pinned.
Subgraph: numbered groups of 380-wide titled columns on the 20 px grid, shared bottom edge,
brown = model loader / sampler, green = prompt.
"""
import json, os, sys, uuid

W, GAP_COL, GAP_GROUP, STEP, TOP_H = 380, 40, 40, 60, 960
BROWN = ("#432", "#653")
GREEN = ("#232", "#353")
NS = uuid.UUID("6b1f3c2e-8f7a-4c55-9a0e-3d2b1c0a9f88")


def snap(v, g=20):
    return -(-int(round(v)) // g) * g


class Graph:
    def __init__(self, name):
        self.name, self.nodes, self.links, self.by_key = name, [], [], {}
        self.inputs = []  # subgraph inputs
        self.next_link = 1

    def node(self, key, type_, title, sockets=(), widgets=(), outputs=(), color=None, h=None, multiline=()):
        """widgets: (name, type, value[, control]) ; control = control_after_generate value inserted after it."""
        nid = len(self.nodes) + 1
        inputs = [{"localized_name": n, "name": n, "type": t, "link": None} for n, t in sockets]
        values, named = [], {}
        for w in widgets:
            n, t, v = w[:3]
            inputs.append({"localized_name": n, "name": n, "type": t, "widget": {"name": n}, "link": None})
            values.append(v); named[n] = v
            if len(w) > 3:
                values.append(w[3]); named["control_after_generate"] = w[3]
        n_rows = len(widgets) + max(len(sockets), len(outputs))
        height = h or snap(50 + 26 * n_rows + 180 * len(multiline))
        node = {"id": nid, "type": type_, "pos": [0, 0], "size": [W, height], "flags": {}, "order": nid - 1, "mode": 0,
                "inputs": inputs,
                "outputs": [{"localized_name": n, "name": n, "type": t, "links": []} for n, t in outputs],
                "title": title, "properties": {"Node name for S&R": type_}}
        if widgets:
            node["widgets_values"] = values
            node["widgets_values_named"] = named
        if color:
            node["color"], node["bgcolor"] = color
        self.nodes.append(node); self.by_key[key] = node
        return node

    def _slot(self, node, name):
        return next(i for i, x in enumerate(node["inputs"]) if x["name"] == name)

    def link(self, src, out_slot, dst, in_name):
        s, d = self.by_key[src], self.by_key[dst]
        lid = self.next_link; self.next_link += 1
        t = s["outputs"][out_slot]["type"]
        s["outputs"][out_slot]["links"].append(lid)
        d["inputs"][self._slot(d, in_name)]["link"] = lid
        self.links.append({"id": lid, "origin_id": s["id"], "origin_slot": out_slot, "target_id": d["id"],
                           "target_slot": self._slot(d, in_name), "type": t})

    def promote(self, name, label, type_, targets, value):
        """A settings-node widget driving one or more inner widgets."""
        slot = len(self.inputs)
        ids = []
        for key, wname in targets:
            d = self.by_key[key]
            lid = self.next_link; self.next_link += 1
            d["inputs"][self._slot(d, wname)]["link"] = lid
            self.links.append({"id": lid, "origin_id": -10, "origin_slot": slot, "target_id": d["id"],
                               "target_slot": self._slot(d, wname), "type": type_})
            ids.append(lid)
            d["widgets_values_named"][wname] = value
            # keep the inner widget value in step with the settings node
            order = [x["name"] for x in d["inputs"] if "widget" in x]
            vals, k = [], 0
            for x in order:
                vals.append(d["widgets_values_named"][x])
                if x in ("seed", "noise_seed") and "control_after_generate" in d["widgets_values_named"]:
                    vals.append(d["widgets_values_named"]["control_after_generate"])
            d["widgets_values"] = vals
        self.inputs.append({"id": str(uuid.uuid5(NS, f"{self.name}/{name}")), "name": name, "type": type_,
                            "linkIds": ids, "label": label, "pos": [-100, 24 + 20 * slot], "value": value})

    def layout(self, groups, previews=None):
        """groups: [(title, [[key, ...], ...columns])]. previews: (title, [(key, width, height)]) placed above."""
        out_groups, x = [], -20
        bottoms = []
        for gi, (title, cols) in enumerate(groups, 1):
            for ci, col in enumerate(cols):
                y = 0
                for key in col:
                    n = self.by_key[key]
                    n["pos"] = [x + 20 + ci * (W + GAP_COL), y]
                    y = snap(y + n["size"][1] + STEP)
                bottoms.append(y - STEP)
            width = len(cols) * W + (len(cols) - 1) * GAP_COL + 40
            out_groups.append({"id": gi, "title": f"{gi} · {title}", "bounding": [x, -80, width, 0], "color": "#3f789e", "flags": {}})
            x += width + GAP_GROUP
        bottom = snap(max(bottoms) + 40)
        for g in out_groups:
            g["bounding"][3] = bottom + 80
        if previews:
            title, items = previews
            px, ph = 0, max(h for _, _, h in items)
            for key, w, h in items:
                self.by_key[key]["pos"] = [px, -200 - ph]
                self.by_key[key]["size"] = [w, h]
                px += w + GAP_COL
            out_groups.append({"id": len(out_groups) + 1, "title": title,
                               "bounding": [-20, -280 - ph, px - GAP_COL + 40, ph + 120], "color": "#3f789e", "flags": {}})
        self.groups, self.out_x = out_groups, x

    def output(self, src, slot, name, type_):
        lid = self.next_link; self.next_link += 1
        self.by_key[src]["outputs"][slot]["links"].append(lid)
        self.links.append({"id": lid, "origin_id": self.by_key[src]["id"], "origin_slot": slot, "target_id": -20, "target_slot": 0, "type": type_})
        self.out = {"id": str(uuid.uuid5(NS, f"{self.name}/out")), "name": name, "type": type_, "linkIds": [lid],
                    "localized_name": name, "label": name, "pos": [self.out_x + 20, 24]}

    def workflow(self, guide, result_prefix):
        for n in self.nodes:
            for o in n["outputs"]:
                if not o["links"]:
                    o["links"] = None
        sid = str(uuid.uuid5(NS, self.name))
        sg = {"id": sid, "version": 1,
              "state": {"lastGroupId": len(self.groups), "lastNodeId": len(self.nodes), "lastLinkId": self.next_link - 1, "lastRerouteId": 0},
              "revision": 0, "config": {}, "name": self.name,
              "inputNode": {"id": -10, "bounding": [-380, 0, 300, 24 + 20 * len(self.inputs) + 20]},
              "outputNode": {"id": -20, "bounding": [self.out_x, 0, 128, 68]},
              "inputs": [{k: v for k, v in i.items() if k != "value"} for i in self.inputs],
              "outputs": [self.out], "widgets": [], "nodes": self.nodes, "groups": self.groups, "links": self.links,
              "extra": {"workflowRendererVersion": "LG"}}
        settings = {"id": 1, "type": sid, "pos": [0, 0], "size": [840, TOP_H], "flags": {"pinned": True}, "order": 0, "mode": 0,
                    "inputs": [{"label": i["label"], "name": i["name"], "type": i["type"], "widget": {"name": i["name"]}, "link": None} for i in self.inputs],
                    "outputs": [{"label": self.out["name"], "localized_name": self.out["name"], "name": self.out["name"], "type": self.out["type"], "links": [1]}],
                    "properties": {"previewExposures": []},
                    "widgets_values": [i["value"] for i in self.inputs],
                    "widgets_values_named": {i["name"]: i["value"] for i in self.inputs}}
        result = {"id": 2, "type": "SaveAudio", "pos": [880, 0], "size": [480, TOP_H], "flags": {"pinned": True}, "order": 1, "mode": 0,
                  "inputs": [{"localized_name": "audio", "name": "audio", "type": "AUDIO", "link": 1},
                             {"localized_name": "filename_prefix", "name": "filename_prefix", "type": "STRING", "widget": {"name": "filename_prefix"}, "link": None}],
                  "outputs": [], "title": "Result", "properties": {"Node name for S&R": "SaveAudio"},
                  "widgets_values": [result_prefix], "widgets_values_named": {"filename_prefix": result_prefix}}
        note = {"id": 3, "type": "MarkdownNote", "pos": [1400, 0], "size": [560, TOP_H], "flags": {"pinned": True}, "order": 2, "mode": 0,
                "inputs": [], "outputs": [], "title": "Guide", "properties": {}, "widgets_values": [guide],
                "widgets_values_named": {"text": guide}, "color": BROWN[0], "bgcolor": BROWN[1]}
        return {"id": str(uuid.uuid5(NS, self.name + "/wf")), "revision": 0, "last_node_id": 3, "last_link_id": 1,
                "nodes": [settings, result, note], "links": [[1, 1, 0, 2, 0, "AUDIO"]], "groups": [],
                "definitions": {"subgraphs": [sg]}, "config": {}, "extra": {"workflowRendererVersion": "LG"}, "version": 0.4}


# ---------------------------------------------------------------- YuE2
def yue2():
    g = Graph("Mine's YuE2")
    style = "Upbeat indie pop with warm female vocals, bright electric guitars, punchy drums, melodic bass, and subtle synth layers. Catchy and energetic, with an uplifting summer atmosphere, a memorable chorus, and polished modern production."
    lyrics = "[Verse]\nMorning light across the window\nCity waking down below\nI can hear the streets are calling\nFeels like somewhere we should go\n\n[Chorus]\nRun with me into the sunlight\nLeave the shadows far behind\nWe don't need to know tomorrow\nTonight the whole world feels alive\n"
    g.node("ckpt", "CheckpointLoaderSimple", "Load YuE2 model", widgets=[("ckpt_name", "COMBO", "yue2_3b_bf16.safetensors")],
           outputs=[("MODEL", "MODEL"), ("CLIP", "CLIP"), ("VAE", "VAE")], color=BROWN, h=160)
    g.node("seed", "SeedNode", "Seed", widgets=[("seed", "INT", 0, "randomize")], outputs=[("seed", "INT")], h=120)
    g.node("abc", "YuE2GenerateABC", "Write score (ABC)", sockets=[("clip", "CLIP")],
           widgets=[("style", "STRING", style), ("lyrics", "STRING", lyrics), ("seed", "INT", 0, "randomize"), ("mode", "COMBO", "full"),
                    ("max_abc_tokens", "INT", 8192), ("temperature", "FLOAT", 0.7), ("top_p", "FLOAT", 0.9), ("top_k", "INT", 30),
                    ("repetition_penalty", "FLOAT", 1.005), ("penalty_window", "INT", 100)],
           outputs=[("abc", "STRING")], color=GREEN, multiline=(1, 2))
    g.node("noabc", "PrimitiveStringMultiline", "Own score (used when score plan is off)", widgets=[("value", "STRING", "")],
           outputs=[("STRING", "STRING")], multiline=(1,))
    g.node("sw", "ComfySwitchNode", "Switch: score plan", sockets=[("on_false", "*"), ("on_true", "*")],
           widgets=[("switch", "BOOLEAN", True)], outputs=[("output", "*")], h=140)
    g.node("music", "YuE2GenerateMusic", "Generate music tokens", sockets=[("clip", "CLIP")],
           widgets=[("style", "STRING", style), ("lyrics", "STRING", lyrics), ("abc", "STRING", ""), ("seed", "INT", 0, "randomize"),
                    ("mode", "COMBO", "full"), ("max_duration", "FLOAT", 180.0), ("temperature", "FLOAT", 1.0), ("top_p", "FLOAT", 0.95),
                    ("top_k", "INT", 100), ("repetition_penalty", "FLOAT", 1.2)],
           outputs=[("CONDITIONING", "CONDITIONING"), ("seconds", "FLOAT")], color=GREEN, multiline=(1, 2, 3))
    g.node("neg", "ConditioningZeroOut", "Empty negative", sockets=[("conditioning", "CONDITIONING")], outputs=[("CONDITIONING", "CONDITIONING")], h=80)
    g.node("lat", "EmptyYuE2LatentAudio", "Empty latent of that length", widgets=[("seconds", "FLOAT", 120.0), ("batch_size", "INT", 1)],
           outputs=[("LATENT", "LATENT")], h=120)
    g.node("ks", "KSampler", "Sample", sockets=[("model", "MODEL"), ("positive", "CONDITIONING"), ("negative", "CONDITIONING"), ("latent_image", "LATENT")],
           widgets=[("seed", "INT", 0, "randomize"), ("steps", "INT", 32), ("cfg", "FLOAT", 1.0), ("sampler_name", "COMBO", "dpm_2"),
                    ("scheduler", "COMBO", "sgm_uniform"), ("denoise", "FLOAT", 1.0)], outputs=[("LATENT", "LATENT")], color=BROWN, h=320)
    g.node("dec", "VAEDecodeAudio", "Decode audio", sockets=[("samples", "LATENT"), ("vae", "VAE")], outputs=[("AUDIO", "AUDIO")], h=100)
    g.node("prev", "PreviewAny", "Preview: score (ABC)", sockets=[("source", "*")], outputs=[], h=520)

    g.link("ckpt", 1, "abc", "clip"); g.link("ckpt", 1, "music", "clip")
    g.link("noabc", 0, "sw", "on_false"); g.link("abc", 0, "sw", "on_true"); g.link("sw", 0, "music", "abc")
    g.link("abc", 0, "prev", "source")
    for k in ("abc", "music", "ks"):
        g.link("seed", 0, k, "seed")
    g.link("music", 0, "neg", "conditioning"); g.link("music", 1, "lat", "seconds")
    g.link("ckpt", 0, "ks", "model"); g.link("music", 0, "ks", "positive"); g.link("neg", 0, "ks", "negative"); g.link("lat", 0, "ks", "latent_image")
    g.link("ks", 0, "dec", "samples"); g.link("ckpt", 2, "dec", "vae")

    g.promote("style", "style", "STRING", [("abc", "style"), ("music", "style")], style)
    g.promote("lyrics", "lyrics", "STRING", [("abc", "lyrics"), ("music", "lyrics")], lyrics)
    g.promote("switch", "score plan", "BOOLEAN", [("sw", "switch")], True)
    g.promote("mode", "mode", "COMBO", [("abc", "mode"), ("music", "mode")], "full")
    g.promote("max_duration", "max duration (seconds)", "FLOAT", [("music", "max_duration")], 180.0)
    g.promote("ckpt_name", "model", "COMBO", [("ckpt", "ckpt_name")], "yue2_3b_bf16.safetensors")
    g.promote("steps", "steps", "INT", [("ks", "steps")], 32)

    g.layout([("Models", [["ckpt", "seed"]]),
              ("Score", [["abc"], ["noabc", "sw"]]),
              ("Music tokens", [["music", "neg"]]),
              ("Sampling", [["lat", "ks"]]),
              ("Decode", [["dec"]])],
             previews=("Previews", [("prev", 800, 520)]))
    g.output("dec", 0, "audio", "AUDIO")
    guide = """# Guide

## Prompt
- **style**: genre, vocal type, language, BPM, instruments. Musical instructions go here, not in the lyrics.
- **lyrics**: only the words to sing, with section tags: `[Verse]` `[Chorus]` `[Bridge]` `[Outro]`.
- Song length follows the lyrics. More sections = longer song.
- Not for instrumentals: it hums even with no lyrics. Use Stable Audio 3 for BGM.

## Settings
- **score plan**: on · writes melody and chords (ABC) first, then sings them. Off = uses *Own score* inside the subgraph; empty = no score, faster and looser.
- **mode**: full (melody + chords) · melody (for covers)
- **max duration (seconds)**: 180 · upper limit, it can end sooner. Up to 900.
- **model**: bf16 (7.8 GB) · int8 for less VRAM
- **steps**: 32

## Previews
- Inside the subgraph, *Preview: score (ABC)* shows the score it wrote. To re-render that tune: paste it (edited or not) into *Own score*, turn **score plan** off.

## Inside the subgraph
- dpm_2 / sgm_uniform · cfg 1
- Seed: random. To keep one: *Seed* → fixed.
- Sampling settings (temperature, top_p, top_k): *Write score* and *Generate music tokens*.

## Routine
1. Write style and lyrics, run 2–3 seeds.
2. Keep the best: fix the seed, then adjust style or lyrics.

About 2–4 min per song on 16 GB. Licence: CC BY-NC 4.0 (non-commercial)."""
    return g.workflow(guide, "audio/yue2")


# ---------------------------------------------------------------- Stable Audio 3
def sa3():
    g = Graph("Mine's Stable Audio 3")
    prompt = "Japanese visual novel slice-of-life daily BGM in bright J-pop style with a catchy piano lead melody, clean electric guitar cutting, bouncy electric bass, snappy pop drums, glockenspiel and a light string section over a royal road IV-V-iii-vi chord progression, creating a cheerful, youthful school-days morning feel. BPM: 128. Length: 90 seconds"
    g.node("ckpt", "CheckpointLoaderSimple", "Load Stable Audio 3 model", widgets=[("ckpt_name", "COMBO", "stable_audio_3_medium.safetensors")],
           outputs=[("MODEL", "MODEL"), ("CLIP", "CLIP"), ("VAE", "VAE")], color=BROWN, h=160)
    g.node("clip", "CLIPLoader", "Load text encoder", widgets=[("clip_name", "COMBO", "t5gemma_b_b_ul2.safetensors"), ("type", "COMBO", "stable_audio"), ("device", "COMBO", "default")],
           outputs=[("CLIP", "CLIP")], h=160)
    g.node("pos", "CLIPTextEncode", "Encode prompt", sockets=[("clip", "CLIP")], widgets=[("text", "STRING", prompt)],
           outputs=[("CONDITIONING", "CONDITIONING")], color=GREEN, h=320)
    g.node("neg", "CLIPTextEncode", "Encode negative prompt", sockets=[("clip", "CLIP")], widgets=[("text", "STRING", "")],
           outputs=[("CONDITIONING", "CONDITIONING")], h=200)
    g.node("lat", "EmptyLatentAudio", "Empty latent of that length", widgets=[("seconds", "FLOAT", 90.0), ("batch_size", "INT", 2)],
           outputs=[("LATENT", "LATENT")], h=120)
    g.node("ks", "KSampler", "Sample", sockets=[("model", "MODEL"), ("positive", "CONDITIONING"), ("negative", "CONDITIONING"), ("latent_image", "LATENT")],
           widgets=[("seed", "INT", 0, "randomize"), ("steps", "INT", 8), ("cfg", "FLOAT", 1.0), ("sampler_name", "COMBO", "lcm"),
                    ("scheduler", "COMBO", "simple"), ("denoise", "FLOAT", 1.0)], outputs=[("LATENT", "LATENT")], color=BROWN, h=320)
    g.node("dec", "VAEDecodeAudio", "Decode audio", sockets=[("samples", "LATENT"), ("vae", "VAE")], outputs=[("AUDIO", "AUDIO")], h=100)

    g.link("clip", 0, "pos", "clip"); g.link("clip", 0, "neg", "clip")
    g.link("ckpt", 0, "ks", "model"); g.link("pos", 0, "ks", "positive"); g.link("neg", 0, "ks", "negative"); g.link("lat", 0, "ks", "latent_image")
    g.link("ks", 0, "dec", "samples"); g.link("ckpt", 2, "dec", "vae")

    g.promote("text", "prompt", "STRING", [("pos", "text")], prompt)
    g.promote("text_1", "negative prompt", "STRING", [("neg", "text")], "")
    g.promote("seconds", "length (seconds)", "FLOAT", [("lat", "seconds")], 90.0)
    g.promote("batch_size", "batch size", "INT", [("lat", "batch_size")], 2)
    g.promote("ckpt_name", "model", "COMBO", [("ckpt", "ckpt_name")], "stable_audio_3_medium.safetensors")
    g.promote("steps", "steps", "INT", [("ks", "steps")], 8)
    g.promote("cfg", "cfg", "FLOAT", [("ks", "cfg")], 1.0)

    g.layout([("Models", [["ckpt", "clip"]]),
              ("Prompt", [["pos", "neg"]]),
              ("Sampling", [["lat", "ks"]]),
              ("Decode", [["dec"]])])
    g.output("dec", 0, "audio", "AUDIO")
    guide = """# Guide

## Prompt
- One sentence: **style** with **main instruments**, **layers**, **percussion**, **mood**. End with `BPM: X. Length: Y seconds`.
- Instrumental and SFX only: it never sings. Good for game BGM and loops.
- Name the scene the music is for ("Japanese visual novel morning BGM", "boss battle").
- For a short SFX, describe the sound and set **length** to a few seconds.

## Settings
- **negative prompt**: empty is fine.
- **length (seconds)**: exact length of the clip. Match the Length in the prompt.
- **batch size**: 2 · takes per run. Cheap: 8 steps, a few seconds each.
- **model**: Medium (music + SFX) · Small Music / Small SFX are lighter.
- **steps** 8 · **cfg** 1

## Inside the subgraph
- lcm / simple
- Seed: random. To keep one: *Sample* → fixed.
- Text encoder: *Load text encoder* (t5gemma).

## Routine
1. Batch 4–8 at the final length, keep the best.
2. Fix the seed, adjust the prompt.
3. For a loop, cut intro and outro and crossfade the ends.

Licence: Stability Community License (commercial use under $1M yearly revenue)."""
    return g.workflow(guide, "audio/stable_audio_3")


# ---------------------------------------------------------------- MiniMax Music 3
def mm3():
    g = Graph("Mine's MiniMax Music 3")
    caption = """Global Metadata: Bright J-pop, anime opening style. 150 BPM, E major. Energetic and hopeful, building to a big final chorus. Polished modern anime soundtrack production, wide stereo.

Vocal Details: Clear bright female lead vocal, confident and emotional, stacked harmonies in the chorus.

Arrangement: Driving electric guitars, bouncy bass, fast pop drums, sparkling piano and synth bells, string stabs in the chorus. Intro: piano and guitar riff. Chorus: full band with strings. Outro: guitar riff rings out."""
    lyrics = "[Intro]\n\n[Verse]\nRunning through the morning light\nEvery window shining bright\n\n[Pre-Chorus]\nHold on, hold on to the sky\n\n[Chorus]\nWe're flying higher than before\nOpen every closing door\nSing it louder, never stop\nWe'll make it to the top\n\n[Instrumental]\n\n[Chorus]\nWe're flying higher than before\nOpen every closing door\nSing it louder, never stop\nWe'll make it to the top\n\n[Outro]\n"
    g.node("unet", "UNETLoader", "Load MiniMax Music 3 model", widgets=[("unet_name", "COMBO", "minimax_music3_dit_fp16.safetensors"), ("weight_dtype", "COMBO", "default")],
           outputs=[("MODEL", "MODEL")], color=BROWN, h=140)
    g.node("clip", "CLIPLoader", "Load text encoder", widgets=[("clip_name", "COMBO", "minimax_music3_text_encoder_pruned_int8_convrot.safetensors"), ("type", "COMBO", "minimax"), ("device", "COMBO", "default")],
           outputs=[("CLIP", "CLIP")], h=160)
    g.node("vae", "VAELoader", "Load VAE", widgets=[("vae_name", "COMBO", "minimax_music3_dav.safetensors")], outputs=[("VAE", "VAE")], h=100)
    g.node("seed", "SeedNode", "Seed", widgets=[("seed", "INT", 0, "randomize")], outputs=[("seed", "INT")], h=120)
    g.node("enc", "MiniMaxMusic3TextEncode", "Encode caption and lyrics", sockets=[("clip", "CLIP")],
           widgets=[("caption", "STRING", caption), ("lyrics", "STRING", lyrics), ("seed", "INT", 0, "randomize"),
                    ("max_duration", "FLOAT", 120.0), ("cfg_scale", "FLOAT", 1.7), ("top_k", "INT", 50)],
           outputs=[("CONDITIONING", "CONDITIONING"), ("seconds", "FLOAT")], color=GREEN, multiline=(1, 2, 3))
    g.node("neg", "ConditioningZeroOut", "Empty negative", sockets=[("conditioning", "CONDITIONING")], outputs=[("CONDITIONING", "CONDITIONING")], h=80)
    g.node("lat", "EmptyMiniMaxMusic3LatentAudio", "Empty latent of that length", widgets=[("seconds", "FLOAT", 120.0), ("batch_size", "INT", 1)],
           outputs=[("LATENT", "LATENT")], h=120)
    g.node("ks", "KSampler", "Sample", sockets=[("model", "MODEL"), ("positive", "CONDITIONING"), ("negative", "CONDITIONING"), ("latent_image", "LATENT")],
           widgets=[("seed", "INT", 0, "randomize"), ("steps", "INT", 30), ("cfg", "FLOAT", 1.7), ("sampler_name", "COMBO", "euler"),
                    ("scheduler", "COMBO", "simple"), ("denoise", "FLOAT", 1.0)], outputs=[("LATENT", "LATENT")], color=BROWN, h=320)
    g.node("dec", "VAEDecodeAudio", "Decode audio", sockets=[("samples", "LATENT"), ("vae", "VAE")], outputs=[("AUDIO", "AUDIO")], h=100)
    g.node("dect", "VAEDecodeAudioTiled", "Decode audio (tiled)", sockets=[("samples", "LATENT"), ("vae", "VAE")],
           widgets=[("tile_size", "INT", 1536), ("overlap", "INT", 64)], outputs=[("AUDIO", "AUDIO")], h=140)
    g.node("sw", "ComfySwitchNode", "Switch: tiled decode", sockets=[("on_false", "*"), ("on_true", "*")],
           widgets=[("switch", "BOOLEAN", True)], outputs=[("output", "*")], h=140)

    g.link("clip", 0, "enc", "clip"); g.link("seed", 0, "enc", "seed"); g.link("seed", 0, "ks", "seed")
    g.link("enc", 0, "neg", "conditioning"); g.link("enc", 1, "lat", "seconds")
    g.link("unet", 0, "ks", "model"); g.link("enc", 0, "ks", "positive"); g.link("neg", 0, "ks", "negative"); g.link("lat", 0, "ks", "latent_image")
    g.link("ks", 0, "dec", "samples"); g.link("vae", 0, "dec", "vae"); g.link("ks", 0, "dect", "samples"); g.link("vae", 0, "dect", "vae")
    g.link("dec", 0, "sw", "on_false"); g.link("dect", 0, "sw", "on_true")

    g.promote("caption", "caption", "STRING", [("enc", "caption")], caption)
    g.promote("lyrics", "lyrics", "STRING", [("enc", "lyrics")], lyrics)
    g.promote("max_duration", "max duration (seconds)", "FLOAT", [("enc", "max_duration")], 120.0)
    g.promote("unet_name", "model", "COMBO", [("unet", "unet_name")], "minimax_music3_dit_fp16.safetensors")
    g.promote("steps", "steps", "INT", [("ks", "steps")], 30)
    g.promote("switch", "tiled decode", "BOOLEAN", [("sw", "switch")], True)

    g.layout([("Models", [["unet", "clip", "vae", "seed"]]),
              ("Prompt", [["enc", "neg"]]),
              ("Sampling", [["lat", "ks"]]),
              ("Decode", [["dec", "dect", "sw"]])])
    g.output("sw", 0, "audio", "AUDIO")
    guide = """# Guide

## Prompt
- **caption**, three parts:
  - *Global Metadata*: genre, BPM, key, mood arc, production.
  - *Vocal Details*: voice, timbre, delivery, harmonies.
  - *Arrangement*: instruments, groove, what each section does.
- **lyrics**: section tags `[Intro]` `[Verse]` `[Pre-Chorus]` `[Chorus]` `[Instrumental]` `[Solo]` `[Bridge]` `[Outro]`, then the words. Tags set the structure; keep it out of the words.
- The song ends when the sections run out. Few sections = a short clip.
- Not for instrumentals: it adds voice. Use Stable Audio 3 for BGM.

## Settings
- **max duration (seconds)**: 120 · upper limit, up to about 300.
- **model**: fp16 · int8 for less VRAM
- **steps**: 30
- **tiled decode**: on · less VRAM, slightly slower. Off on large GPUs.

## Inside the subgraph
- euler / simple · cfg 1.7 (also *cfg_scale* 1.7 in *Encode caption and lyrics*)
- Seed: random. To keep one: *Seed* → fixed.
- Model files: the *Load …* nodes.

## Routine
1. Write caption and lyrics with every section you want.
2. Run 2–3 seeds, fix the best, then adjust the caption.

About 1–3 min per song on 16 GB. Licence: MiniMax Community License (commercial use under $20M yearly revenue)."""
    return g.workflow(guide, "audio/minimax_music3")


if __name__ == "__main__":
    out = sys.argv[1]
    for name, wf in (("Mine's YuE2", yue2()), ("Mine's Stable Audio 3", sa3()), ("Mine's MiniMax Music 3", mm3())):
        with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(wf, f, indent=2, ensure_ascii=False)
        sg = wf["definitions"]["subgraphs"][0]
        print(name, "nodes", len(sg["nodes"]), "links", len(sg["links"]), "groups", [(x["title"], x["bounding"]) for x in sg["groups"]])
