import socket
import struct
import wave
import threading
from enum import Enum
import wave
import struct
import os
# 配置
HOST = '192.168.8.100'  # 本地主机
PORT = 10001            # 与发送端的端口保持一致

def handle_client(conn, addr, client_id):

# 主线程监听并接受客户端连接
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)  # 最大等待队列长度
        print(f"Server listening on {HOST}:{PORT}...")
         # 设置服务器 socket 为非阻塞
        s.setblocking(False)
        client_id = 0
        while True:
            try:
                # 尝试接受连接（非阻塞模式下，如果没有连接会抛出异常）
                conn, addr = s.accept()
                # conn.setblocking(False)  # 设置客户端连接为非阻塞
                # connections.append((conn, addr))
                print(f"Client {client_id} connected from {addr}")
                client_id += 1
                
                # conn, addr = s.accept()
                client_id += 1
                print(f"New connection from {addr}, client ID: {client_id}")
                client_thread = threading.Thread(target=handle_client, args=(conn, addr, client_id))
                client_thread.start()
            except BlockingIOError:
                # 没有新的连接，非阻塞模式下可以安全忽略
                pass

if __name__ == "__main__":
    # 接参数IP地址
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    main()