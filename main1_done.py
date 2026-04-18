import json
import time
import datetime
import webbrowser
import sys

import requests
import pyttsx3
import pyaudio
import vosk


class Speech:
    def __init__(self):
        if sys.platform.startswith('win'):
            self.tts = pyttsx3.init('sapi5')
        elif sys.platform == 'darwin':
            self.tts = pyttsx3.init('nsss')
        else:
            self.tts = pyttsx3.init()

        self.voices = self.tts.getProperty('voices')

    def set_voice(self, speaker=0):
        if not self.voices:
            return None

        voice_id = self.voices[0].id

        for count, voice in enumerate(self.voices):
            if count == speaker:
                voice_id = voice.id
                break

        return voice_id

    def text2voice(self, text='Готов', speaker=0):
        voice_id = self.set_voice(speaker)
        if voice_id is not None:
            self.tts.setProperty('voice', voice_id)

        self.tts.say(text)
        self.tts.runAndWait()


class Recognize:
    def __init__(self, model_path='model_small'):
        model = vosk.Model(model_path)
        self.record = vosk.KaldiRecognizer(model, 16000)
        self.stream = None
        self.open_stream()

    def open_stream(self):
        pa = pyaudio.PyAudio()
        self.stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )

    def listen(self):
        while True:
            data = self.stream.read(4000, exception_on_overflow=False)

            if self.record.AcceptWaveform(data) and len(data) > 0:
                answer = json.loads(self.record.Result())
                text = answer.get('text', '').strip().lower()

                if text:
                    yield text


class VoiceAssistant:
    def __init__(self):
        self.speech = Speech()
        self.recognizer = Recognize('model_small')

    def speak(self, text):
        print(f'Ассистент: {text}')
        self.speech.text2voice(text=text, speaker=1)

    def get_time(self):
        now = datetime.datetime.now().strftime('%H:%M')
        self.speak(f'Сейчас {now}')

    def get_date(self):
        today = datetime.datetime.now().strftime('%d.%m.%Y')
        self.speak(f'Сегодня {today}')

    def tell_joke(self):
        try:
            response = requests.get(
                'https://official-joke-api.appspot.com/random_joke',
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            setup = data.get('setup', 'Joke not found.')
            punchline = data.get('punchline', '')
            self.speak(f'{setup} {punchline}')

        except requests.RequestException:
            self.speak('Ошибка в запросе. Не удалось получить шутку.')

    def tell_fact(self):
        try:
            response = requests.get(
                'https://uselessfacts.jsph.pl/api/v2/facts/random?language=en',
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            fact = data.get('text', 'Fact not found.')
            self.speak(fact)

        except requests.RequestException:
            self.speak('Ошибка в запросе. Не удалось получить факт.')

    def find_word(self, text):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            self.speak('После команды find нужно сказать английское слово.')
            return

        word = parts[1].strip().lower()
        url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            meaning = data[0]['meanings'][0]['definitions'][0]['definition']
            self.speak(f'The meaning of {word} is: {meaning}')
            webbrowser.open(url)

        except requests.RequestException:
            self.speak('Ошибка в запросе. Не удалось найти запрос.')
        except (KeyError, IndexError, TypeError):
            self.speak('Запрос найден, но значение извлечь не удалось.')

    def execute_command(self, text):
        if text in ['привет', 'hello', 'hi']:
            self.speak('Привет. Готово к работе.')

        elif text in ['время', 'time']:
            self.get_time()

        elif text in ['дата', 'date']:
            self.get_date()

        elif text in ['шутка', 'joke']:
            self.tell_joke()

        elif text in ['факт', 'fact']:
            self.tell_fact()

        elif text.startswith('find '):
            self.find_word(text)

        elif text in ['закрыть', 'выход', 'stop', 'exit']:
            self.speak('Бывай. Закругляемся.')
            return False

        else:
            self.speak('Не распознана команда.')

        return True

    def run(self):
        self.speak('Starting')
        time.sleep(0.5)

        for text in self.recognizer.listen():
            print(f'Вы сказали: {text}')

            work = self.execute_command(text)
            if not work:
                break


if __name__ == '__main__':
    assistant = VoiceAssistant()
    assistant.run()
