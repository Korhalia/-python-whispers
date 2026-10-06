import math
import wave
import struct
import os
import random
import sys

song_type = sys.argv[1] if len(sys.argv) > 1 else "long_gospel"

if song_type == "long_gospel":
    filename = "long_gospel_song.wav"
    tempo = 90
    duration = 180  # 3 minutes
    notes = [261, 294, 330, 349, 392, 440, 392, 349]

elif song_type == "gospel":
    filename = "gospel_song.wav"
    tempo = 90
    duration = 60
    notes = [261, 294, 330, 349, 392, 440, 392, 349]

elif song_type == "commercial":
    filename = "commercial_song.wav"
    tempo = 120
    duration = 15
    notes = [262, 330, 392, 523]

else:
    print("Unknown song type.")
    sys.exit()

SAMPLE_RATE = 44100
BPM = 120
BEAT = 60 / BPM
BARS = 32
SONG_LENGTH = BARS * 4 * BEAT

OUTPUT = "static/music/halloween_dance.wav"

os.makedirs("static/music", exist_ok=True)

random.seed(7)

# Musical notes
NOTES = {
    "A2": 110.00,
    "C3": 130.81,
    "D3": 146.83,
    "E3": 164.81,
    "F3": 174.61,
    "G3": 196.00,
    "A3": 220.00,
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "F4": 349.23,
    "G4": 392.00,
    "A4": 440.00,
    "C5": 523.25,
}

# Dark dance chord progression
CHORDS = [
    [NOTES["A3"], NOTES["C4"], NOTES["E4"]],
    [NOTES["F3"], NOTES["A3"], NOTES["C4"]],
    [NOTES["C3"], NOTES["E3"], NOTES["G3"]],
    [NOTES["G3"], NOTES["A3"], NOTES["D4"]],
]

# Original vocal hook
VOCAL_HOOK = [
    ("A3", 1),
    ("C4", 1),
    ("E4", 1),
    ("C4", 1),
    ("A3", 1),
    ("C4", 1),
    ("D4", 1),
    ("E4", 1),
    ("G4", 2),
    ("E4", 1),
    ("D4", 1),
]

# Vowels used as synthetic vocal sounds
VOWELS = ["ah", "oh", "ah", "mm", "oh", "ah"]


def sine(frequency, time):
    return math.sin(2 * math.pi * frequency * time)


def envelope(position, duration):
    attack = min(0.04, duration * 0.2)
    release = min(0.12, duration * 0.3)

    if position < attack:
        return position / attack

    if position > duration - release:
        return max(0, (duration - position) / release)

    return 1.0


def drum_kick(time_in_beat):
    if time_in_beat < 0.18:
        frequency = 120 - 70 * (time_in_beat / 0.18)
        volume = 0.85 * (1 - time_in_beat / 0.18)
        return sine(frequency, time_in_beat) * volume
    return 0


def drum_snare(time_in_beat):
    if time_in_beat < 0.15:
        noise = random.uniform(-1, 1)
        volume = 0.45 * (1 - time_in_beat / 0.15)
        return noise * volume
    return 0


def drum_hat(time_in_beat):
    if time_in_beat < 0.045:
        noise = random.uniform(-1, 1)
        volume = 0.16 * (1 - time_in_beat / 0.045)
        return noise * volume
    return 0


def bass_sound(frequency, position, duration):
    env = envelope(position, duration)

    fundamental = sine(frequency, position)
    second_harmonic = sine(frequency * 2, position) * 0.25

    return (fundamental + second_harmonic) * env * 0.30


def vocal_sound(frequency, position, duration, vowel):
    """
    Creates a low synthetic vocal tone using harmonics.
    This is vocal-like, not a realistic human singing voice.
    """

    env = envelope(position, duration)

    fundamental = sine(frequency, position)
    harmonic_2 = sine(frequency * 2, position) * 0.45
    harmonic_3 = sine(frequency * 3, position) * 0.22
    harmonic_4 = sine(frequency * 4, position) * 0.12

    # Slightly different tone for each vowel
    if vowel == "oh":
        tone = fundamental + harmonic_2 * 0.8 + harmonic_3 * 0.15
    elif vowel == "mm":
        tone = fundamental * 0.8 + harmonic_2 * 0.65 + harmonic_3 * 0.35
    else:
        tone = fundamental + harmonic_2 + harmonic_3 + harmonic_4

    # Add gentle vibrato
    vibrato = 1 + 0.012 * math.sin(2 * math.pi * 5 * position)

    return tone * env * vibrato * 0.34


def get_vocal_note(current_time):
    hook_length = sum(beats for _, beats in VOCAL_HOOK) * BEAT
    hook_time = current_time % hook_length

    elapsed = 0
    syllable_index = 0

    for note_name, beats in VOCAL_HOOK:
        duration = beats * BEAT

        if elapsed <= hook_time < elapsed + duration:
            position = hook_time - elapsed
            return (
                NOTES[note_name],
                position,
                duration,
                VOWELS[syllable_index % len(VOWELS)]
            )

        elapsed += duration
        syllable_index += 1

    return None


total_samples = int(SONG_LENGTH * SAMPLE_RATE)

with wave.open(OUTPUT, "w") as audio:
    audio.setnchannels(1)
    audio.setsampwidth(2)
    audio.setframerate(SAMPLE_RATE)

    for sample_number in range(total_samples):
        time = sample_number / SAMPLE_RATE
        beat_number = time / BEAT
        beat_position = time % BEAT

        # Four beats per bar
        beat_in_bar = int(beat_number) % 4
        bar_number = int(beat_number // 4)

        # Intro is quieter; chorus sections are louder
        if bar_number < 4:
            energy = 0.45
        elif 12 <= bar_number < 20:
            energy = 1.0
        else:
            energy = 0.78

        sound = 0.0

        # Kick on every beat
        sound += drum_kick(beat_position) * energy

        # Snare on beats 2 and 4
        if beat_in_bar in [1, 3]:
            sound += drum_snare(beat_position) * energy

        # Hi-hats on offbeats
        half_beat_position = (time % (BEAT / 2))
        if beat_in_bar in [0, 1, 2, 3]:
            sound += drum_hat(half_beat_position) * energy

        # Chord pad
        chord_index = bar_number % len(CHORDS)
        chord = CHORDS[chord_index]

        for frequency in chord:
            sound += sine(frequency / 2, time) * 0.045 * energy

        # Bass on each beat
        bass_notes = [NOTES["A2"], NOTES["F3"], NOTES["C3"], NOTES["G3"]]
        bass_frequency = bass_notes[chord_index]

        sound += bass_sound(
            bass_frequency,
            beat_position,
            BEAT
        ) * energy

        # Synthetic low female-style vocal hook
        vocal = get_vocal_note(time)

        if vocal:
            frequency, vocal_position, vocal_duration, vowel = vocal

            # Keep the vocal deep and smooth
            sound += vocal_sound(
                frequency,
                vocal_position,
                vocal_duration,
                vowel
            ) * energy

        # Atmospheric spooky tone
        spooky_frequency = 55 + 3 * math.sin(time * 0.4)
        sound += sine(spooky_frequency, time) * 0.025

        # Prevent clipping
        sound = max(-1.0, min(1.0, sound))

        audio.writeframes(
            struct.pack("<h", int(sound * 32767))
        )

print(f"Created: {OUTPUT}")
