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

@app.route("/api/script/")
def api_script():
    return core.Script.list()

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

@app.route("/api/script/<string:script_id>/transcript", methods=["POST"])
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
