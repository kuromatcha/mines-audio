"""Make a music clip loop seamlessly.

Usage: python tools/make_loop.py <in.flac> <out.flac> [fade_seconds=3]

The last fade_seconds are crossfaded (equal power) into the first ones and then cut off, so the end of the file
runs straight into its start. The output is fade_seconds shorter than the input. Needs `av` and `numpy`
(both come with ComfyUI's Python).
"""
import sys

import av
import numpy as np

if len(sys.argv) not in (3, 4):
    sys.exit(__doc__)
src, dst = sys.argv[1], sys.argv[2]
fade = float(sys.argv[3]) if len(sys.argv) == 4 else 3.0

with av.open(src) as c:
    stream = c.streams.audio[0]
    rate = stream.rate
    resampler = av.AudioResampler(format="fltp", layout="stereo", rate=rate)
    x = np.concatenate([r.to_ndarray() for f in c.decode(stream) for r in resampler.resample(f)], axis=1)

F = int(fade * rate)
if F <= 0 or 2 * F >= x.shape[1]:
    sys.exit(f"fade of {fade} s does not fit a {x.shape[1] / rate:.1f} s clip")
t = np.linspace(0.0, np.pi / 2, F, dtype=np.float32)
out = x[:, :-F].copy()
out[:, :F] = x[:, :F] * np.sin(t) + x[:, -F:] * np.cos(t)

with av.open(dst, "w") as o:
    s = o.add_stream("flac", rate=rate, layout="stereo")
    pcm = (np.clip(out, -1.0, 1.0) * 32767).astype(np.int16).T.reshape(1, -1)
    frame = av.AudioFrame.from_ndarray(pcm, format="s16", layout="stereo")
    frame.rate = rate
    for p in s.encode(frame):
        o.mux(p)
    for p in s.encode(None):
        o.mux(p)
print(f"{dst}: {out.shape[1] / rate:.1f} s loop")
