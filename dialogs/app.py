import core
import flask
import yaml
import json
import os

app = flask.Flask(__name__)

@app.route("/")
def ui():
    return flask.render_template('index.html', scripts=core.Script.list())

@app.route("/edit/<script_name>")
def ui_script_edit(script_name):
    return flask.render_template('edit.html', script=core.Script(script_name))

@app.route("/api/script")
def api_script():
    return core.Script.list()

UPLOAD_FOLDER = '/tmp'  # FIXME
@app.route('/api/script', methods=['POST'])
def api_script_post():
    if 'file' not in flask.request.files:
        return flask.jsonify({'error': 'No file part'}), 400

    file = flask.request.files['file']
    if file.filename == '':
        return flask.jsonify({'error': 'No selected file'}), 400

    if file and file.mimetype.startswith('video/'):
        tmp_file = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(tmp_file, 'wb') as f:
            for chunk in file.stream:
                f.write(chunk)
        try:
            core.Script.ingest(tmp_file)  # TODO: Launch ingest task using celery.
            os.remove(tmp_file)
        except Exception as e:
            return flask.jsonify({'error': str(e)}), 500
        return flask.jsonify({'message': 'File successfully uploaded'}), 200
    else:
        return flask.jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/script/<script_id>', methods=['DELETE'])
def api_script_delete(script_id):
    try:
        core.Script.delete(script_id)
        return flask.jsonify({'message': f'Script "{script_id}" successfully deleted'}), 200
    except Exception as e:
        return flask.jsonify({'error': str(e)}), 500

@app.route("/api/script/<script_id>/video")
def api_script_video(script_id):
    script = core.Script(script_id)
    return flask.send_from_directory(
        os.path.dirname(script.video_filename),
        os.path.basename(script.video_filename))

@app.route("/api/script/<script_id>/transcript")
def api_script_transcript(script_id):
    script = core.Script(script_id)
    return flask.send_from_directory(
        os.path.dirname(script.transcript_filename),
        os.path.basename(script.transcript_filename))

@app.route("/api/script/<script_id>/transcript", methods=["POST"])
def api_script_transcript_post(script_id):
    script = core.Script(script_id)

    if not flask.request.is_json:
        return flask.jsonify({"error": "Request body must be JSON"}), 400

    data = flask.request.get_json()

    # TODO: Check if the data is a valid transcript
    # if not core.validate_transcript(data):
    #     return flask.jsonify({"error": "Invalid transcript data"}), 400

    # Store the serialized data to disk with the given filename
    transcript_json = json.dumps(data)
    with open(script.transcript_filename, "w") as file:
        file.write(transcript_json)

    # Load the stored transcript from disk
    with open(script.transcript_filename, "r") as file:
        loaded_transcript = json.load(file)

    return flask.jsonify(loaded_transcript)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)
