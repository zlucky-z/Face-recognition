#!/bin/bash

echo "正在停止http_push_test.py服务..."

# 获取http_push_test.py进程的PID
pid=$(pgrep -f "python3.*http_push_test.py")

if [ -z "$pid" ]; then
    echo "没有发现运行中的http_push_test.py进程"
    exit 0
fi

# 首先尝试正常终止进程
echo "正在终止进程 $pid..."
kill $pid

# 等待2秒让进程有机会正常退出
sleep 2

# 检查是否还有进程在运行
if pgrep -f "python3.*http_push_test.py" > /dev/null; then
    echo "进程未能正常终止，尝试强制终止..."
    pkill -9 -f "python3.*http_push_test.py"
fi

# 最后检查
if pgrep -f "python3.*http_push_test.py" > /dev/null; then
    echo "警告：http_push_test.py进程未能终止"
    exit 1
else
    echo "http_push_test.py服务已成功停止"
    exit 0
fi 