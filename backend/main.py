from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from typing import Dict, List
import json
import asyncio
import os
import shutil
import csv
import time
from adbutils import adb
from core.android_collector import AndroidCollector
from core.ios_collector import IOSCollector
from core.performance_analyzer import PerformanceAnalyzer
from core.report_generator import ReportGenerator
from core.notification_service import notification_service, NotificationType, NotificationPriority
from core.exceptions import MobiPerfException
from core.auth import get_current_active_user
from database.db_manager import DatabaseManager, PerformanceDataRepository
from core.config_loader import config
from loguru import logger
from typing import Union
import uuid
from datetime import datetime
from routes.collaboration import router as collaboration_router
from routes.notifications import router as notification_router
from routes.auth import router as auth_router
from middleware.error_handler import (
    mobiperf_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from middleware.request_id import RequestIDMiddleware
from middleware.rate_limit import RateLimitMiddleware
from models.schemas import (
    DeviceListResponse, DeviceInfo,
    AppListResponse, AppInfo,
    SessionListResponse, SessionInfo,
    RecordListResponse, RecordFile,
    HealthCheckResponse
)
from core.auth import get_current_active_user
from core.logging_config import setup_logging
from core.cache import Cache

setup_logging(log_level=config.LOG_LEVEL, enable_file_log=config.logging.file_enabled)

db_manager = DatabaseManager(config.DATABASE_CONFIG)
repository = None
cache = Cache()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global repository
    try:
        await db_manager.init_pool()
        repository = PerformanceDataRepository(db_manager)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Running without database persistence")
        repository = None
    
    await cache.init()
    
    yield
    
    await cache.close()
    await db_manager.close_pool()
    logger.info("Database connection closed")

app = FastAPI(
    title="MobiPerf API",
    lifespan=lifespan,
    description="""
## MobiPerf 移动端性能测试工具 API

MobiPerf 是一个开源、免费的移动端性能测试工具，支持 Android 和 iOS 设备。

### 主要功能

- 🔍 **设备管理**：自动识别和管理连接的设备
- 📊 **性能监控**：实时采集 FPS、CPU、内存、GPU 等指标
- 📈 **数据分析**：性能评分、趋势预测
- 📝 **报告生成**：自动生成专业的 HTML 性能报告
- 🔔 **智能通知**：可配置的通知系统和告警阈值

### 快速开始

1. 连接设备并开启调试模式
2. 访问 `/api/devices` 获取设备列表
3. 通过 WebSocket `/ws/monitor/{serial}` 开始实时监控
4. 生成并下载性能报告

### WebSocket 接口

WebSocket 端点：`ws://localhost:8000/ws/monitor/{device_serial}`

支持的消息类型：
- `start` - 开始监控
- `stop` - 停止监控
- `record` - 开始录制
- `generate_report` - 生成报告
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "MobiPerf Team",
        "url": "https://github.com/yourusername/MobiPerf",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_exception_handler(MobiPerfException, mobiperf_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)

app.include_router(auth_router)
app.include_router(collaboration_router)
app.include_router(notification_router)

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="检查服务运行状态",
    tags=["系统"]
)
async def health_check():
    """健康检查端点
    
    Returns:
        服务状态、数据库连接状态和当前时间戳
    """
    return {
        "status": "healthy",
        "database": "connected" if repository else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.get(
    "/api/cache/stats",
    summary="获取缓存统计信息",
    description="获取Redis缓存的使用统计信息",
    tags=["系统"]
)
async def get_cache_stats():
    """获取缓存统计信息
    
    Returns:
        缓存后端类型、连接状态、键数量和内存使用情况
    """
    stats = await cache.get_stats()
    return {
        "backend": "redis" if cache._use_redis else "memory",
        **stats
    }

@app.post(
    "/api/cache/clear",
    summary="清除缓存",
    description="清除所有缓存数据",
    tags=["系统"]
)
async def clear_cache(current_user: Dict = Depends(get_current_active_user)):
    """清除缓存
    
    Returns:
        成功消息
    """
    await cache.clear()
    return {"message": "缓存已清除"}

# Ensure static/screenshots exists
SCREENSHOT_DIR = "static/screenshots"
if os.path.exists(SCREENSHOT_DIR):
    shutil.rmtree(SCREENSHOT_DIR)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

app.mount("/screenshots", StaticFiles(directory=SCREENSHOT_DIR), name="screenshots")

# Ensure static/records exists and mount
RECORD_DIR = "static/records"
os.makedirs(RECORD_DIR, exist_ok=True)
app.mount("/records", StaticFiles(directory=RECORD_DIR), name="records")

# Ensure reports directory exists and mount
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)
app.mount("/reports", StaticFiles(directory=REPORT_DIR), name="reports")

# Ensure logs directory exists and mount
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
app.mount("/logs", StaticFiles(directory=LOG_DIR), name="logs")

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储活跃的采集器实例
collectors: Dict[str, Union[AndroidCollector, IOSCollector]] = {}

def get_device(serial: str):
    """根据序列号获取设备对象
    
    Args:
        serial: 设备序列号
        
    Returns:
        设备对象，如果未找到返回 None
    """
    try:
        # Check if it's an iOS device
        if len(serial) > 20 or "-" in serial:
            return serial  # For iOS, just return the serial
        
        # For Android devices
        for d in adb.device_list():
            if d.serial == serial:
                return d
        
        return None
    except Exception as e:
        logger.error(f"Failed to get device {serial}: {e}")
        return None

@app.get(
    "/api/devices",
    response_model=DeviceListResponse,
    summary="获取设备列表",
    description="返回所有已连接的 Android 和 iOS 设备列表",
    tags=["设备管理"]
)
async def get_devices(current_user: Dict = Depends(get_current_active_user)):
    """获取连接的设备列表
    
    返回当前连接的所有 Android 和 iOS 设备信息，包括：
    - 设备序列号
    - 设备型号
    - 平台类型
    - 连接状态
    """
    cache_cfg = config.get_cache_key("devices")
    cached = await cache.get(cache_cfg.key)
    if cached is not None:
        logger.debug("Returning cached device list")
        return {"devices": cached}
    
    devices = []
    
    try:
        for d in adb.device_list():
            manufacturer = d.prop.get("ro.product.manufacturer", "")
            model = d.prop.model
            name = f"{manufacturer} {model}".strip()
            
            devices.append({
                "serial": d.serial,
                "model": name,
                "platform": "android",
                "status": "online"
            })
    except Exception as e:
        logger.error(f"Failed to list Android devices: {e}")

    try:
        ios_devices = IOSCollector.get_connected_devices()
        for d in ios_devices:
            devices.append({
                "serial": d["serial"],
                "name": d.get("model", "iOS Device"),
                "model": d.get("model", "iOS Device"),
                "platform": "ios",
                "status": "online"
            })
    except Exception as e:
        logger.error(f"Failed to list iOS devices: {e}")
    
    await cache.set(cache_cfg.key, devices, cache_cfg.ttl)
        
    return {"devices": devices}

@app.get(
    "/api/apps/{serial}",
    response_model=AppListResponse,
    summary="获取应用列表",
    description="获取指定设备上安装的应用列表",
    tags=["设备管理"]
)
async def get_apps(
    serial: str,
    platform: str = "android",
    current_user: Dict = Depends(get_current_active_user)
):
    """获取设备上安装的应用列表
    
    Args:
        serial: 设备序列号
        platform: 平台类型
        
    Returns:
        应用列表，包含包名和应用名称
    """
    cache_cfg = config.get_cache_key("apps")
    cache_key = cache_cfg.key.format(serial=serial)
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Returning cached app list for {serial}")
        return {"apps": cached}
    
    if platform == "ios" or (len(serial) > 20 or "-" in serial):
        apps = IOSCollector.get_installed_apps(serial)
    else:
        apps = AndroidCollector.get_installed_apps(serial)
    
    await cache.set(cache_key, apps, cache_cfg.ttl)
    return {"apps": apps}

@app.get(
    "/api/current-app/{serial}",
    summary="获取当前前台应用",
    description="获取设备当前前台运行的应用包名",
    tags=["设备管理"]
)
async def get_current_app(serial: str, current_user: Dict = Depends(get_current_active_user)):
    """获取设备当前前台运行的应用
    
    Args:
        serial: 设备序列号
        
    Returns:
        当前前台应用的包名
    """
    try:
        if len(serial) > 20 or "-" in serial:
            return {"package": None, "error": "iOS not supported"}
        
        device = get_device(serial)
        if not device:
            return {"package": None, "error": "Device not found"}
        
        collector = AndroidCollector(device)
        package = collector._get_top_package()
        
        return {"package": package, "error": None}
    except Exception as e:
        logger.error(f"Failed to get current app: {e}")
        return {"package": None, "error": str(e)}

@app.post(
    "/api/screenshot/{serial}",
    summary="截取设备屏幕",
    description="截取指定设备的当前屏幕并保存",
    tags=["设备管理"]
)
async def take_screenshot(serial: str, current_user: Dict = Depends(get_current_active_user)):
    """截取设备屏幕
    
    Args:
        serial: 设备序列号
        
    Returns:
        截图文件的URL和保存路径
    """
    try:
        device = get_device(serial)
        if not device:
            return {"success": False, "error": "Device not found"}
        
        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}.png"
        screenshot_dir_serial = os.path.join(SCREENSHOT_DIR, serial)
        os.makedirs(screenshot_dir_serial, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir_serial, filename)
        
        if len(serial) > 20 or "-" in serial:
            # iOS device
            import subprocess
            result = subprocess.run(
                ['idevicescreenshot', '-u', serial, screenshot_path],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"iOS screenshot failed: {result.stderr}")
                return {"success": False, "error": result.stderr}
        else:
            # Android device
            device.shell(f"screencap -p /sdcard/{filename}")
            device.sync.pull(f"/sdcard/{filename}", screenshot_path)
            device.shell(f"rm /sdcard/{filename}")
        
        screenshot_url = f"/screenshots/{serial}/{filename}"
        
        return {
            "success": True,
            "url": screenshot_url,
            "filename": filename,
            "timestamp": timestamp
        }
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return {"success": False, "error": str(e)}

@app.get(
    "/api/screenshots/{serial}",
    summary="获取截图列表",
    description="获取指定设备的所有截图",
    tags=["设备管理"]
)
async def list_screenshots(serial: str, current_user: Dict = Depends(get_current_active_user)):
    """获取设备的截图列表
    
    Args:
        serial: 设备序列号
        
    Returns:
        截图文件列表，包含文件名、URL、大小和时间
    """
    screenshot_dir_serial = os.path.join(SCREENSHOT_DIR, serial)
    if not os.path.exists(screenshot_dir_serial):
        return {"screenshots": []}
    
    screenshots = []
    try:
        for f in os.listdir(screenshot_dir_serial):
            if f.endswith(".png"):
                fp = os.path.join(screenshot_dir_serial, f)
                stat = os.stat(fp)
                screenshots.append({
                    "filename": f,
                    "url": f"/screenshots/{serial}/{f}",
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        screenshots.sort(key=lambda x: x['created_at'], reverse=True)
        return {"screenshots": screenshots}
    except Exception as e:
        logger.error(f"Failed to list screenshots: {e}")
        return {"screenshots": [], "error": str(e)}

@app.delete(
    "/api/screenshots/{serial}/{filename}",
    summary="删除截图",
    description="删除指定的截图文件",
    tags=["设备管理"]
)
async def delete_screenshot(serial: str, filename: str, current_user: Dict = Depends(get_current_active_user)):
    """删除截图文件
    
    Args:
        serial: 设备序列号
        filename: 截图文件名
        
    Returns:
        删除结果
    """
    try:
        screenshot_path = os.path.join(SCREENSHOT_DIR, serial, filename)
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            return {"success": True, "message": "Screenshot deleted"}
        else:
            return {"success": False, "error": "Screenshot not found"}
    except Exception as e:
        logger.error(f"Failed to delete screenshot: {e}")
        return {"success": False, "error": str(e)}

# Screen recording state management
recording_processes = {}

@app.post(
    "/api/screenrecord/start/{serial}",
    summary="开始录屏",
    description="开始录制设备屏幕",
    tags=["设备管理"]
)
async def start_screenrecord(serial: str, current_user: Dict = Depends(get_current_active_user)):
    """开始录屏
    
    Args:
        serial: 设备序列号
        
    Returns:
        录屏开始状态
    """
    try:
        if serial in recording_processes:
            return {"success": False, "error": "Recording already in progress"}
        
        device = get_device(serial)
        if not device:
            return {"success": False, "error": "Device not found"}
        
        if len(serial) > 20 or "-" in serial:
            return {"success": False, "error": "iOS screen recording not supported yet"}
        
        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}.mp4"
        video_dir_serial = os.path.join(SCREENSHOT_DIR, serial, "videos")
        os.makedirs(video_dir_serial, exist_ok=True)
        video_path = os.path.join(video_dir_serial, filename)
        
        # Start screen recording on device
        device.shell(f"screenrecord /sdcard/{filename} &")
        
        recording_processes[serial] = {
            "filename": filename,
            "start_time": timestamp,
            "video_path": video_path
        }
        
        return {
            "success": True,
            "message": "Recording started",
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Failed to start screen recording: {e}")
        return {"success": False, "error": str(e)}

@app.post(
    "/api/screenrecord/stop/{serial}",
    summary="停止录屏",
    description="停止录制设备屏幕并保存视频",
    tags=["设备管理"]
)
async def stop_screenrecord(serial: str, current_user: Dict = Depends(get_current_active_user)):
    """停止录屏
    
    Args:
        serial: 设备序列号
        
    Returns:
        录屏文件URL和保存路径
    """
    try:
        if serial not in recording_processes:
            return {"success": False, "error": "No recording in progress"}
        
        recording = recording_processes[serial]
        filename = recording["filename"]
        video_path = recording["video_path"]
        
        device = get_device(serial)
        if not device:
            return {"success": False, "error": "Device not found"}
        
        # Stop recording by killing the process
        device.shell("pkill -SIGINT screenrecord")
        time.sleep(2)  # Wait for recording to finish
        
        # Pull the video file
        device.sync.pull(f"/sdcard/{filename}", video_path)
        device.shell(f"rm /sdcard/{filename}")
        
        del recording_processes[serial]
        
        video_url = f"/screenshots/{serial}/videos/{filename}"
        
        return {
            "success": True,
            "url": video_url,
            "filename": filename,
            "duration": int(time.time() * 1000) - recording["start_time"]
        }
    except Exception as e:
        logger.error(f"Failed to stop screen recording: {e}")
        if serial in recording_processes:
            del recording_processes[serial]
        return {"success": False, "error": str(e)}

@app.get(
    "/api/videos/{serial}",
    summary="获取录屏列表",
    description="获取指定设备的所有录屏文件",
    tags=["设备管理"]
)
async def list_videos(serial: str, current_user: Dict = Depends(get_current_active_user)):
    """获取设备的录屏列表
    
    Args:
        serial: 设备序列号
        
    Returns:
        录屏文件列表，包含文件名、URL、大小和时间
    """
    video_dir_serial = os.path.join(SCREENSHOT_DIR, serial, "videos")
    if not os.path.exists(video_dir_serial):
        return {"videos": []}
    
    videos = []
    try:
        for f in os.listdir(video_dir_serial):
            if f.endswith(".mp4"):
                fp = os.path.join(video_dir_serial, f)
                stat = os.stat(fp)
                videos.append({
                    "filename": f,
                    "url": f"/screenshots/{serial}/videos/{f}",
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        videos.sort(key=lambda x: x['created_at'], reverse=True)
        return {"videos": videos}
    except Exception as e:
        logger.error(f"Failed to list videos: {e}")
        return {"videos": [], "error": str(e)}

@app.delete(
    "/api/videos/{serial}/{filename}",
    summary="删除录屏",
    description="删除指定的录屏文件",
    tags=["设备管理"]
)
async def delete_video(serial: str, filename: str, current_user: Dict = Depends(get_current_active_user)):
    """删除录屏文件
    
    Args:
        serial: 设备序列号
        filename: 录屏文件名
        
    Returns:
        删除结果
    """
    try:
        video_path = os.path.join(SCREENSHOT_DIR, serial, "videos", filename)
        if os.path.exists(video_path):
            os.remove(video_path)
            return {"success": True, "message": "Video deleted"}
        else:
            return {"success": False, "error": "Video not found"}
    except Exception as e:
        logger.error(f"Failed to delete video: {e}")
        return {"success": False, "error": str(e)}

@app.get(
    "/api/records/{serial}",
    response_model=RecordListResponse,
    summary="获取录制文件列表",
    description="获取指定设备的性能数据录制文件列表",
    tags=["数据管理"]
)
async def list_records(serial: str, current_user: Dict = Depends(get_current_active_user)):
    """获取设备的录制文件列表
    
    Args:
        serial: 设备序列号
        
    Returns:
        CSV 录制文件列表，包含文件名、大小、修改时间和下载链接
    """
    record_dir_serial = os.path.join(RECORD_DIR, serial)
    if not os.path.exists(record_dir_serial):
        return {"files": []}
    
    files = []
    try:
        for f in os.listdir(record_dir_serial):
            if f.endswith(".csv"):
                fp = os.path.join(record_dir_serial, f)
                stat = os.stat(fp)
                files.append({
                    "name": f,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "url": f"/records/{serial}/{f}"
                })
        # Sort by mtime desc
        files.sort(key=lambda x: x["mtime"], reverse=True)
    except Exception as e:
        logger.error(f"List records error: {e}")
        
    return {"files": files}

@app.get(
    "/api/sessions",
    response_model=SessionListResponse,
    summary="获取测试会话列表",
    description="获取历史测试会话记录",
    tags=["数据管理"]
)
async def get_sessions(limit: int = 50, offset: int = 0):
    """获取测试会话列表
    
    Args:
        limit: 返回数量限制，默认 50
        offset: 偏移量，用于分页
        
    Returns:
        测试会话列表，包含会话信息、设备信息、测试时长等
    """
    if not repository:
        return {"sessions": [], "error": "Database not initialized"}
    
    try:
        sessions = await repository.get_test_sessions(limit, offset)
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        return {"sessions": [], "error": str(e)}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """获取单个测试会话详情"""
    if not repository:
        return {"error": "Database not initialized"}
    
    try:
        session = await repository.get_session_by_id(session_id)
        if not session:
            return {"error": "Session not found"}
        
        stats = await repository.get_session_statistics(session_id)
        analysis = await repository.get_comprehensive_analysis(session_id)
        
        return {
            "session": session,
            "statistics": stats,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        return {"error": str(e)}

@app.get("/api/sessions/{session_id}/metrics")
async def get_session_metrics(session_id: str, limit: int = 1000):
    """获取测试会话的性能指标数据"""
    if not repository:
        return {"metrics": [], "error": "Database not initialized"}
    
    try:
        metrics = await repository.get_performance_metrics(session_id, limit)
        return {"metrics": metrics, "total": len(metrics)}
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {"metrics": [], "error": str(e)}

@app.post("/api/sessions/search")
async def search_sessions(filters: Dict):
    """搜索测试会话"""
    if not repository:
        return {"sessions": [], "error": "Database not initialized"}
    
    try:
        sessions = await repository.search_sessions(filters)
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        logger.error(f"Failed to search sessions: {e}")
        return {"sessions": [], "error": str(e)}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除测试会话"""
    if not repository:
        return {"success": False, "error": "Database not initialized"}
    
    try:
        success = await repository.delete_session(session_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        return {"success": False, "error": str(e)}

@app.websocket("/ws/monitor/{serial}")
async def websocket_endpoint(websocket: WebSocket, serial: str):
    logger.info(f"Accepting WebSocket connection for device: {serial}")
    await websocket.accept()
    
    platform = "android"
    if len(serial) > 20 or "-" in serial:
        platform = "ios"
        
    logger.info(f"WebSocket connected for device: {serial} ({platform})")

    if serial in collectors:
        logger.warning(f"Collector already exists for {serial}, stopping old one")
        collectors[serial].stop()
        del collectors[serial]

    if platform == "android":
        collector = AndroidCollector(serial)
    else:
        collector = IOSCollector(serial)
    
    collectors[serial] = collector

    data_queue = asyncio.Queue()
    
    analyzer = PerformanceAnalyzer(window_size=60)
    last_analysis_time = time.time()
    analysis_interval = 5
    
    report_generator = ReportGenerator()
    
    session_id = str(uuid.uuid4())
    session_start_time = None
    session_created = False
    
    csv_file = None
    csv_writer = None
    
    def queue_callback(data):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(data_queue.put_nowait, data)
        except RuntimeError:
             pass

    collector.set_callback(queue_callback)
    
    # Defer start until receiving 'start' message to allow target package/bundle id to be set
    # Prepare recording resources
    record_dir_serial = os.path.join(RECORD_DIR, serial)
    os.makedirs(record_dir_serial, exist_ok=True)
    record_fp = None
    record_writer = None

    try:
        while True:
            # 使用 asyncio.gather 同时等待 队列数据 和 WS 消息
            # 但为了简化，我们可以用 wait task
            
            # 创建读取 WS 的 task
            recv_task = asyncio.create_task(websocket.receive_json())
            # 创建读取 Queue 的 task
            queue_task = asyncio.create_task(data_queue.get())
            
            done, pending = await asyncio.wait(
                [recv_task, queue_task], 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                if task == queue_task:
                    # 发送采集数据
                    data = task.result()
                    await websocket.send_json(data)
                    
                    if isinstance(data, dict) and data.get("type") == "monitor":
                        analyzer.add_metrics(data)
                        
                        if repository and session_created:
                            try:
                                await repository.save_performance_metrics(session_id, data)
                                
                                if not target and data.get("package"):
                                    target = data.get("package")
                                    await repository.update_test_session(session_id, {
                                        'app_package': target
                                    })
                                    logger.info(f"Updated session {session_id} with package: {target}")
                            except Exception as e:
                                logger.error(f"Failed to save metrics to database: {e}")
                        
                        # 定期发送性能分析结果
                        current_time = time.time()
                        if current_time - last_analysis_time >= analysis_interval:
                            analysis_result = analyzer.get_comprehensive_analysis()
                            await websocket.send_json({
                                "type": "analysis",
                                "timestamp": int(current_time * 1000),
                                "data": analysis_result
                            })
                            
                            # 保存分析结果到数据库
                            if repository and session_created:
                                try:
                                    await repository.save_fps_analysis(session_id, analysis_result.get('fps', {}))
                                    await repository.save_memory_analysis(session_id, analysis_result.get('memory', {}))
                                    await repository.save_comprehensive_analysis(session_id, analysis_result)
                                except Exception as e:
                                    logger.error(f"Failed to save analysis to database: {e}")
                            
                            last_analysis_time = current_time
                    
                    # Write CSV when recording and monitor payload
                    if record_writer and isinstance(data, dict) and data.get("type") == "monitor":
                        row = [
                            data.get("timestamp"),
                            data.get("package"),
                            data.get("cpu"),
                            data.get("memory"),
                            data.get("fps"),
                            data.get("jank"),
                            data.get("stutter"),
                            data.get("gpu"),
                            data.get("battery", {}).get("level"),
                            data.get("battery", {}).get("voltage"),
                            data.get("battery", {}).get("temp"),
                            data.get("battery", {}).get("current"),
                            data.get("network", {}).get("rx"),
                            data.get("network", {}).get("tx"),
                        ]
                        try:
                            record_writer.writerow(row)
                            if record_fp:
                                record_fp.flush()
                        except Exception as e:
                            logger.error(f"Record write error: {e}")
                    
                    if isinstance(data, dict) and data.get("type") == "monitor":
                        await notification_service.check_performance_thresholds(data, serial)
                elif task == recv_task:
                    # 处理客户端指令
                    msg = task.result()
                    # 比如 {"type": "start", "target": "com.example"}
                    logger.info(f"Received message: {msg}")
                    
                    if msg.get("type") == "start":
                        logger.info(f"Processing start message, repository={repository is not None}")
                        target = msg.get("target")
                        collector.set_target(target)
                        if not collector.running:
                            await collector.start()
                        
                        # 创建数据库会话
                        if repository:
                            try:
                                session_start_time = datetime.now()
                                logger.info(f"Creating database session: session_id={session_id}, device_model={collector.device_model if hasattr(collector, 'device_model') else 'Unknown'}, serial={serial}, target={target}")
                                created_id = await repository.create_test_session({
                                    'session_id': session_id,
                                    'device_model': collector.device_model if hasattr(collector, 'device_model') else 'Unknown',
                                    'device_serial': serial,
                                    'app_package': target,
                                    'start_time': session_start_time
                                })
                                if created_id:
                                    session_created = True
                                    logger.info(f"✅ Created database session: {session_id}")
                                else:
                                    logger.warning(f"❌ Failed to create database session: {session_id}, created_id is None or False")
                            except Exception as e:
                                logger.error(f"❌ Exception creating database session: {e}", exc_info=True)
                        else:
                            logger.warning(f"⚠️ Repository is None, cannot create database session")
                        
                        # initialize CSV recorder
                        try:
                            ts_name = str(int(time.time() * 1000))
                            base_name = f"{ts_name}_{target or 'unknown'}.csv"
                            file_path = os.path.join(record_dir_serial, base_name)
                            record_fp = open(file_path, "w", newline="", encoding="utf-8")
                            record_writer = csv.writer(record_fp)
                            record_writer.writerow([
                                "timestamp","package","cpu(%)","memory(MB)","fps","jank","stutter(%)",
                                "gpu(%)","battery.level","battery.voltage(mV)","battery.temp(C)",
                                "battery.current(mA)","network.rx(KB/s)","network.tx(KB/s)"
                            ])
                            logger.info(f"Recording to {file_path}")
                        except Exception as e:
                            logger.error(f"Failed to init recording: {e}")
                    elif msg.get("type") == "stop":
                        logger.info(f"Received stop message, repository={repository is not None}, session_created={session_created}, session_id={session_id}")
                        collector.stop()
                        # 重置性能分析器
                        analyzer.reset()
                        
                        # 更新数据库会话状态
                        if repository and session_created:
                            try:
                                end_time = datetime.now()
                                duration = int((end_time - session_start_time).total_seconds()) if session_start_time else 0
                                logger.info(f"Updating session {session_id}: end_time={end_time}, duration={duration}")
                                await repository.update_test_session(session_id, {
                                    'end_time': end_time,
                                    'status': 'completed',
                                    'duration': duration
                                })
                                logger.info(f"Updated database session: {session_id}, duration: {duration}s")
                            except Exception as e:
                                logger.error(f"Failed to update database session: {e}")
                        else:
                            logger.warning(f"Cannot update session: repository={repository is not None}, session_created={session_created}")
                        
                        session_created = False
                        
                        # finalize CSV
                        try:
                            if record_fp:
                                record_fp.flush()
                                record_fp.close()
                        except Exception:
                            pass
                        record_fp = None
                        record_writer = None
                    elif msg.get("type") == "generate_report":
                        # 生成性能报告
                        try:
                            # 检查是否有足够的分析数据
                            if analyzer.data_count < 5:
                                await websocket.send_json({
                                    "type": "error",
                                    "error_type": "insufficient_data",
                                    "message": "数据不足，无法生成报告",
                                    "details": "请至少收集 5 秒的性能数据后再生成报告"
                                })
                                continue
                            
                            analysis_result = analyzer.get_comprehensive_analysis()
                            device_model = msg.get("device_model", "Unknown Device")
                            app_package = msg.get("app_package", "Unknown App")
                            
                            # 生成 HTML 报告
                            generate_result = report_generator.generate_html_report(
                                analysis_result, device_model, app_package
                            )
                            
                            if not generate_result['success']:
                                await websocket.send_json({
                                    "type": "error",
                                    "error_type": generate_result['error_type'],
                                    "message": generate_result['message'],
                                    "details": generate_result['details']
                                })
                                continue
                            
                            html_content = generate_result['html_content']
                            
                            # 保存报告
                            report_dir = "reports"
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            report_filename = f"report_{device_model}_{timestamp}.html"
                            
                            save_result = report_generator.save_report(
                                html_content, report_dir, report_filename
                            )
                            
                            if not save_result['success']:
                                await websocket.send_json({
                                    "type": "error",
                                    "error_type": save_result['error_type'],
                                    "message": save_result['message'],
                                    "details": save_result['details']
                                })
                                continue
                            
                            report_path = save_result['filepath']
                            logger.info(f"Report generated: {report_path}")
                            
                            # 发送报告路径给前端
                            await websocket.send_json({
                                "type": "report_generated",
                                "report_url": f"/reports/{report_filename}",
                                "report_path": report_path,
                                "message": "报告生成成功"
                            })
                            
                        except Exception as e:
                            logger.error(f"Failed to generate report: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "error_type": "unknown_error",
                                "message": "报告生成失败",
                                "details": f"发生未知错误: {str(e)}"
                            })

            # 取消未完成的任务
            for task in pending:
                task.cancel()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {serial}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info(f"Cleaning up WebSocket for {serial}, session_created={session_created}, session_id={session_id}")
        collector.stop()
        
        # Update session status when WebSocket disconnects
        if repository and session_created and session_id:
            try:
                end_time = datetime.now()
                duration = int((end_time - session_start_time).total_seconds()) if session_start_time else 0
                logger.info(f"Updating session {session_id} on disconnect: end_time={end_time}, duration={duration}")
                await repository.update_test_session(session_id, {
                    'end_time': end_time,
                    'status': 'completed',
                    'duration': duration
                })
                logger.info(f"Updated session {session_id} on WebSocket disconnect")
            except Exception as e:
                logger.error(f"Failed to update session on disconnect: {e}")
        
        try:
            if record_fp:
                record_fp.flush()
                record_fp.close()
        except Exception:
            pass
        if serial in collectors:
            del collectors[serial]

@app.websocket("/ws/multi-monitor")
async def multi_device_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Multi-device WebSocket connected")
    
    active_collectors: Dict[str, Union[AndroidCollector, IOSCollector]] = {}
    data_queues: Dict[str, asyncio.Queue] = {}
    session_ids: Dict[str, str] = {}
    
    try:
        async def handle_device_data(serial: str, queue: asyncio.Queue):
            while True:
                try:
                    data = await queue.get()
                    await websocket.send_json({
                        "type": "data",
                        "serial": serial,
                        "data": data
                    })
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error handling data for {serial}: {e}")
                    break
        
        async for message in websocket.iter_json():
            try:
                msg_type = message.get("type")
                
                if msg_type == "start_device":
                    serial = message.get("serial")
                    target = message.get("target")
                    
                    if serial in active_collectors:
                        await websocket.send_json({
                            "type": "error",
                            "serial": serial,
                            "error": {
                                "error_type": "device_already_active",
                                "message": f"设备 {serial} 已在监控中"
                            }
                        })
                        continue
                    
                    platform = "android"
                    if len(serial) > 20 or "-" in serial:
                        platform = "ios"
                    
                    if platform == "android":
                        collector = AndroidCollector(serial)
                    else:
                        collector = IOSCollector(serial)
                    
                    active_collectors[serial] = collector
                    data_queues[serial] = asyncio.Queue()
                    session_ids[serial] = str(uuid.uuid4())
                    
                    def queue_callback(data):
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                loop.call_soon_threadsafe(data_queues[serial].put_nowait, data)
                        except RuntimeError:
                            pass
                    
                    collector.set_callback(queue_callback)
                    
                    if platform == "android":
                        collector.set_target(target)
                        await collector.start()
                    else:
                        collector.set_target(target)
                        await collector.start()
                    
                    asyncio.create_task(handle_device_data(serial, data_queues[serial]))
                    
                    await websocket.send_json({
                        "type": "device_started",
                        "serial": serial,
                        "session_id": session_ids[serial]
                    })
                    
                    logger.info(f"Started monitoring device: {serial}")
                
                elif msg_type == "stop_device":
                    serial = message.get("serial")
                    
                    if serial in active_collectors:
                        active_collectors[serial].stop()
                        del active_collectors[serial]
                        del data_queues[serial]
                        del session_ids[serial]
                        
                        await websocket.send_json({
                            "type": "device_stopped",
                            "serial": serial
                        })
                        
                        logger.info(f"Stopped monitoring device: {serial}")
                
                elif msg_type == "get_status":
                    await websocket.send_json({
                        "type": "status",
                        "active_devices": list(active_collectors.keys())
                    })
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": {
                        "error_type": "message_processing_error",
                        "message": str(e)
                    }
                })
    
    except WebSocketDisconnect:
        logger.info("Multi-device WebSocket disconnected")
    except Exception as e:
        logger.error(f"Multi-device WebSocket error: {e}")
    finally:
        for serial, collector in active_collectors.items():
            try:
                collector.stop()
            except Exception as e:
                logger.error(f"Error stopping collector {serial}: {e}")
        active_collectors.clear()
        data_queues.clear()
        session_ids.clear()

@app.websocket("/ws/notifications")
async def notification_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Notification WebSocket connected")
    
    async def send_notification(notification: Dict):
        try:
            await websocket.send_json({
                "type": "notification",
                "data": notification
            })
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    notification_service.register_websocket_callback(send_notification)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Notification WebSocket connected successfully",
            "unread_count": notification_service.get_unread_count()
        })
        
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "mark_read":
                    notification_id = data.get("notification_id")
                    if notification_id:
                        notification_service.mark_as_read(notification_id)
                        await websocket.send_json({
                            "type": "marked_read",
                            "notification_id": notification_id
                        })
                elif data.get("type") == "mark_all_read":
                    count = notification_service.mark_all_as_read()
                    await websocket.send_json({
                        "type": "all_marked_read",
                        "count": count
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing notification message: {e}")
    
    except WebSocketDisconnect:
        logger.info("Notification WebSocket disconnected")
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}")
    finally:
        notification_service.unregister_websocket_callback(send_notification)

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve frontend SPA"""
    frontend_index = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {"error": "Frontend not found. Please build the frontend first."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
