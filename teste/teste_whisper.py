import whisper

model = whisper.load_model("medium")
result = model.transcribe("oalienista_1_machadodeassis_64kb.spx")
print(result["text"])
