import os
import torch
import soundfile as sf
from transformers import AutoProcessor, MusicgenForConditionalGeneration

model_id = "facebook/musicgen-small"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading MusicGen on {device}...")
processor = AutoProcessor.from_pretrained(model_id)
model = MusicgenForConditionalGeneration.from_pretrained(model_id).to(device)

prompt = "Upbeat Halloween dance music with playful spooky synths and crisp electronic drums"
inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(device)

print("Generating music...")
with torch.no_grad():
    audio = model.generate(**inputs, max_new_tokens=256)

os.makedirs("static/music", exist_ok=True)
sf.write(
    "static/music/generated.wav",
    audio[0, 0].cpu().numpy(),
    model.config.audio_encoder.sampling_rate,
)

print("Saved to static/music/generated.wav")
