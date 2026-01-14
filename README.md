# Scripts 目录说明

本目录包含了 RetinaFace + ResNet + FAISS 人脸识别系统的所有脚本文件和 Web 管理界面。

## 目录结构

```
scripts/
├── http_push_test.py          # Flask Web 服务主程序
├── frame_cache.py             # 帧缓存管理模块
├── resnet_opencv_faiss_write.py  # 人脸特征提取和数据库生成脚本
├── start.sh                   # 启动人脸识别主程序
├── stop.sh                    # 停止 Web 服务
├── reboot_server.sh           # 重启 Web 服务
├── download.sh                # 下载模型和数据文件
├── before-use.md              # 使用前的环境配置说明
├── requirements.txt           # Python 依赖包列表
├── latest_frame.json          # 最新帧数据缓存文件
├── main_process.log           # 主进程日志文件
├── templates/                 # Web 界面 HTML 模板
│   ├── main.html             # 主界面
│   ├── login.html            # 登录页面
│   └── index.html            # 首页
└── static/                    # 静态资源文件
    ├── css/                  # 样式文件
    ├── js/                   # JavaScript 库
    └── webfonts/             # 字体文件
```

## 核心脚本说明

### 1. http_push_test.py - Web 服务主程序

基于 Flask 的 Web 服务，提供人脸识别系统的可视化管理界面。

**主要功能：**
- 用户登录认证（默认用户名/密码：admin/admin）
- 实时显示人脸检测结果
- 视频源管理和配置
- 人脸识别任务启动/停止控制
- 已识别人脸展示（需检测到 3 次以上才显示）
- 相似度阈值过滤（默认阈值 0.3）

**API 端点：**
- `GET /` - 主界面（需登录）
- `POST /login` - 用户登录
- `GET /logout` - 用户登出
- `GET /latest_img` - 获取最新帧图像
- `GET /latest_labels` - 获取最新帧的人脸标签
- `GET /get_face_image/<frame_id>/<face_index>` - 获取指定人脸图片
- `POST /stream/test` - 接收视频帧数据
- `POST /start_task` - 启动人脸识别任务
- `GET /task_status` - 查询任务运行状态
- `GET /get_confirmed_faces` - 获取已确认的人脸列表
- `POST /update_config` - 更新配置文件中的视频路径
- `POST /auto_cleanup` - 自动清理任务资源

**配置参数：**
```python
SIMILARITY_THRESHOLD = 0.3      # 相似度阈值
IMAGE_QUALITY = 85              # 人脸图片压缩质量
FACE_SIZE = (720, 540)          # 人脸图片尺寸
DETECTION_COUNT_THRESHOLD = 3   # 显示前需要检测的次数
```

**启动方式：**
```bash
python3 http_push_test.py
# 服务将在 0.0.0.0:8030 启动
```

### 2. frame_cache.py - 帧缓存管理模块

实现了一个线程安全的 LRU（最近最少使用）缓存系统，用于管理视频帧数据。

**主要特性：**
- 使用 OrderedDict 实现 LRU 缓存
- 线程安全的读写操作
- 自动清理过期数据
- 内存管理和垃圾回收

**使用示例：**
```python
from frame_cache import FrameCache

# 创建缓存实例（最多缓存 10 帧，每 300 秒清理一次）
cache = FrameCache(max_size=10, cleanup_interval=300)

# 更新缓存
cache.update(frame_data)

# 获取最新帧
latest_frame = cache.get()

# 获取指定帧
specific_frame = cache.get(frame_id)
```

### 3. resnet_opencv_faiss_write.py - 人脸特征提取脚本

用于从训练图片中提取人脸特征向量，生成 FAISS 数据库所需的数据文件。

**功能说明：**
- 使用 ResNet 模型提取人脸特征
- 支持批量处理图片
- 生成 FAISS 索引数据和标签文件
- 基于 Sophon SAIL 框架实现硬件加速

**使用方法：**
```bash
# 设置环境变量（必须）
export PYTHONPATH=/opt/sophon/sophon-opencv-latest/opencv-python:$PYTHONPATH

# 运行脚本
python3 resnet_opencv_faiss_write.py \
  --input /path/to/face_images \
  --bmodel /path/to/resnet_model.bmodel \
  --db_data faiss_db_data.txt \
  --index_label faiss_index_label.name \
  --dev_id 0
```

**参数说明：**
- `--input`: 训练图片目录路径（按人名分文件夹组织）
- `--bmodel`: ResNet 模型文件路径
- `--db_data`: 输出的特征向量数据文件
- `--index_label`: 输出的标签文件
- `--dev_id`: TPU 设备 ID（默认 0）

**输入数据格式：**
```
face_data_train/
├── person1/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── person2/
│   ├── image1.jpg
│   └── ...
└── ...
```

### 4. Shell 脚本

#### start.sh - 启动主程序
启动人脸识别主程序，设置必要的环境变量。

```bash
./start.sh
```

**功能：**
- 设置 PYTHONPATH 和 LD_LIBRARY_PATH
- 启动 main 程序并后台运行
- 加载配置文件

#### stop.sh - 停止服务
优雅地停止 Web 服务进程。

```bash
./stop.sh
```

**功能：**
- 查找 http_push_test.py 进程
- 尝试正常终止（SIGTERM）
- 如果失败则强制终止（SIGKILL）

#### reboot_server.sh - 重启服务
重启 Web 服务。

```bash
./reboot_server.sh
```

#### download.sh - 下载资源
下载模型文件和训练数据。

```bash
./download.sh
```

**下载内容：**
- BM1684X 模型文件
- BM1688 模型文件
- 人脸训练数据（face_data）
- 测试图片（images）
- 类别名称文件（class.names）

## 使用前准备

### 1. 环境配置

参考 [before-use.md](before-use.md) 文件，在运行人脸特征提取脚本前，需要设置环境变量：

```bash
export PYTHONPATH=/opt/sophon/sophon-opencv-latest/opencv-python:$PYTHONPATH
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

主要依赖：
- Flask 2.0.1 - Web 框架
- psutil 5.9.0 - 进程管理
- Pillow - 图像处理
- OpenCV - 计算机视觉
- sophon.sail - 算能 TPU 推理框架

### 3. 下载模型和数据

```bash
./download.sh
```

## 完整使用流程

### 步骤 1：准备训练数据

将人脸图片按人名分文件夹组织：
```
data/images/face_data_train/
├── 张三/
│   ├── 001.jpg
│   ├── 002.jpg
│   └── ...
├── 李四/
│   └── ...
└── ...
```

### 步骤 2：生成人脸特征数据库

```bash
# 设置环境变量
export PYTHONPATH=/opt/sophon/sophon-opencv-latest/opencv-python:$PYTHONPATH

# 运行特征提取
python3 resnet_opencv_faiss_write.py \
  --input ../data/images/face_data_train \
  --bmodel ../data/models/BM1688/resnet_arcface_fp32_1b.bmodel \
  --db_data faiss_db_data.txt \
  --index_label faiss_index_label.name
```

### 步骤 3：启动 Web 服务

```bash
python3 http_push_test.py
```

服务启动后访问：http://服务器IP:8030

### 步骤 4：登录系统

- 用户名：admin
- 密码：admin

### 步骤 5：配置视频源并启动识别

1. 在 Web 界面选择视频文件或配置摄像头
2. 点击"启动任务"按钮
3. 系统开始实时人脸识别
4. 当同一人脸被检测到 3 次以上时，会在界面显示

### 步骤 6：停止服务

```bash
./stop.sh
```

## 配置文件

主配置文件位于：`../config/retinaface_distributor_resnet_faiss_converger.json`

可通过 Web 界面或直接编辑配置文件来修改：
- 视频源路径
- 模型文件路径
- 检测参数
- 识别阈值

## 日志文件

- `main_process.log` - 主进程运行日志
- Flask 控制台输出 - Web 服务日志

## 注意事项

1. **环境变量**：运行特征提取脚本前必须设置 PYTHONPATH
2. **硬件要求**：需要算能 TPU 硬件支持（BM1684X 或 BM1688）
3. **端口占用**：Web 服务默认使用 8030 端口，确保端口未被占用
4. **内存管理**：系统会自动清理过期的帧缓存，避免内存溢出
5. **安全性**：生产环境请修改默认的 secret_key 和登录密码
6. **识别阈值**：可根据实际需求调整 SIMILARITY_THRESHOLD 和 DETECTION_COUNT_THRESHOLD

## 故障排查

### Web 服务无法启动
- 检查端口 8030 是否被占用
- 确认 Python 依赖已正确安装
- 查看控制台错误信息

### 人脸识别不准确
- 调整 SIMILARITY_THRESHOLD 阈值
- 增加训练样本数量
- 检查模型文件是否正确加载

### 主程序无法启动
- 检查环境变量是否正确设置
- 确认配置文件路径正确
- 查看 main_process.log 日志

### 内存占用过高
- 减小 FrameCache 的 max_size
- 降低 IMAGE_QUALITY 参数
- 缩小 FACE_SIZE 尺寸

## 技术支持

如遇到问题，请检查：
1. 日志文件中的错误信息
2. 环境变量配置
3. 硬件设备状态
4. 模型文件完整性

## 许可证

请参考项目根目录的许可证文件。
