import core
import celery
import yaml

app = celery.Celery(__name__,
    broker=core.config['backend']['redis_broker_url'],
    backend=core.config['backend']['redis_backend_url'])

@app.task(bind=True)
def ingest_script(self, name):
    """
    Start celery worker task on movie ingestion process.
    """
    script = core.Script(name)
    self.update_state(state='PROGRESS', meta={'step': 'Extracting transcript'})  # make state available to api (flask app)
    script.extract_transcript()
    self.update_state(state='DONE', meta={'step': 'Done'})  # make state available to api (flask app)
