import whisper
import ffmpeg
import yaml
import json
import glob
import shutil
import os

with open('./config.yaml', 'r') as file:
    config = yaml.safe_load(file)

class Script:
    """
    A Movie Script.
    """
    scripts_path = os.path.join(config['backend']['workdir'], 'userdata', 'scripts')

    def __init__(self, name) -> None:
        self.name = name
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)

    @property
    def path(self):
        return os.path.join(self.scripts_path, self.name)

    @property
    def video_filename(self):
        return os.path.join(self.path, 'video.mp4')

    @property
    def audio_filename(self):
        return os.path.join(self.path, 'audio.mp3')

    @property
    def transcript_filename(self):
        return os.path.join(self.path, 'transcript.json')

    @property
    def log_filename(self):
        return os.path.join(self.path, 'log.txt')

    # @property
    # def script_filename(self):
    #     return os.path.join(self.path, 'file.txt')  # FIXME: The originally written script

    @classmethod
    def list(cls):
        return [
            os.path.basename(os.path.normpath(path))
            for path in glob.glob(os.path.join(cls.scripts_path, '*'))]  # FIXME: Must only return directories

    @classmethod
    def delete(cls, name):
        shutil.rmtree(Script(name).path)
        return name

    @classmethod
    def ingest(cls, video_filename, name=None, replace=False):
        if not name:
            name = os.path.basename(os.path.splitext(video_filename)[0])
            print(f'No name provided, using name "{name}"')
        if name in cls.list():
            if replace:
                Script.delete(name)
            else:
                raise ValueError(f'Script with name "{name}" already exists')
        print('Ingesting...', name, video_filename)
        try:
            script = Script(name)
            with open(video_filename, 'rb') as f:
                script.write_video(f.read())
            script.extract_transcript()
        except Exception as e:
            Script.delete(name)  # Clean aborted work
            raise

    def write_video(self, video_binary):
        print('Writing...', len(video_binary))
        tmp_filename = self.video_filename + '-tmp'
        with open(tmp_filename, 'wb') as file:
            file.write(video_binary)
        print('Transcoding...', self.video_filename)
        ffmpeg_process = (
            ffmpeg.FFmpeg()
                .option("y")
                .input(tmp_filename)
                .output(self.video_filename))
        ffmpeg_process.execute()
        os.remove(tmp_filename)

    def extract_transcript(self, whisper_model='large'):
        print('Preparing...')
        ffmpeg_process = (
            ffmpeg.FFmpeg()
                .option("y")
                .input(self.video_filename)
                .output(self.audio_filename))
        # @ffmpeg_process.on("start")
        # def on_start(arguments: list[str]):
        #     print("arguments:", arguments)
        # @ffmpeg_process.on("progress")
        # def on_progress(progress: ffmpeg.Progress):
        #     print(progress)
        print('Extracting audio...', self.audio_filename)
        ffmpeg_process.execute()
        print('Loading audio...')
        model = whisper.load_model(whisper_model)
        print('Transcribing...', whisper_model)
        transcript = model.transcribe(self.audio_filename)  # TODO: use verbose=True to get progress ? https://github.com/openai/whisper/discussions/850#discussioncomment-7850096
        print('Stripping transcript...')
        transcript = [
            {
                "id": segment["id"],
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"]
            }
            for segment in transcript.get("segments", [])
        ]
        print('Writing stripped transcript...')
        with open(self.transcript_filename, 'w') as file:
            json.dump(transcript, file)

    def apply_transcript_corrections(self, corrections):
        pass  # TODO
