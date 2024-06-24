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