import math
import wave
import struct
import os

SAMPLE_RATE = 44100
BPM = 100
BEAT = 60 / BPM
SONG_LENGTH = 16
OUTPUT = "static/music/song1.wav"

notes = {
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "G4": 392.00,
    "A4": 440.00,
    "C5": 523.25,
    "D5": 587.33,
    "E5": 659.25,
    "G5": 783.99,
    "A5": 880.00,
}

# Original melody: each item is (note, number of beats)
melody = [
    ("C4", 1), ("E4", 1), ("G4", 1), ("E4", 1),
    ("D4", 1), ("G4", 1), ("A4", 1), ("G4", 1),
    ("C5", 1), ("A4", 1), ("G4", 1), ("E4", 1),
    ("D4", 1), ("E4", 1), ("G4", 2),
]

# Chord progression
chords = [
    [notes["C4"], notes["E4"], notes["G4"]],
    [notes["G4"], notes["B4"] if "B4" in notes else 493.88, notes["D5"]],
    [notes["A4"], notes["C5"], notes["E5"]],
    [notes["F4"] if "F4" in notes else 349.23, notes["A4"], notes["C5"]],
]

def envelope(position, duration):
    attack = min(0.05, duration / 4)
    release = min(0.15, duration / 3)

    if position < attack:
        return position / attack

    if position > duration - release:
        return max(0, (duration - position) / release)

    return 1.0

def sine(frequency, time):
    return math.sin(2 * math.pi * frequency * time)

os.makedirs("static/music", exist_ok=True)

total_samples = int(SONG_LENGTH * SAMPLE_RATE)

with wave.open(OUTPUT, "w") as audio:
    audio.setnchannels(1)
    audio.setsampwidth(2)
    audio.setframerate(SAMPLE_RATE)

    for sample_number in range(total_samples):
        time = sample_number / SAMPLE_RATE
        beat_number = time / BEAT

        # Melody
        melody_time = time % (len(melody) * BEAT)
        current_time = 0
        melody_value = 0

        for note, beats in melody:
            note_duration = beats * BEAT

            if current_time <= melody_time < current_time + note_duration:
                note_position = melody_time - current_time
                frequency = notes[note]
                melody_value = (
                    0.42
                    * sine(frequency, note_position)
                    * envelope(note_position, note_duration)
                )
                break

            current_time += note_duration

        # Soft background chords
        chord_index = int(beat_number // 4) % len(chords)
        chord_value = 0

        for frequency in chords[chord_index]:
            chord_value += sine(frequency / 2, time) * 0.06

        # Bass note
        bass_notes = [130.81, 98.00, 110.00, 87.31]
        bass_frequency = bass_notes[chord_index]
        bass_value = sine(bass_frequency, time) * 0.16

        final_value = melody_value + chord_value + bass_value
        final_value = max(-1, min(1, final_value))

        audio.writeframes(
            struct.pack("<h", int(final_value * 32767))
        )

print(f"Song created: {OUTPUT}")
