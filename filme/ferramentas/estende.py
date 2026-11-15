#!/usr/bin/env python3
"""Emenda: o arquivo que já está no projeto fica INTACTO até `corte` s; daí em diante entra o render novo, no mesmo volume.
  estende.py <antigo.wav> <novo render.wav> <saida.wav> <corte em s>"""
import sys, wave, numpy as np
def le(p):
    w = wave.open(p); x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float).reshape(-1, w.getnchannels()) / 32767; return x, w.getframerate(), w.getnchannels()
a, sr, ca = le(sys.argv[1]); b, sr2, cb = le(sys.argv[2]); corte = float(sys.argv[4]); assert sr == sr2 and ca == cb, (sr, sr2, ca, cb)
rms = lambda x: float(np.sqrt((x ** 2).mean()))
j0, j1 = int((corte - 35) * sr), int(corte * sr); g = rms(a[j0:j1]) / rms(b[j0:j1])          # o render novo pode ter saído com outro ganho global
nx = sr; i0 = int(corte * sr); w = np.linspace(0, 1, nx)[:, None]                              # crossfade linear de 1 s
out = np.concatenate([a[:i0], a[i0:i0 + nx] * (1 - w) + b[i0:i0 + nx] * g * w, b[i0 + nx:] * g])
assert np.array_equal(out[:i0], a[:i0])
pk = np.abs(out).max(); assert pk <= 1.0, pk
wv = wave.open(sys.argv[3], "wb"); wv.setnchannels(ca); wv.setsampwidth(2); wv.setframerate(sr); wv.writeframes((np.clip(out, -1, 1) * 32767).round().astype("<i2").tobytes()); wv.close()
print(f"{sys.argv[3].split('/')[-2]}/{sys.argv[3].split('/')[-1]}: {len(out) / sr:g} s; ganho do trecho novo ×{g:.3f}; pico {pk:.2f}; trecho novo rms {20 * np.log10(rms(out[int(226 * sr):])):.1f} dB vs mural antigo {20 * np.log10(rms(a[int(226 * sr):int(235 * sr)])):.1f} dB")
