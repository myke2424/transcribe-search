# Transcription search
Transcribe video to text and get timestamps for keywords and phrase search results.
<br>
I created this because some professors upload their lecture recordings to google drive with no transcription. This way, I can use this to search the recording for keywords and get the corresponding timestamps, so I don't have to find the points in the recording manually
## Tech-stack:
```
Python3.8
```

## Hard dependencies
Project uses Google Speech-to-Text API, it requires the following environment variable. 
```
GOOGLE_APPLICATION_CREDENTIALS=<credentials.json file>
```

Pricing depends on usage: https://cloud.google.com/speech-to-text/pricing

## Install from requirements
```
python3.8 -m pip install -r requirements.txt
```

## Install from poetry
```
poetry install
```
Made this project because some profs upload their lecture recordings to google drive, with no tranascription.
This way, I can use this to search the recording for keywords and get the corresponding timestamps, so I don't have to manually find the points in the recording! :)