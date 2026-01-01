"""Generate placeholder WAV sound effects for Mines Arena.
Creates: tick.wav, click.wav, explosion.wav, win.wav, lose.wav, tie.wav
Uses only Python stdlib (wave, struct, math, random).
Run: python generate_sfx.py
"""
import wave
import struct
import math
import random
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'sfx')
os.makedirs(OUT_DIR, exist_ok=True)

SAMPLE_RATE = 44100

def write_wave(path, samples, sampwidth=2, nchannels=1, framerate=SAMPLE_RATE):
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        # clip and pack
        max_amp = 2**(8*sampwidth - 1) - 1
        for s in samples:
            val = int(max(-1.0, min(1.0, s)) * max_amp)
            wf.writeframes(struct.pack('<h', val))

def sine(freq, t):
    return math.sin(2 * math.pi * freq * t)

def envelope(t, length, attack=0.001, decay=0.2):
    if t < attack:
        return t/attack
    if t > length - decay:
        return max(0.0, (length - t)/decay)
    return 1.0

def generate_click(path):
    dur = 0.07
    samples = []
    for i in range(int(SAMPLE_RATE*dur)):
        t = i / SAMPLE_RATE
        env = envelope(t, dur, attack=0.001, decay=0.04)
        val = 0.9 * env * (0.6 * sine(1800, t) + 0.4 * sine(2400, t))
        samples.append(val)
    write_wave(path, samples)

def generate_tick(path):
    dur = 0.05
    samples = []
    for i in range(int(SAMPLE_RATE*dur)):
        t = i / SAMPLE_RATE
        env = envelope(t, dur, attack=0.0005, decay=0.03)
        val = 0.5 * env * sine(1200, t)
        samples.append(val)
    write_wave(path, samples)

def generate_explosion(path):
    dur = 0.9
    samples = []
    for i in range(int(SAMPLE_RATE*dur)):
        t = i / SAMPLE_RATE
        # white noise
        n = random.uniform(-1, 1)
        env = math.exp(-3.0 * t)  # decay
        # low-pass-ish by mixing with a sine for thud
        thud = 0.6 * sine(120 + 80 * math.exp(-2.0 * t), t)
        val = env * (0.9 * n + thud)
        samples.append(val)
    write_wave(path, samples)

def generate_win(path):
    dur = 0.8
    samples = []
    for i in range(int(SAMPLE_RATE*dur)):
        t = i / SAMPLE_RATE
        # ascending arpeggio
        f1 = 440 * (1 + 0.5 * t)  # A4 -> up
        f2 = f1 * 1.2599
        f3 = f1 * 1.4983
        env = envelope(t, dur, attack=0.01, decay=0.25)
        val = 0.6 * env * (0.6 * sine(f1, t) + 0.3 * sine(f2, t) + 0.1 * sine(f3, t))
        samples.append(val)
    write_wave(path, samples)

def generate_lose(path):
    dur = 0.8
    samples = []
    for i in range(int(SAMPLE_RATE*dur)):
        t = i / SAMPLE_RATE
        # descending
        f1 = 660 * (1 - 0.5 * t)
        f2 = f1 * 0.8
        env = envelope(t, dur, attack=0.01, decay=0.3)
        val = 0.6 * env * (0.7 * sine(f1, t) + 0.3 * sine(f2, t))
        samples.append(val)
    write_wave(path, samples)

def generate_tie(path):
    dur = 0.6
    samples = []
    for i in range(int(SAMPLE_RATE*dur)):
        t = i / SAMPLE_RATE
        env = envelope(t, dur, attack=0.005, decay=0.12)
        # gentle bell (inharmonic)
        val = 0.5 * env * (0.6 * sine(880, t) + 0.3 * sine(1320, t) * math.sin(2*math.pi*0.5*t))
        samples.append(val)
    write_wave(path, samples)

if __name__ == '__main__':
    files = {
        'tick.wav': generate_tick,
        'click.wav': generate_click,
        'explosion.wav': generate_explosion,
        'win.wav': generate_win,
        'lose.wav': generate_lose,
        'tie.wav': generate_tie,
    }
    for name, gen in files.items():
        p = os.path.join(OUT_DIR, name)
        print('Generating', p)
        gen(p)
    print('Done.')
