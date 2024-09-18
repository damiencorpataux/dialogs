A web-app for video transcription and translation. Using whisper, ollama, flask, python and web-standards. It's a POC.
[![Dialogs demo](https://img.youtube.com/vi/DEJq_zsyxpQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=DEJq_zsyxpQ)


Quickstart
-

Clone code
```sh
git clone ...
```
Install dependencies
```sh
cd dialogs
pip install -r requirements.txt
```
Start server
```sh
cd dialogs
python3 -m app
```
Open http://localhost:9999/


Components
-
- **Core module:** Implementation of transcription project features
- **REST API:** Exposition of the core as REST endpoints, using flask
- **UI:** Plain HTML/JS, for prototyping


Ra&D
-
- Products
  - https://www.descript.com/
  - https://frame.io/
  - https://www.google.com/search?q=text+based+editing+adobe+premiere+pro

- Features
  - Speaker Diarization
    - Post: https://community.openai.com/t/how-to-identify-different-speakers-using-whisper/466219/4
    - Pyannote-audio: https://github.com/pyannote/pyannote-audio