# -*- coding: utf-8 -*-

from pydub import AudioSegment

def wav_to_pcm(input_wav, output_pcm, sample_rate=16000, channels=1):
    # 加载 WAV 文件
    audio = AudioSegment.from_wav(input_wav)
    
    # 设置采样率和声道
    audio = audio.set_frame_rate(sample_rate).set_channels(channels)
    
    # 导出为 PCM (s16le 原始格式)
    audio.export(output_pcm, format="raw")


# 示例用法
input_wav = "output.wav"  # 输入的 WAV 文件路径
output_pcm = "output.pcm"  # 输出的 PCM 文件路径

wav_to_pcm(input_wav, output_pcm)

