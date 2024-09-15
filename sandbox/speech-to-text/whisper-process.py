import whisper
import ffmpeg
import os

audio_file = "output.mp3"

ffmpeg_process = (
    ffmpeg.FFmpeg()
    .option("y")
    .input("/Users/damien/Downloads/LA SOUPE AUX CHOUX - Extrait #1 ＂Concours de pets＂ - Louis de Funès ⧸ Jean Carmet [utUC0BXJvfg].mp4")
    .output(
        audio_file
    )
    # .output(
    #     "pipe:1",
    #     # {"codec:a": "pcm_s16le"},
    #     vn=None,
    #     f="mp3",
    # )
)
# import wave, io
# bytes = ffmpeg_process.execute()
# with wave.open(io.BytesIO(bytes), "rb") as wave_file:
#     print("Sample width in bytes:", wave_file.getsampwidth())
#     print("Sampling frequency:", wave_file.getframerate())
#     print("Number of frames:", wave_file.getnframes())

@ffmpeg_process.on("start")
def on_start(arguments: list[str]):
    print("arguments:", arguments)

@ffmpeg_process.on("progress")
def on_progress(progress: ffmpeg.Progress):
    print(progress)

print('Extracting audio...')
ffmpeg_process.execute()
print('Loading audio...')
model = whisper.load_model("large")
print('Transcribing...')
result = model.transcribe(audio_file)
os.unlink(audio_file)
print(result)

for segment in result['segments']:
    print(f'{segment["start"]} -> {segment["end"]}: {segment["text"]}')
