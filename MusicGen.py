import wave
import struct
import math

# ---------- SETTINGS ----------
sample_rate = 44100
tempo = 70
beat = 60 / tempo
duration = 60  # seconds
output_file = "Assets/Sounds/Music/glacial_ambient.wav"

# Note frequencies
NOTES = {
    "C":261.63, "D":293.66, "E":329.63, "F":349.23,
    "G":392.00, "A":440.00, "Bb":466.16
}

# Chord progression
CHORDS = [
    ("D","F","A"),
    ("Bb","D","F"),
    ("F","A","C"),
    ("C","E","G")
]

# Sparse melody
MELODY = ["A","D","F","E"]

# ---------- SOUND FUNCTIONS ----------

def sine(freq, t):
    return math.sin(2 * math.pi * freq * t)

def piano_envelope(t, length):
    """Fast attack, exponential decay"""
    if t < 0:
        return 0
    return math.exp(-3 * t / length)

def pad_envelope(t):
    """Slow evolving pad motion"""
    return 0.6 + 0.4 * math.sin(2 * math.pi * 0.02 * t)

# ---------- AUDIO GENERATION ----------

total_samples = int(sample_rate * duration)
print("started")
with wave.open(output_file, 'w') as wf:

    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)

    for i in range(total_samples):

        t = i / sample_rate

        # ----- PAD CHORDS -----
        chord_index = int((t / (beat*8)) % len(CHORDS))
        chord = CHORDS[chord_index]

        pad = 0
        for note in chord:
            pad += sine(NOTES[note]/2, t)

        pad = pad / 3
        pad *= 0.3
        pad *= pad_envelope(t)

        # ----- MELODY -----
        melody_index = int((t / (beat*2)) % len(MELODY))
        note = MELODY[melody_index]

        note_start = int(t/(beat*2))*(beat*2)
        local_time = t - note_start

        melody = sine(NOTES[note], t)
        melody *= piano_envelope(local_time, beat*2)
        melody *= 0.6

        # ----- COMBINE -----
        sample = pad + melody
        sample = max(-1, min(1, sample))

        wf.writeframes(struct.pack('<h', int(sample*32767)))

print("Soundtrack generated:", output_file)