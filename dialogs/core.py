import whisper
import ffmpeg
import yaml
import json
import glob
import shutil
import os
import logging

with open('./config.yaml', 'r') as file:
    config = yaml.safe_load(file)


class Project:
    """
    A Movie Project.
    """
    projects_path = os.path.join(config['backend']['workdir'], 'userdata', 'projects')

    def __init__(self, name, create=False) -> None:
        self.name = name
        if not os.path.exists(self.path):
            if create:
                os.makedirs(self.path, exist_ok=True)
            else:
                raise ValueError(f'{self.__class__.__name__} "{name}" does not exist')
        self.log = self.setup_logger()

    @property
    def files(self):
        return [
            os.path.basename(filename)
            for filename in glob.glob(os.path.join(self.path, '*'))]

    @property
    def path(self):
        return os.path.join(self.projects_path, self.name)

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
    # def project_filename(self):
    #     return os.path.join(self.path, 'file.txt')  # FIXME: The originally written project

    def setup_logger(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        # Check if logger singleton already has handlers to avoid adding multiple handlers
        if not logger.handlers:
            # Create file handler
            fh = logging.FileHandler(self.log_filename)
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s: %(message)s',
                '%Y-%m-%d %H:%M:%S'))
            logger.addHandler(fh)
            # Create console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s: %(name)s: %(message)s'))
            logger.addHandler(ch)
        return logger

    @classmethod
    def list(cls):
        return [
            os.path.basename(os.path.normpath(path))
            for path in glob.glob(os.path.join(cls.projects_path, '*'))]  # FIXME: Must only return directories

    @classmethod
    def delete(cls, name):
        project = Project(name)
        project.log.info(f'Deleting project "{name}"')
        shutil.rmtree(project.path)  # FIXME: Nothing should be auto-deleted !
        return name                 #        Items should be deleted one by one by the user
                                    #        and log.txt could be not deletable
    @classmethod
    def create_name_from_filename(cls, filename):
        return os.path.basename(os.path.splitext(filename)[0])

    @classmethod
    def ingest(cls, video_filename, name=None, overwrite=False):  # FIXME: arg replace -> overwrite (keep all files but overwrite video file)
        if not name:
            name = cls.create_name_from_filename(video_filename)
        project = Project(name, create=True)
        if not overwrite and os.path.exists(video_filename):
            raise ValueError(f'Project with name "{name}" already exists')
        project.log.info('Ingesting to project "%s" from video file "%s"...', name, video_filename)
        try:
            with open(video_filename, 'rb') as f:
                project.write_video_transcoded(f.read())
            project.extract_transcript()
        except Exception as e:
            project.log.exception(e)
            # Project.delete(name)  # FIXME: Don't auto-delete anything !
            raise

    def write_transcript(self, transcript):
        with open(self.transcript_filename, "w") as file:
            json.dump(transcript, file)
            # file.write(transcript_json)
        print('X'*50)
        self.log.info('Saved transcript to "%s"', self.transcript_filename)

    def write_video_transcoded(self, video_binary):
        self.log.info('Writing original video (%s bytes)...', len(video_binary))
        tmp_filename = self.video_filename + '-tmp'
        with open(tmp_filename, 'wb') as file:
            file.write(video_binary)
        self.log.info('Transcoding video to "%s"...', self.video_filename)
        ffmpeg_process = (
            ffmpeg.FFmpeg()
                .option("y")
                .input(tmp_filename)
                .output(self.video_filename))
        ffmpeg_process.execute()
        os.remove(tmp_filename)

    def extract_transcript(self, whisper_model='large'):
        self.log.info('Extracting audio to "%s"...', self.audio_filename)
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
        ffmpeg_process.execute()
        self.log.info('Loading audio...')
        model = whisper.load_model(whisper_model)
        self.log.info('Transcribing audio (model "%s")...', whisper_model)
        transcript = model.transcribe(self.audio_filename)  # TODO: use verbose=True to get progress ? https://github.com/openai/whisper/discussions/850#discussioncomment-7850096
        self.log.info('Stripping transcript...')
        transcript = [
            {
                "id": segment["id"],
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"]
            }
            for segment in transcript.get("segments", [])
        ]
        self.log.info('Writing stripped transcript...')
        with open(self.transcript_filename, 'w') as file:
            json.dump(transcript, file)
        self.log.info('Ingestion successful !')

    def apply_transcript_corrections(self, corrections):
        pass  # TODO
