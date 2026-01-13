import json
import base64
import os
from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session, send_from_directory
from PIL import Image
from io import BytesIO
import time
from collections import OrderedDict
import glob
import subprocess
import psutil
import signal
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 用于session加密，请更改为安全的密钥

# 全局变量存储人脸检测状态
face_detection_counter = {}  # 格式: {label: count}
confirmed_faces = {}  # 已确认可以显示的人脸 {label: {"image": base64, "similarity": float, "frameId": int, "faceIndex": int}}

# 添加任务状态跟踪
task_was_running = False  # 记录任务之前是否在运行

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 配置
SIMILARITY_THRESHOLD = 0.3  # 阈值，score大于等于此值为正常识别，否则为unknown
IMAGE_QUALITY = 85           # 人脸图片压缩质量
FACE_SIZE = (720, 540)       # 统一的人脸图片大小
CONFIG_FILE = '../config/retinaface_distributor_resnet_faiss_converger.json'
DETECTION_COUNT_THRESHOLD = 3  # 需要检测到多少次才显示

# 模拟用户数据库
USERS = {
    'admin': 'admin'  # 用户名: 密码
}

@app.route('/static/<path:filename>')
def static_files(filename):
    """提供静态文件服务"""
    return send_from_directory('static', filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """前端页面入口"""
    return render_template('main.html')

@app.route('/latest_img')
def get_latest_image():
    """获取最新帧图像和元数据"""
    try:
        with open('latest_frame.json', 'r') as f:
            frame_data = json.load(f)
        return jsonify({
            "img": frame_data['mFrame']['mSpData'],
            "metadata": frame_data
        })
    except Exception:
        return jsonify({"img": "", "metadata": {}}), 404

@app.route('/latest_labels')
def get_latest_labels():
    """获取最新帧的标签统计数据"""
    global face_detection_counter, confirmed_faces
    try:
        with open('latest_frame.json', 'r') as f:
            frame_data = json.load(f)

        labels = []
        face_indices = []
        similarities = []

        faces = frame_data.get('mFaceObjectMetadata', [])
        subs = frame_data.get('mSubObjectMetadatas', [])

        current_frame_faces = {}  # 当前帧检测到的人脸
        
        for i, face in enumerate(faces):
            label = f"face_{i+1}"
            similarity = float(face.get('score', 0))
            if i < len(subs):
                recog_objs = subs[i].get('mRecognizedObjectMetadatas', [])
                if recog_objs:
                    recog = recog_objs[0]
                    label = recog.get('mLabelName', label)
                    if 'mScores' in recog and recog['mScores']:
                        similarity = float(recog['mScores'][0])
            
            # 只处理识别相似度达到阈值的人脸
            if similarity >= SIMILARITY_THRESHOLD:
                # 统计检测次数
                if label not in face_detection_counter:
                    face_detection_counter[label] = 0
                face_detection_counter[label] += 1
                
                # 记录当前帧的人脸信息
                current_frame_faces[label] = {
                    'similarity': similarity,
                    'frameId': frame_data['mFrame']['mFrameId'],
                    'faceIndex': i
                }
                
                # 检查是否达到显示条件（第三次检测到）且不是unknown
                if face_detection_counter[label] >= DETECTION_COUNT_THRESHOLD and label != "unknown":
                    # 如果还没有确认的人脸图片，则保存当前的
                    if label not in confirmed_faces:
                        # 获取人脸图片
                        try:
                            sp_data = frame_data['mFrame']['mSpData']
                            if sp_data:
                                img_data = base64.b64decode(sp_data)
                                img = Image.open(BytesIO(img_data))
                                
                                left = int(face.get('left', 0))
                                top = int(face.get('top', 0))
                                right = int(face.get('right', 0))
                                bottom = int(face.get('bottom', 0))
                                
                                # 边界检查
                                img_width, img_height = img.size
                                left = max(0, min(left, img_width - 1))
                                top = max(0, min(top, img_height - 1))
                                right = max(0, min(right, img_width))
                                bottom = max(0, min(bottom, img_height))
                                
                                if right > left and bottom > top:
                                    face_img = img.crop((left, top, right, bottom))
                                    face_img = face_img.resize(FACE_SIZE, Image.Resampling.LANCZOS)
                                    buffered = BytesIO()
                                    face_img.save(buffered, format="JPEG", quality=IMAGE_QUALITY)
                                    face_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                                    
                                    confirmed_faces[label] = {
                                        'image': face_b64,
                                        'similarity': similarity,
                                        'frameId': frame_data['mFrame']['mFrameId'],
                                        'faceIndex': i
                                    }
                        except Exception as e:
                            print(f"保存确认人脸失败: {e}")
            else:
                # 未达到阈值的标记为unknown
                label = "unknown"
            
            labels.append(label)
            face_indices.append(i)
            similarities.append(similarity)

        # 只返回已确认的人脸（检测满3次的）
        confirmed_labels = []
        confirmed_face_indices = []
        confirmed_similarities = []
        
        for label, face_info in confirmed_faces.items():
            confirmed_labels.append(label)
            confirmed_face_indices.append(face_info['faceIndex'])
            confirmed_similarities.append(face_info['similarity'])

        return jsonify({
            "labels": confirmed_labels,
            "frameId": frame_data['mFrame']['mFrameId'],
            "faceIndices": confirmed_face_indices,
            "similarities": confirmed_similarities,
            "detectionCounts": face_detection_counter  # 添加检测计数信息
        })
    except Exception as e:
        print(f'latest_labels error: {e}')
        return jsonify({
            "labels": [], 
            "frameId": 0, 
            "faceIndices": [], 
            "similarities": [],
            "detectionCounts": {}
        })

@app.route('/get_face_image/<int:frame_id>/<int:face_index>')
def get_face_image(frame_id, face_index):
    global confirmed_faces
    try:
        # 首先尝试从confirmed_faces中获取图片
        for label, face_info in confirmed_faces.items():
            if face_info['faceIndex'] == face_index:
                return jsonify({"image": face_info['image']})
        
        # 如果没有找到确认的人脸，则按原来的方式处理
        # 直接读取文件
        with open('latest_frame.json', 'r') as f:
            frame_data = json.load(f)
        if frame_data['mFrame']['mFrameId'] != frame_id:
            return jsonify({"image": ""}), 404
        faces = frame_data.get('mFaceObjectMetadata', [])
        if len(faces) <= face_index:
            return jsonify({"image": ""}), 404
        sp_data = frame_data['mFrame']['mSpData']
        if not sp_data:
            return jsonify({"image": ""}), 404
        img_data = base64.b64decode(sp_data)
        img = Image.open(BytesIO(img_data))
        face = faces[face_index]
        left = int(face.get('left', 0))
        top = int(face.get('top', 0))
        right = int(face.get('right', 0))
        bottom = int(face.get('bottom', 0))
        if right <= left or bottom <= top:
            return jsonify({"image": ""}), 400
        img_width, img_height = img.size
        left = max(0, min(left, img_width - 1))
        top = max(0, min(top, img_height - 1))
        right = max(0, min(right, img_width))
        bottom = max(0, min(bottom, img_height))
        if right <= left or bottom <= top:
            return jsonify({"image": ""}), 400
        face_img = img.crop((left, top, right, bottom))
        face_img = face_img.resize(FACE_SIZE, Image.Resampling.LANCZOS)
        buffered = BytesIO()
        face_img.save(buffered, format="JPEG", quality=IMAGE_QUALITY)
        face_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return jsonify({"image": face_b64})
    except Exception as e:
        print(f"裁剪人脸失败: Frame {frame_id}, Face {face_index} - {str(e)}")
        return jsonify({"image": ""}), 500

@app.route('/stream/test', methods=['POST'])
def stream_test():
    """接收视频帧数据"""
    try:
        data = json.loads(request.data.decode('utf-8'))
        frame_id = data.get('mFrame', {}).get('mFrameId')
        if not frame_id:
            return jsonify({"status": "error", "message": "Missing frame ID"}), 400
        with open('latest_frame.json', 'w') as f:
            json.dump(data, f)
        return jsonify({"status": "success", "frameId": frame_id})
    except Exception as e:
        print(f"处理帧数据失败: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/video/<path:filename>')
def serve_video(filename):
    """提供视频文件服务"""
    try:
        video_path = os.path.join('/data/sophon-stream-master/samples/retinaface_distributor_resnet_faiss_converger', filename)
        if os.path.exists(video_path):
            return send_file(video_path, mimetype='video/mp4')
        return jsonify({"error": "Video file not found"}), 404
    except Exception as e:
        print(f"提供视频文件失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/list_videos')
def list_videos():
    """获取指定路径下的视频文件列表"""
    try:
        path = request.args.get('path', '')
        if not path or not os.path.exists(path):
            return jsonify({"files": []}), 404

        # 获取所有视频文件
        video_files = []
        for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
            video_files.extend(glob.glob(os.path.join(path, ext)))

        # 格式化文件信息
        files = [{
            'name': os.path.basename(f),
            'path': f
        } for f in video_files]

        return jsonify({"files": files})
    except Exception as e:
        print(f"获取视频文件列表失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/update_config', methods=['POST'])
def update_config():
    """更新配置文件中的视频路径"""
    try:
        data = request.get_json()
        video_path = data.get('video_path')
        if not video_path:
            return jsonify({"error": "Missing video path"}), 400

        # 读取当前配置
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        # 更新视频路径
        if config.get('channels') and len(config['channels']) > 0:
            config['channels'][0]['url'] = video_path

            # 保存更新后的配置
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)

            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Invalid config format"}), 400
    except Exception as e:
        print(f"更新配置文件失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/auto_cleanup', methods=['POST'])
def auto_cleanup():
    """自动清理任务完成后的资源"""
    global task_was_running
    try:
        # 强制终止所有main进程
        subprocess.run(['pkill', '-9', '-f', 'main'], stderr=subprocess.DEVNULL)
        
        # 重置任务状态
        task_was_running = False
        
        return jsonify({
            'status': 'success', 
            'message': '检测任务已完成，系统资源已自动清理'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'自动清理失败: {str(e)}'
        }), 500

@app.route('/start_task', methods=['POST'])
def start_task():
    global face_detection_counter, confirmed_faces, task_was_running
    try:
        # 清空人脸检测状态
        face_detection_counter = {}
        confirmed_faces = {}
        
        # 在启动新任务前，先确保没有遗留的main进程
        subprocess.run(['pkill', '-9', '-f', 'main'], stderr=subprocess.DEVNULL)
        
        # 设置任务运行状态
        task_was_running = True
        
        # 启动新任务
        subprocess.Popen(['bash', os.path.join(os.path.dirname(__file__), 'start.sh')])
        return jsonify({
            'status': 'success', 
            'message': '检测任务已启动，正在进行人脸对比，请耐心等待'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/task_status', methods=['GET'])
def task_status():
    global task_was_running
    try:
        is_running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'main' in proc.info['name']:
                    is_running = True
                    break
            except Exception:
                continue
        
        # 构建响应数据
        response_data = {
            'status': 'success', 
            'is_running': is_running,
            'was_running': task_was_running
        }
        
        # 如果之前在运行但现在停止了，说明任务自然完成
        if task_was_running and not is_running:
            # 不要在这里重置task_was_running，让前端处理完成逻辑后再重置
            pass
        elif is_running:
            # 任务正在运行，更新状态
            task_was_running = True
            
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'is_running': False,
            'was_running': task_was_running
        }), 500

@app.route('/get_confirmed_faces', methods=['GET'])
def get_confirmed_faces():
    """获取已确认的人脸列表（检测满3次的人脸）"""
    global confirmed_faces, face_detection_counter
    try:
        result = []
        for label, face_info in confirmed_faces.items():
            # 过滤掉unknown
            if label != "unknown":
                result.append({
                    'label': label,
                    'image': face_info['image'],
                    'similarity': face_info['similarity'],
                    'frameId': face_info['frameId'],
                    'faceIndex': face_info['faceIndex'],
                    'detectionCount': face_detection_counter.get(label, 0)
                })
        return jsonify({
            'status': 'success',
            'confirmedFaces': result,
            'totalCount': len(result)
        })
    except Exception as e:
        print(f"获取已确认人脸失败: {e}")
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'confirmedFaces': [],
            'totalCount': 0
        }), 500

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

def cleanup_old_frames():
    try:
        if os.path.exists('latest_frame.json'):
            # 只保留最新的几帧
            with open('latest_frame.json', 'r') as f:
                frame_data = json.load(f)
            # 清理旧数据
            if 'mFrame' in frame_data:
                frame_data['mFrame']['mSpData'] = ""  # 清空图像数据
            with open('latest_frame.json', 'w') as f:
                json.dump(frame_data, f)
    except Exception as e:
        print(f"清理旧帧数据失败: {e}")

if __name__ == '__main__':
    # 确保上传的图片有足够的内存空间
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    app.run(host='0.0.0.0', port=8030, debug=True)