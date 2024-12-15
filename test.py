import os
import sys
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime, sleep
import _thread as thread
from pydub import AudioSegment
import subprocess
import threading
import socket
from concurrent.futures import ThreadPoolExecutor


# 定义常量
HOST = "192.168.0.100"
# HOST = "192.168.8.100"
PORT = 8080
# url 前缀
URL_PREFIX = "http://192.168.0.100/python/"

def handle_client(conn, addr, client_id):
    try:
        while True:
            # 判断是否存在demo.pcm文件
            if not os.path.exists("demo.pcm"):
                print("demo.pcm not found, waiting...")
                sleep(1)
                continue
            subprocess.check_output(["rm", "-rf","demo1.pcm"])

            # copy demo.pcm to demo1.pcm
            subprocess.check_output(["cp", "demo.pcm", "demo1.pcm"])
            # 删除demo.pcm文件
            subprocess.check_output(["rm", "-rf","demo.pcm"])
            # 发送URL_PREFIX/demo1.pcm link给客户端
            url = URL_PREFIX + "demo1.pcm"
            conn.sendall(url.encode("utf-8"))
            

    except subprocess.CalledProcessError as e:
        print(f"Error during FFmpeg execution: {e}")

# 主线程监听并接受客户端连接
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Server listening on {HOST}:{PORT}...")
        s.setblocking(False)

        with ThreadPoolExecutor(max_workers=5) as executor:
            client_id = 0
            while True:
                try:
                    conn, addr = s.accept()
                    client_id += 1
                    print(f"New connection from {addr}, client ID: {client_id}")
                    executor.submit(handle_client, conn, addr, client_id)
                except BlockingIOError:
                    pass  # No new connections, continue
if __name__ == "__main__":
            # 接参数IP地址
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    main()