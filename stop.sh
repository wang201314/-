#!/bin/bash

# 停止程序的脚本
# 使用方式: ./stop.sh

echo "正在停止程序..."

# 定义程序的名称或端口
PROCESS_NAMES=("a2t.py" "talk" "t2a.py" "test.py")   # 程序名称列表
PORTS=("8080" "10001")                                    # 如果有特定端口占用，可在此添加

# 1. 通过进程名称查找并终止
for PROCESS in "${PROCESS_NAMES[@]}"; do
    echo "查找进程: $PROCESS"
    PIDS=$(pgrep -f "$PROCESS")   # 查找与名称匹配的进程ID
    if [ -n "$PIDS" ]; then
        echo "找到进程ID: $PIDS，正在终止..."
        kill -9 $PIDS
        echo "进程 $PROCESS 已终止."
    else
        echo "未找到进程: $PROCESS"
    fi
done

# 2. 通过端口查找并终止
for PORT in "${PORTS[@]}"; do
    echo "查找占用端口: $PORT"
    PIDS=$(lsof -t -i:$PORT)  # 查找占用指定端口的进程ID
    if [ -n "$PIDS" ]; then
        echo "找到占用端口 $PORT 的进程ID: $PIDS，正在终止..."
        kill -9 $PIDS
        echo "端口 $PORT 占用已清理."
    else
        echo "未找到占用端口 $PORT 的进程."
    fi
done

echo "所有指定程序已停止。"
