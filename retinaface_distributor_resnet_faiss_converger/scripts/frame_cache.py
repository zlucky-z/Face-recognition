import time
from collections import OrderedDict
from threading import Lock
import gc

class FrameCache:
    def __init__(self, max_size=10, cleanup_interval=300):
        self._cache = OrderedDict()  # 使用OrderedDict实现LRU缓存
        self._lock = Lock()
        self._max_size = max_size
        self._last_cleanup = time.time()
        self._cleanup_interval = cleanup_interval
    
    def update(self, frame_data):
        with self._lock:
            frame_id = frame_data.get('mFrame', {}).get('mFrameId')
            if not frame_id:
                return
            # 直接缓存原始数据，不做图片压缩
            self._cache[frame_id] = {
                'mFrame': {
                    'mFrameId': frame_id,
                    'mSpData': frame_data.get('mFrame', {}).get('mSpData', '')
                },
                'mFaceObjectMetadata': frame_data.get('mFaceObjectMetadata', []),
                'mSubObjectMetadatas': frame_data.get('mSubObjectMetadatas', []),
                'timestamp': time.time()
            }
            # 如果超出最大缓存大小，删除最旧的帧
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)
            # 定期清理
            self._cleanup_if_needed()
    
    def get(self, frame_id=None):
        with self._lock:
            if frame_id is None:
                # 返回最新的帧
                return self._cache[max(self._cache.keys())] if self._cache else None
            return self._cache.get(frame_id)
    
    def _cleanup_if_needed(self):
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup()
            self._last_cleanup = current_time
    
    def _cleanup(self):
        """清理过期数据"""
        current_time = time.time()
        expired_frames = [
            frame_id for frame_id, data in self._cache.items()
            if current_time - data['timestamp'] > self._cleanup_interval
        ]
        for frame_id in expired_frames:
            del self._cache[frame_id]
        # 强制垃圾回收
        gc.collect() 