# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#  本demo测试时运行的环境为：Windows + Python3.7
#  本demo测试成功运行时所安装的第三方库及其版本如下，您可自行逐一或者复制到一个新的txt文件利用pip一次性安装：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#
#  语音听写流式 WebAPI 接口调用示例 接口文档（必看）：https://doc.xfyun.cn/rest_api/语音听写（流式版）.html
#  webapi 听写服务参考帖子（必看）：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=38947&extra=
#  语音听写流式WebAPI 服务，热词使用方式：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--个性化热词，
#  设置热词
#  注意：热词只能在识别的时候会增加热词的识别权重，需要注意的是增加相应词条的识别率，但并不是绝对的，具体效果以您测试为准。
#  语音听写流式WebAPI 服务，方言试用方法：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--识别语种列表
#  可添加语种或方言，添加后会显示该方言的参数值
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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
from time import mktime
import _thread as thread
from pydub import AudioSegment
import subprocess
import threading
import socket
from concurrent.futures import ThreadPoolExecutor
import json
import threading
import time
import subprocess

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":1,"vad_eos":10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url

# 缓冲区
buffer = []

# 最大消息次数
MAX_MESSAGE_COUNT = 5
# 定义缓冲区写入文件的间隔时间（3秒）
BUFFER_FLUSH_INTERVAL = 3
# 超时（秒）
TIMEOUT = 5

# 用于记录每轮的消息计数
message_count = 0
# 超时标志
timeout_flag = False
# 轮次标志
is_new_round = True

# 将缓冲区内容写入文件的函数
def write_buffer_to_file():
    global message_count, timeout_flag, is_new_round
    while True:
        time.sleep(BUFFER_FLUSH_INTERVAL)
        
        # 如果缓冲区有内容或超时标志被触发，或达到最大回调次数
        if buffer or timeout_flag:
            result = ''.join(buffer)  # 将缓冲区中的所有内容拼接起来
            
            subprocess.check_output(["rm", "-rf", "r_content1.txt"])
            
            with open("r_content1.txt", "a+", encoding="utf-8") as f:
                f.write(result)
            subprocess.check_output(["cp", "r_content1.txt", "r_content.txt"])
            print("The result has been written to 'r_content.txt'")

            # 清空缓冲区
            buffer.clear()

            # 重置超时标志
            timeout_flag = False
            # 重置计数
            message_count = 0
            # 重置轮次标志
            is_new_round = True

# 超时计时器
def timeout_timer():
    global timeout_flag, is_new_round
    time.sleep(TIMEOUT)
    if not is_new_round:  # 如果是当前轮次
        timeout_flag = True
        print("Timeout reached, writing buffer to file.")

# 收到websocket消息的处理
def on_message(ws, message):
    global message_count, timeout_flag, is_new_round

    try:
        # 判断是否是新一轮上传音频（每轮需要重置计数）
        if is_new_round:
            # 启动超时计时器
            timeout_thread = threading.Thread(target=timeout_timer, daemon=True)
            timeout_thread.start()

            # 标记为当前音频的轮次
            is_new_round = False

        # 解析消息
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            data = json.loads(message)["data"]["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            if result == "？" or result == "。" or result == "！" or result == "":
                return
            # 打印识别的结果
            print("sid:%s call success!, data is:%s" % (sid, json.dumps(data, ensure_ascii=False)))

            # 将识别结果添加到缓冲区
            buffer.append(result)

            # 增加消息计数
            message_count += 1

            # 检查消息次数是否达到最大值
            if message_count >= MAX_MESSAGE_COUNT:
                timeout_flag = True  # 达到最大回调次数，触发写入缓冲区
                print(f"Received {MAX_MESSAGE_COUNT} messages, writing buffer to file.")

    except Exception as e:
        print("receive msg, but parse exception:", e)



# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws,a,b):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws, wsParam):
    def run(*args):
        frameSize = 8000  # 每一帧的音频大小
        intervel = 0.04  # 发送音频间隔(单位:s)
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                # 文件结束
                if not buf:
                    status = STATUS_LAST_FRAME
                # 第一帧处理
                # 发送第一帧音频，带business 参数
                # appid 必须带上，只需第一帧发送
                if status == STATUS_FIRST_FRAME:

                    d = {"common": wsParam.CommonArgs,
                         "business": wsParam.BusinessArgs,
                         "data": {"status": 0, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                # 模拟音频采样间隔
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())


# rtsp_url = "rtsp://192.168.0.214:554/live/1"
# output_file = "input.wav"
# capture_duration = "10"  # 捕获时间，单位为秒

# command = [
#     "ffmpeg",
#     "-y",  # 自动覆盖已存在文件
#     "-i", rtsp_url,
#     "-vn",  # 不捕获视频
#     "-acodec", "pcm_s16le",  # 转换为 PCM 格式
#     "-ar", "16000",  # 采样率
#     "-ac", "1",  # 单声道
#     "-t", capture_duration,  # 捕获时间
#     output_file
# ]
# def wav_to_pcm(input_wav, output_pcm, sample_rate=16000, channels=1):
#     # 加载 WAV 文件
#     audio = AudioSegment.from_wav(input_wav)
    
#     # 设置采样率和声道
#     audio = audio.set_frame_rate(sample_rate).set_channels(channels)
    
#     # 导出为 PCM (s16le 原始格式)
#     audio.export(output_pcm, format="raw")

# def handle_client(conn, addr, client_id):
#     try:
#         subprocess.run(command, check=True)
#         print(f"Captured audio saved to {output_file}")
#     except subprocess.CalledProcessError as e:
#         print("Error during FFmpeg execution:", e)
#     wav_to_pcm(input_wav=output_file, output_pcm='output.pcm')
#     # 测试时候在此处正确填写相关信息即可运行
#     time1 = datetime.now()
#     wsParam = Ws_Param(APPID='38f87f46', APISecret='MmZmZWZiOGNhMWNmODA0Mjc5NTg0MGM5',
#                        APIKey='8bd40e6493921b6afc6eb528f970094a',
#                        AudioFile=r'output.pcm')
#     websocket.enableTrace(False)
#     wsUrl = wsParam.create_url()
#     ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
#     ws.on_open = on_open
#     ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
#     time2 = datetime.now()
#     print(time2-time1)
SAMPLE_RATE = 16000  # 采样率
CHANNELS = 1  # 单声道
# 配置
HOST = '192.168.8.100'  # 本地主机
PORT = 10001            # 与发送端的端口保持一致
def capture_audio(rtsp_url, output_file, capture_duration):
    command = [
        "ffmpeg", "-y" , "-i", rtsp_url, "-vn", "-acodec", "pcm_s16le", "-ar", str(SAMPLE_RATE),
        "-ac", str(CHANNELS), "-t", str(capture_duration), output_file
    ]
    subprocess.run(command, check=True)
    print(f"Captured audio saved to {output_file}")

def wav_to_pcm(input_wav, output_pcm):
    audio = AudioSegment.from_wav(input_wav)
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(CHANNELS)
    audio.export(output_pcm, format="raw")

def handle_client(conn, addr, client_id):
    try:
        capture_audio(rtsp_url="rtsp://192.168.0.214:554/live/1", output_file=f"input{client_id}.wav", capture_duration=5)
        wav_to_pcm(input_wav=f"input{client_id}.wav", output_pcm=f"output{client_id}.pcm")
        
        # 测试时候在此处正确填写相关信息即可运行
        time1 = datetime.now()
        wsParam = Ws_Param(APPID='38f87f46', APISecret='MmZmZWZiOGNhMWNmODA0Mjc5NTg0MGM5',
                        APIKey='8bd40e6493921b6afc6eb528f970094a',
                        AudioFile=rf"output{client_id}.pcm")
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        # 启动缓冲区写入文件的线程
        thread = threading.Thread(target=write_buffer_to_file, daemon=True)
        thread.start()

        ws.on_open = lambda ws: on_open(ws, wsParam)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        time2 = datetime.now()
        print(time2-time1)
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
    # wsParam
        # 接参数IP地址
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    main()