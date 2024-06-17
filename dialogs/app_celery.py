import core
import celery
import yaml

app = celery.Celery(__name__,
    broker=core.config['backend']['celery']['broker_url'],
    backend=core.config['backend']['celery']['broker_url'])  # backend = broker, in our case


@app.task(bind=True)
def ingest_script(self, name):
    """
    Start celery worker task on movie ingestion process.
    """
    script = core.Script(name)
    self.update_state(state='PROGRESS', meta={'step': 'Uploading video'})
    script.upload_video(binary=...)
    self.update_state(state='PROGRESS', meta={'step': 'Extracting transcript'})  # make state available to api (flask app)
    script.extract_transcript()
    self.update_state(state='PROGRESS', meta={'step': 'Extracting transcript'})  # make state available to api (flask app)
