#!/bin/bash

# 设置目标主机
HOST=192.168.0.100

# 定义启动程序的函数，方便管理
start_programs() {
    # 删除文件
    rm -f a2t.log talk.log t2a.log test.log
    rm -f *.txt *.pcm *.wav *.log
    echo "Starting programs..."

    sudo nohup python3 -u a2t.py "${HOST}" > a2t.log 2>&1 &
    echo "a2t.py started."

    sudo ./talk > talk.log 2>&1 &
    echo "talk started."

    sudo nohup python3 -u t2a.py > t2a.log 2>&1 &
    echo "t2a.py started."

    sudo nohup python3 -u test.py "${HOST}" > test.log 2>&1 &
    echo "test.py started."
}

# 启动程序
start_programs

# 提示用户所有程序已启动
echo "All programs started successfully."
