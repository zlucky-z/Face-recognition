# 人脸检测-分发-识别系统

[English](README_EN.md) | 简体中文

## 目录
- [人脸检测-分发-识别系统](#人脸检测-分发-识别系统)
  - [目录](#目录)
  - [1. 项目简介](#1-项目简介)
  - [2. 系统特性](#2-系统特性)
  - [3. 项目结构](#3-项目结构)
  - [4. 快速开始](#4-快速开始)
    - [4.1 准备模型与数据](#41-准备模型与数据)
    - [4.2 环境准备](#42-环境准备)
    - [4.3 安装依赖](#43-安装依赖)
  - [5. 程序编译](#5-程序编译)
    - [5.1 x86/arm PCIe平台](#51-x86arm-pcie平台)
    - [5.2 SoC平台](#52-soc平台)
  - [6. 使用指南](#6-使用指南)
    - [6.1 生成人脸数据库](#61-生成人脸数据库)
    - [6.2 启动 Web 管理界面](#62-启动-web-管理界面)
    - [6.3 配置说明](#63-配置说明)
    - [6.4 命令行运行](#64-命令行运行)
  - [7. Web 管理界面](#7-web-管理界面)
  - [8. 配置文件详解](#8-配置文件详解)
  - [9. 性能测试](#9-性能测试)
  - [10. 常见问题](#10-常见问题)
  - [11. 技术支持](#11-技术支持)

## 1. 项目简介

本项目是一个基于算能 Sophon 平台的完整人脸识别解决方案，集成了人脸检测、特征提取、人脸识别和 Web 可视化管理功能。系统采用 RetinaFace 进行人脸检测，ResNet 提取人脸特征，FAISS 进行高效的人脸匹配，并提供了友好的 Web 管理界面。

**核心功能：**
- 实时视频流人脸检测与识别
- 多路视频流并发处理
- Web 可视化管理界面
- 人脸数据库管理
- HTTP 推流支持
- 识别结果实时展示

**适用场景：**
- 智能安防监控
- 门禁考勤系统
- 访客管理系统
- 智能零售分析

## 2. 系统特性

### 算法特性
* **人脸检测**：RetinaFace MobileNet0.25 模型，高效准确
* **特征提取**：ResNet ArcFace 模型，512维特征向量
* **人脸识别**：FAISS 向量检索，毫秒级匹配速度
* **多线程处理**：支持多路视频流并发处理
* **智能分发**：按类别、时间、帧数灵活分发策略

### 硬件支持
* **BM1684X**：x86 PCIe、SoC 平台
* **BM1688**：SoC 平台（需 SDK 1.8+）
* **多 TPU 设备**：支持多设备负载均衡

### Web 界面特性
* **用户认证**：登录保护，默认账号 admin/admin
* **实时监控**：视频流实时显示，人脸框选标注
* **识别展示**：已识别人脸卡片展示，相似度显示
* **任务控制**：一键启动/停止识别任务
* **视频管理**：支持视频文件选择和配置
* **智能过滤**：相似度阈值过滤，多次确认机制

## 3. 项目结构

```
retinaface_distributor_resnet_faiss_converger/
├── README.md                          # 项目说明文档（本文件）
├── README_EN.md                       # 英文说明文档
├── face_test1.mp4                     # 测试视频文件1
├── face_test2.mp4                     # 测试视频文件2
├── face_test3.mp4                     # 测试视频文件3
├── config/                            # 配置文件目录
│   ├── retinaface_distributor_resnet_faiss_converger.json  # 主配置文件
│   ├── engine_group.json              # 处理流程图配置
│   ├── decode.json                    # 视频解码配置
│   ├── retinaface_group.json          # RetinaFace 检测配置
│   ├── retinaface_pre.json            # RetinaFace 前处理
│   ├── retinaface_infer.json          # RetinaFace 推理
│   ├── retinaface_post.json           # RetinaFace 后处理
│   ├── distributor_*.json             # 分发器配置（按类别/时间/帧数）
│   ├── resnet_face.json               # ResNet 特征提取配置
│   ├── faiss.json                     # FAISS 检索配置
│   ├── converger.json                 # 结果汇聚配置
│   ├── osd.json                       # 画图配置
│   ├── http_push.json                 # HTTP 推流配置
│   └── encode.json                    # 视频编码配置
├── data/                              # 数据目录
│   ├── class.names                    # 分类标签文件
│   ├── models/                        # 模型文件
│   │   ├── BM1684X/
│   │   │   ├── retinaface_mobilenet0.25_fp32_1b.bmodel
│   │   │   └── resnet_arcface_fp32_1b.bmodel
│   │   └── BM1688/
│   │       ├── retinaface_mobilenet0.25_fp32_1b.bmodel
│   │       └── resnet_arcface_fp32_1b.bmodel
│   ├── face_data/                     # 人脸数据库
│   │   ├── faiss_db_data.txt          # 特征向量数据
│   │   └── faiss_index_label.name     # 人脸标签索引
│   └── images/                        # 图片数据集
│       ├── face_data_train/           # 训练集（用于生成数据库）
│       └── face_data_test/            # 测试集
└── scripts/                           # 脚本目录
    ├── README.md                      # 脚本说明文档
    ├── http_push_test.py              # Flask Web 服务主程序
    ├── frame_cache.py                 # 帧缓存管理模块
    ├── resnet_opencv_faiss_write.py   # 人脸数据库生成脚本
    ├── start.sh                       # 启动识别主程序
    ├── stop.sh                        # 停止 Web 服务
    ├── reboot_server.sh               # 重启 Web 服务
    ├── download.sh                    # 下载模型和数据
    ├── before-use.md                  # 使用前配置说明
    ├── requirements.txt               # Python 依赖
    ├── latest_frame.json              # 最新帧缓存
    ├── templates/                     # Web 界面模板
    │   ├── main.html                  # 主界面
    │   ├── login.html                 # 登录页面
    │   └── index.html                 # 首页
    └── static/                        # 静态资源
        ├── css/                       # 样式文件
        ├── js/                        # JavaScript 库
        └── webfonts/                  # 字体文件
```

## 4. 快速开始

### 4.1 准备模型与数据

在 `scripts` 目录下提供了模型和数据的下载脚本：

```bash
# 安装 unzip（若已安装请跳过）
sudo apt install unzip

# 赋予脚本执行权限并运行
chmod -R +x scripts/
./scripts/download.sh
```

**下载内容：**
- **模型文件**：RetinaFace 和 ResNet 的 BM1684X/BM1688 模型
- **人脸数据库**：预生成的 FAISS 索引和标签
- **训练数据集**：用于生成自定义人脸数据库
- **测试数据集**：用于测试识别效果
- **分类标签**：class.names 文件

### 4.2 环境准备

#### x86/arm PCIe 平台

如果您在 x86/arm 平台安装了 PCIe 加速卡（如 SC 系列加速卡），需要安装：
- libsophon
- sophon-opencv
- sophon-ffmpeg

具体步骤可参考 [x86-pcie平台的开发和运行环境搭建](../../docs/EnvironmentInstallGuide.md#3-x86-pcie平台的开发和运行环境搭建) 或 [arm-pcie平台的开发和运行环境搭建](../../docs/EnvironmentInstallGuide.md#5-arm-pcie平台的开发和运行环境搭建)。

#### SoC 平台

如果您使用 SoC 平台（如 SE、SM 系列边缘设备），刷机后在 `/opt/sophon/` 下已经预装了相应的运行库包，可直接使用。通常还需要一台 x86 主机作为开发环境，用于交叉编译 C++ 程序。

### 4.3 安装依赖

```bash
# 进入 scripts 目录
cd scripts

# 安装 Python 依赖
pip3 install -r requirements.txt

# 设置环境变量（生成人脸数据库时需要）
export PYTHONPATH=/opt/sophon/sophon-opencv-latest/opencv-python:$PYTHONPATH
```

**主要依赖：**
- Flask 2.0.1 - Web 框架
- psutil 5.9.0 - 进程管理
- Pillow - 图像处理
- OpenCV - 计算机视觉
- sophon.sail - 算能 TPU 推理框架


## 5. 程序编译

程序运行前需要编译可执行文件。

### 5.1 x86/arm PCIe平台

可以直接在 PCIe 平台上编译程序，具体请参考 [sophon-stream编译](../../docs/HowToMake.md)

### 5.2 SoC平台

通常在 x86 主机上交叉编译程序，您需要在 x86 主机上使用 SOPHON SDK 搭建交叉编译环境，将程序所依赖的头文件和库文件打包至 sophon_sdk_soc 目录中，具体请参考 [sophon-stream编译](../../docs/HowToMake.md)。本例程主要依赖 libsophon、sophon-opencv 和 sophon-ffmpeg 运行库包。

## 6. 使用指南

### 6.1 生成人脸数据库

在使用系统前，需要先生成人脸特征数据库。将训练图片按人名分文件夹组织：

```bash
data/images/face_data_train/
├── 张三/
│   ├── 001.jpg
│   ├── 002.jpg
│   └── ...
├── 李四/
│   ├── 001.jpg
│   └── ...
└── ...
```

然后运行特征提取脚本：

```bash
# 设置环境变量（必须）
export PYTHONPATH=/opt/sophon/sophon-opencv-latest/opencv-python:$PYTHONPATH

# 运行特征提取（BM1688 示例）
cd scripts
python3 resnet_opencv_faiss_write.py \
  --input ../data/images/face_data_train \
  --bmodel ../data/models/BM1688/resnet_arcface_fp32_1b.bmodel \
  --db_data ../data/face_data/faiss_db_data.txt \
  --index_label ../data/face_data/faiss_index_label.name \
  --dev_id 0
```

**参数说明：**
- `--input`: 训练图片目录路径（按人名分文件夹）
- `--bmodel`: ResNet 模型文件路径
- `--db_data`: 输出的特征向量数据文件
- `--index_label`: 输出的标签文件
- `--dev_id`: TPU 设备 ID（默认 0）

### 6.2 启动 Web 管理界面

系统提供了友好的 Web 管理界面，推荐使用此方式：

```bash
cd scripts
python3 http_push_test.py
```

服务启动后，访问：`http://服务器IP:8030`

**默认登录信息：**
- 用户名：`admin`
- 密码：`admin`

**Web 界面功能：**
1. **视频源配置**：选择视频文件或配置摄像头
2. **任务控制**：一键启动/停止识别任务
3. **实时监控**：查看视频流和检测结果
4. **人脸展示**：显示已识别的人脸（检测3次以上）
5. **相似度查看**：查看每个人脸的识别相似度

### 6.3 配置说明

主配置文件：[config/retinaface_distributor_resnet_faiss_converger.json](config/retinaface_distributor_resnet_faiss_converger.json)

```json
{
  "channels": [
    {
      "channel_id": 0,
      "url": "../retinaface_distributor_resnet_faiss_converger/face_test1.mp4",
      "source_type": "VIDEO",
      "loop_num": 1,
      "sample_interval": 1,
      "fps": -1
    }
  ],
  "engine_config_path": "../retinaface_distributor_resnet_faiss_converger/config/engine_group.json"
}
```

**参数说明：**
- `channel_id`: 通道 ID
- `url`: 视频源路径（支持视频文件、图片目录、RTSP 流）
- `source_type`: 源类型（VIDEO/IMG_DIR/RTSP）
- `loop_num`: 循环次数
- `sample_interval`: 采样间隔
- `fps`: 帧率（-1 表示使用原始帧率）

**支持多路视频流：**可以在 `channels` 数组中添加多个通道配置。

### 6.4 命令行运行

如果不使用 Web 界面，也可以直接运行主程序：

```bash
# 进入编译目录
cd /path/to/sophon-stream/samples/build

# 运行主程序
./main --demo_config_path=../retinaface_distributor_resnet_faiss_converger/config/retinaface_distributor_resnet_faiss_converger.json
```

运行结果存放在 `./build/results` 目录下。

## 7. Web 管理界面

Web 管理界面提供了完整的可视化操作体验：

### 功能特性

1. **用户认证**
   - 登录保护，防止未授权访问
   - 默认账号：admin/admin
   - 可在代码中修改用户名密码

2. **实时视频监控**
   - 实时显示视频流
   - 人脸框选标注
   - 帧率和分辨率信息

3. **人脸识别展示**
   - 卡片式展示已识别人脸
   - 显示人脸姓名和相似度
   - 自动过滤低相似度结果

4. **智能过滤机制**
   - 相似度阈值：0.3（可配置）
   - 确认机制：检测到 3 次以上才显示
   - 自动过滤 unknown 人脸

5. **任务管理**
   - 一键启动识别任务
   - 自动检测任务状态
   - 任务完成自动清理资源

6. **视频源管理**
   - 支持视频文件选择
   - 支持 RTSP 流配置
   - 动态更新配置文件

### 配置参数

在 [scripts/http_push_test.py](scripts/http_push_test.py) 中可以调整以下参数：

```python
SIMILARITY_THRESHOLD = 0.3      # 相似度阈值（0-1）
IMAGE_QUALITY = 85              # 人脸图片压缩质量（1-100）
FACE_SIZE = (720, 540)          # 人脸图片尺寸
DETECTION_COUNT_THRESHOLD = 3   # 显示前需要检测的次数
```

### API 接口

Web 服务提供了以下 REST API：

- `POST /login` - 用户登录
- `GET /logout` - 用户登出
- `GET /latest_img` - 获取最新帧图像
- `GET /latest_labels` - 获取最新帧的人脸标签
- `GET /get_face_image/<frame_id>/<face_index>` - 获取指定人脸图片
- `POST /stream/test` - 接收视频帧数据
- `POST /start_task` - 启动人脸识别任务
- `GET /task_status` - 查询任务运行状态
- `GET /get_confirmed_faces` - 获取已确认的人脸列表
- `POST /update_config` - 更新配置文件
- `POST /auto_cleanup` - 自动清理任务资源

## 8. 配置文件详解

系统采用模块化配置，每个处理环节都有独立的配置文件：

### 主配置文件

[retinaface_distributor_resnet_faiss_converger.json](config/retinaface_distributor_resnet_faiss_converger.json) - 管理输入源和整体流程

### 处理流程配置

[engine_group.json](config/engine_group.json) - 定义处理流程图，包含：
- **元素定义**：decode、retinaface、distributor、resnet、faiss、converger、osd、http_push
- **连接关系**：定义数据流向

**处理流程：**
```
视频输入 → 解码 → RetinaFace检测 → 分发器 → ResNet特征提取 → FAISS检索 → 结果汇聚 → 画图 → HTTP推流
                                    ↓
                                 全帧输出
```

### 模块配置文件

- [decode.json](config/decode.json) - 视频解码配置
- [retinaface_group.json](config/retinaface_group.json) - RetinaFace 检测配置
- [distributor_frame_class.json](config/distributor_frame_class.json) - 分发策略配置
- [resnet_face.json](config/resnet_face.json) - ResNet 特征提取配置
- [faiss.json](config/faiss.json) - FAISS 检索配置
- [converger.json](config/converger.json) - 结果汇聚配置
- [osd.json](config/osd.json) - 画图配置
- [http_push.json](config/http_push.json) - HTTP 推流配置

### 分发策略

系统支持多种分发策略：
- `distributor_frame.json` - 跳帧分发全帧
- `distributor_time.json` - 按时间间隔分发全帧
- `distributor_class.json` - 每帧按类别分发
- `distributor_frame_class.json` - 跳帧按类别分发（默认）
- `distributor_time_class.json` - 按时间间隔按类别分发

## 9. 性能测试

由于全流程依赖输入视频 fps 且画图速度较慢，本例程暂不提供完整的性能测试结果。

**如需各模型推理性能，请参考：**
- RetinaFace 模型性能：参考 RetinaFace 例程
- ResNet 模型性能：参考 ResNet 例程
- FAISS 检索性能：毫秒级匹配速度

**性能优化建议：**
1. 调整 `sample_interval` 参数，降低处理帧率
2. 使用 INT8 量化模型提升推理速度
3. 合理配置 `thread_number` 参数
4. 多路视频流时使用多 TPU 设备负载均衡

## 10. 常见问题

### Q1: Web 服务无法启动

**可能原因：**
- 端口 8030 被占用
- Python 依赖未正确安装
- 权限不足

**解决方案：**
```bash
# 检查端口占用
netstat -tuln | grep 8030

# 重新安装依赖
pip3 install -r scripts/requirements.txt

# 使用 sudo 运行（如需要）
sudo python3 scripts/http_push_test.py
```

### Q2: 人脸识别不准确

**可能原因：**
- 相似度阈值设置不当
- 训练样本不足
- 模型文件损坏

**解决方案：**
```python
# 调整相似度阈值（在 http_push_test.py 中）
SIMILARITY_THRESHOLD = 0.5  # 提高阈值，减少误识别

# 增加训练样本
# 每个人至少 5-10 张不同角度的照片

# 重新下载模型
./scripts/download.sh
```

### Q3: 主程序无法启动

**可能原因：**
- 环境变量未设置
- 配置文件路径错误
- TPU 设备不可用

**解决方案：**
```bash
# 设置环境变量
export LD_LIBRARY_PATH=/data/sophon-stream-master/build/lib:$LD_LIBRARY_PATH

# 检查 TPU 设备
ls /dev/bm*

# 检查配置文件路径
cat config/retinaface_distributor_resnet_faiss_converger.json
```

### Q4: 内存占用过高

**可能原因：**
- 帧缓存过大
- 图片质量设置过高
- 多路视频流并发

**解决方案：**
```python
# 在 frame_cache.py 中调整缓存大小
cache = FrameCache(max_size=5, cleanup_interval=300)  # 减小 max_size

# 在 http_push_test.py 中降低图片质量
IMAGE_QUALITY = 60  # 降低质量
FACE_SIZE = (480, 360)  # 缩小尺寸
```

### Q5: 生成人脸数据库失败

**可能原因：**
- 环境变量未设置
- 图片格式不支持
- 模型路径错误

**解决方案：**
```bash
# 设置环境变量（必须）
export PYTHONPATH=/opt/sophon/sophon-opencv-latest/opencv-python:$PYTHONPATH

# 检查图片格式（支持 jpg、png、jpeg、bmp）
file data/images/face_data_train/person1/*.jpg

# 检查模型文件
ls -lh data/models/BM1688/resnet_arcface_fp32_1b.bmodel
```

### Q6: 视频流卡顿

**可能原因：**
- 网络带宽不足
- 处理速度跟不上
- 采样间隔设置不当

**解决方案：**
```json
// 在配置文件中调整参数
{
  "sample_interval": 3,  // 增加采样间隔
  "fps": 10              // 降低帧率
}
```

### Q7: 无法识别某些人脸

**可能原因：**
- 人脸角度过大
- 光照条件差
- 人脸数据库中无此人

**解决方案：**
1. 确保训练图片包含多角度照片
2. 使用光照良好的图片
3. 检查数据库中是否有该人的特征数据

### Q8: 登录密码忘记

**解决方案：**
```python
# 在 scripts/http_push_test.py 中修改
USERS = {
    'admin': 'newpassword'  # 修改密码
}
```

## 11. 技术支持

### 文档资源

- **项目文档**：[README.md](README.md)（本文件）
- **脚本文档**：[scripts/README.md](scripts/README.md)
- **使用前配置**：[scripts/before-use.md](scripts/before-use.md)
- **英文文档**：[README_EN.md](README_EN.md)

### 日志文件

- **主程序日志**：`scripts/main_process.log`
- **Web 服务日志**：控制台输出
- **系统日志**：`/var/log/syslog`（Linux）

### 调试建议

1. **启用详细日志**
   ```python
   # 在 Python 脚本中
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查系统资源**
   ```bash
   # 查看 TPU 使用情况
   bm-smi

   # 查看内存使用
   free -h

   # 查看进程状态
   ps aux | grep main
   ```

3. **测试模型推理**
   ```bash
   # 单独测试 RetinaFace
   # 单独测试 ResNet
   # 单独测试 FAISS
   ```

### 联系方式

如遇到无法解决的问题，请：
1. 查看日志文件获取详细错误信息
2. 检查环境配置是否正确
3. 确认硬件设备状态正常
4. 验证模型文件完整性

### 贡献指南

欢迎提交问题和改进建议：
1. Fork 本项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

### 许可证

请参考项目根目录的许可证文件。

---

**版本信息：**
- 项目版本：1.0
- 最后更新：2026-01
- 支持平台：BM1684X、BM1688
- SDK 要求：1.8+（BM1688）

**关键词：** 人脸识别、RetinaFace、ResNet、FAISS、算能、Sophon、TPU、Web界面、实时检测
