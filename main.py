import ollama

import json
import requests
import io
import soundfile
import sounddevice as sd
from typing import TypedDict


class PlaySound:
    def __init__(self, output_device_name="CABLE Input") -> None:
        # 指定された出力デバイス名に基づいてデバイスIDを取得
        output_device_id = self._search_output_device_id(output_device_name)
        # 入力デバイスIDは使用しないため、デフォルトの0を設定
        input_device_id = 0
        # デフォルトのデバイス設定を更新
        sd.default.device = [input_device_id, output_device_id]

    def _search_output_device_id(
        self, output_device_name, output_device_host_api=0
    ) -> int:
        # 利用可能なデバイスの情報を取得
        devices = sd.query_devices()
        output_device_id = None
        # 指定された出力デバイス名とホストAPIに合致するデバイスIDを検索
        for device in devices:
            is_output_device_name = output_device_name in device["name"]
            is_output_device_host_api = device["hostapi"] == output_device_host_api
            if is_output_device_name and is_output_device_host_api:
                output_device_id = device["index"]
                break

        # 合致するデバイスが見つからなかった場合の処理
        if output_device_id is None:
            print("output_deviceが見つかりませんでした")
            exit()
        return output_device_id

    def play_sound(self, data, rate) -> bool:
        # 音声データを再生
        sd.play(data, rate)
        # 再生が完了するまで待機
        sd.wait()
        return True


class VoicevoxAdapter:
    URL = "http://127.0.0.1:50021/"

    # 二回postする。一回目で変換、二回目で音声合成
    def __init__(self) -> None:
        pass

    def __create_audio_query(self, text: str, speaker_id: int) -> json:
        item_data = {
            "text": text,
            "speaker": speaker_id,
        }
        response = requests.post(self.URL + "audio_query", params=item_data)
        return response.json()

    def __create_request_audio(self, query_data, speaker_id: int) -> bytes:
        a_params = {
            "speaker": speaker_id,
        }
        headers = {"accept": "audio/wav", "Content-Type": "application/json"}
        res = requests.post(
            self.URL + "synthesis",
            params=a_params,
            data=json.dumps(query_data),
            headers=headers,
        )
        print(res.status_code)
        return res.content

    def get_voice(self, text: str):
        speaker_id = 3
        query_data: json = self.__create_audio_query(text, speaker_id=speaker_id)
        audio_bytes = self.__create_request_audio(query_data, speaker_id=speaker_id)
        audio_stream = io.BytesIO(audio_bytes)
        data, sample_rate = soundfile.read(audio_stream)
        return data, sample_rate


response = ollama.chat(
    model="llama3",
    messages=[
        {
            "role": "user",
            "content": "こんにちわ！あなたはどんなことができますか？日本語で回答してください",
        },
    ],
)

print(response["message"]["content"])

input_str = response["message"]["content"]
voicevox_adapter = VoicevoxAdapter()
play_sound = PlaySound("LG HDR 4K")
data, rate = voicevox_adapter.get_voice(input_str)
play_sound.play_sound(data, rate)
