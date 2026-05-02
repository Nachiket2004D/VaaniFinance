import os
import requests
import base64
from dotenv import load_dotenv
load_dotenv()
KEY = os.getenv('SARVAM_API_KEY')
print(f'API Key found: {KEY is not None}')
url = 'https://api.sarvam.ai/text-to-speech'
payload = {
    'inputs': ['Hello, welcome to XYZ Bank!'],
    'target_language_code': 'en-IN',
    'speaker': 'arya',
    'pitch': 0,
    'pace': 1.0,
    'loudness': 1.5,
    'speech_sample_rate': 22050,
    'enable_preprocessing': True,
    'model': 'bulbul:v2'
}
headers = {
    'Content-Type': 'application/json',
    'api-subscription-key': KEY
}
response = requests.post(url, headers=headers, json=payload)
print(f'Status Code: {response.status_code}')
print(f'Response: {response.text[:300]}')
if response.status_code == 200:
    result = response.json()
    audio_bytes = base64.b64decode(result['audios'][0])
    with open('test_output.wav', 'wb') as f:
        f.write(audio_bytes)
    print('TTS WORKS! Audio saved!')
else:
    print('TTS FAILED!')
