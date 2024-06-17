import core
import flask
import yaml
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

# @app.route("/api/project/<script_id>/video", methods=["POST"])
# def api_script_video_upload(script_id):
#     # TODO: See ingestion using celery working in aeoe: https://bitbucket.org/damiencorpataux/unil-decanat-archive-search/src/f40f6c3d399905166338112e254e53bb09cd166c/app/api/app.py#lines-433
#     return []


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)
