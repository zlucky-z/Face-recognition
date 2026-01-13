#!/bin/bash
# 设置环境变量
export PYTHONPATH=$PYTHONPATH:/opt/sophon/sophon-opencv_1.9.0/opencv-python
export LD_LIBRARY_PATH=/data/sophon-stream-master/build/lib:$LD_LIBRARY_PATH

# 切换到工作目录
cd /data/sophon-stream-master/samples/build

# 启动主程序并放入后台运行
./main --demo_config_path=../retinaface_distributor_resnet_faiss_converger/config/retinaface_distributor_resnet_faiss_converger.json &

