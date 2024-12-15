# -*- coding: utf-8 -*-

import subprocess

rtsp_url = "rtsp://192.168.0.214:554/live/1"
output_file = "input.wav"
capture_duration = "10"  # 捕获时间，单位为秒

command = [
    "ffmpeg",
    "-y",  # 自动覆盖已存在文件
    "-i", rtsp_url,
    "-vn",  # 不捕获视频
    "-acodec", "pcm_s16le",  # 转换为 PCM 格式
    "-ar", "16000",  # 采样率
    "-ac", "1",  # 单声道
    "-t", capture_duration,  # 捕获时间
    output_file
]

try:
    subprocess.run(command, check=True)
    print(f"Captured audio saved to {output_file}")
except subprocess.CalledProcessError as e:
    print("Error during FFmpeg execution:", e)
