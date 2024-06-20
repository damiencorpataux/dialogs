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

@app.route('/api/project', methods=['POST'])
def api_project_post():
        if 'file' not in flask.request.files:
            return flask.jsonify({'error': 'No file part'}), 400

        file = flask.request.files['file']
        if file.filename == '':
            return flask.jsonify({'error': 'No selected file'}), 400

        # Validate file
        allowed_extra_extensions = ['mkv']
        file_is_valid = (
            file
            and file.mimetype.startswith('video/')
            or file.mimetype.startswith('audio/')
            or os.path.splitext(file.filename)[1][1:] in allowed_extra_extensions)
        if not file_is_valid:
            if file and file.mimetype:
                error_message = f'Invalid file type ({file.mimetype} is not supported)'
            else:
                error_message = 'Invalid file type'
            return flask.jsonify({'error': error_message}), 400
        else:
            # Upload file in project directory
            # TODO: Factorize this in core.Project.ingest_binary(project_name, file_binary)
            project = core.Project(
                core.Project.create_name_from_filename(file.filename),
                create=True)
            tmp_file = os.path.join(
                project.path,
                'upload' + os.path.splitext(file.filename)[1])
            project.log.info(f'Writing temporary original file to %s', tmp_file)
            # Actual upload
            with open(tmp_file, 'wb') as f:
                for chunk in file.stream:
                    f.write(chunk)
            try:
                # Start ingestion process
                core.Project.ingest(tmp_file, name=project.name, overwrite=True)  # TODO: Launch ingest task using celery.
                return flask.jsonify({'message': 'File successfully uploaded'}), 200
            except Exception as e:
                return flask.jsonify({'error': str(e)}), 500
            finally:
                print(f'Removing temporary original file to "{tmp_file}"')
                os.remove(tmp_file)

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
    # FIXME: Or maybe just use sh.tail(...) as in https://stackoverflow.com/a/12523119
    #        which is not very inter-operable. For example:
    #             import sh
    #             if (n is None):
    #                 tail = sh.tail('-f', log_filename, _iter=True)
    #             else:
    #                 tail = sh.tail('-f', '-n', n, log_filename, _iter=True)
    #             tail_generator = (f"data: {line}\n\n" for line in tail)
    def tail_file(filename, n=None):
        """Stream end of a text file like like `tail -f`."""
        try:  # FIXME: Is it necessary if everything is caught in hte Actual function ?
            with open(filename, 'r') as file:
                if n is not None:
                    lines = collections.deque(file, maxlen=n)  # Read the last n lines
                    for line in lines:
                        yield f"data: {line}\n\n"
                    file.seek(0, os.SEEK_END)  # Move to the end of the file
                while True:
                    line = file.readline()
                    if not line:
                        time.sleep(0.1)  # Sleep briefly
                        continue
                    yield f"data: {line}\n\n"
        except GeneratorExit as e:
            print('Client disconnected', e)  # FIXME: Never reached ?
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
    return flask.Response(flask.stream_with_context(tail_generator), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True, threaded=True)
