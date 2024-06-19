import core
import flask
import yaml
import json
import time
import os
import logging

app = flask.Flask(__name__)


# UI Endpoints.

@app.route("/")
def ui():
    return flask.render_template('index.html', project_list=core.Project.list())

@app.route("/edit/<project_name>")
def ui_project_edit(project_name):
    return flask.render_template('edit.html', project=core.Project(project_name))

@app.route("/log/<project_name>")
def ui_project_log(project_name):
    return flask.render_template('log.html', project_name=project_name)

# API Endpoints.

@app.route("/api/project")
def api_project():
    return core.Project.list()

UPLOAD_FOLDER = '/tmp'  # FIXME: Make it configurable with a sensible default (use python module: tempdir ?)
@app.route('/api/project', methods=['POST'])
def api_project_post():
    if 'file' not in flask.request.files:
        return flask.jsonify({'error': 'No file part'}), 400

    file = flask.request.files['file']
    if file.filename == '':
        return flask.jsonify({'error': 'No selected file'}), 400

    if file and file.mimetype.startswith('video/'):
        tmp_file = os.path.join(UPLOAD_FOLDER, file.filename)
        # project = core.Project(core.Project.create_name_from_filename(file.filename))
        # tmp_file = os.path.join(project.path, 'video-original' + os.path.splitext(file.filename)[1])
        with open(tmp_file, 'wb') as f:
            for chunk in file.stream:
                f.write(chunk)
        try:
            core.Project.ingest(tmp_file, overwrite=True)  # TODO: Launch ingest task using celery.
            os.remove(tmp_file)
        except Exception as e:
            return flask.jsonify({'error': str(e)}), 500

        return flask.jsonify({'message': 'File successfully uploaded'}), 200
    else:
        return flask.jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/project/<project_name>', methods=['DELETE'])
def api_project_delete(project_name):
    try:
        core.Project.delete(project_name)
        return flask.jsonify({'message': f'Project "{project_name}" successfully deleted'}), 200
    except Exception as e:
        return flask.jsonify({'error': str(e)}), 500

@app.route("/api/project/<project_name>/video")
def api_project_video(project_name):
    project = core.Project(project_name)
    return flask.send_from_directory(
        os.path.dirname(project.video_filename),
        os.path.basename(project.video_filename))

@app.route("/api/project/<project_name>/transcript")
def api_project_transcript(project_name):
    project = core.Project(project_name)
    return flask.send_from_directory(
        os.path.dirname(project.transcript_filename),
        os.path.basename(project.transcript_filename))

@app.route("/api/project/<project_name>/transcript", methods=["PATCH"])
def api_project_transcript_post(project_name):
    if not flask.request.is_json:
        return flask.jsonify({"error": "Request body must be JSON"}), 400
    transcript = flask.request.get_json()
    # TODO: Check if the data is a valid transcript
    # if not core.validate_transcript(data):
    #     return flask.jsonify({"error": "Invalid transcript data"}), 400
    project = core.Project(project_name)
    project.write_transcript(transcript)
    return api_project_transcript(project_name)

@app.route("/api/project/<project_name>/files")
def api_project_files(project_name):
    project = core.Project(project_name)
    return flask.jsonify(project.files)

import collections
@app.route('/api/project/<project_name>/log')
@app.route('/api/project/<project_name>/log/<n>')
def api_project_log(project_name, n=None):
    def tail_file(filename, n=None):
        """Stream end of a text file like like `tail -f`."""
        try:  # FIXME: Is it necessary if everything is caught in hte Actual function ?
            with open(filename, 'r') as file:
                if n is not None:
                    lines = collections.deque(file, maxlen=n)  # Read the last n lines
                    for line in lines:
                        yield f"data: {line}\n\n"
                    # Move to the end of the file
                    file.seek(0, os.SEEK_END)
                while True:
                    line = file.readline()
                    if not line:
                        time.sleep(0.1)  # Sleep briefly
                        continue
                    yield f"data: {line}\n\n"
        except FileNotFoundError as e:
            print(e.__class__.__name__, e)
            yield "event: error\ndata: File not found\n\n"
        except Exception as e:
            print(e.__class__.__name__, e)
            yield f"event: error\ndata: {str(e)}\n\n"
    # Actual function
    try:
        log_filename = core.Project(project_name).log_filename
        n = int(n) if n is not None else None  # cast n (received as string by flask)
        tail_generator = tail_file(log_filename, n)
    except Exception as e:
        tail_generator = (error for error in (f"event: error\ndata: {str(e)}\n\n",))
    return flask.Response(tail_generator, mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)
