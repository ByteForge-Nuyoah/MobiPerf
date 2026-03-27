# MobiPerf 🚀

<p align="center">
  <strong>开源、免费的移动端性能测试工具</strong>
</p>

<p align="center">
  <a href="#-核心特性">核心特性</a> •
  <a href="#-技术栈">技术栈</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-使用指南">使用指南</a> •
  <a href="#-api-文档">API 文档</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3.2+-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/Platform-Android%20%7C%20iOS-brightgreen.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 📑 目录

- [核心特性](#-核心特性)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
  - [前置要求](#前置要求)
  - [方式一：一键启动](#方式一一键启动推荐)
  - [方式二：手动启动](#方式二手动启动)
- [使用指南](#-使用指南)
- [配置说明](#️-配置说明)
- [API 文档](#-api-文档)
- [常见问题](#-常见问题)
- [贡献指南](#-贡献指南)
- [开源协议](#-开源协议)

---

## ✨ 核心特性

### 🎯 实时性能监控

| 指标 | 描述 |
|------|------|
| **FPS 监控** | 实时帧率、卡顿检测 |
| **CPU 监控** | CPU 使用率、趋势分析 |
| **内存监控** | 内存占用、内存泄漏检测 |
| **GPU 监控** | GPU 使用率、渲染性能 |
| **电池监控** | 电量、温度、电压、电流 |
| **网络监控** | 上下行流量统计 |

### 📊 专业分析功能

- **性能评分**：综合性能评分系统
- **趋势分析**：CPU、内存、温度趋势预测
- **风险预警**：内存泄漏风险、温度过高预警

### 🔔 智能通知系统

- **可配置通知类型**：FPS、CPU、内存、温度等
- **多级优先级**：低、中、高、紧急
- **实时推送**：WebSocket 实时通知
- **阈值触发**：自定义告警阈值

### 📈 数据可视化

- **实时曲线图**：多指标实时展示
- **设备截图**：实时屏幕截图
- **历史对比**：历史数据对比分析

### 📝 报告生成

- **HTML 报告**：专业性能测试报告
- **数据导出**：CSV 格式原始数据
- **图表导出**：PNG 格式图表
- **一键下载**：浏览器直接下载

### 📱 多设备支持

- **多设备监控**：同时监控多台设备
- **设备管理**：设备热插拔自动识别
- **平台支持**：Android 5.0+、iOS 12.0+

---

## 🛠️ 技术栈

### 后端

| 技术 | 版本 | 描述 |
|------|------|------|
| [Python](https://www.python.org/) | 3.8+ | 主要开发语言 |
| [FastAPI](https://fastapi.tiangolo.com/) | Latest | 高性能 Web 框架 |
| [Uvicorn](https://www.uvicorn.org/) | Latest | ASGI 服务器 |
| [WebSockets](https://websockets.readthedocs.io/) | Latest | 实时通信 |
| [adbutils](https://github.com/openatx/adbutils) | Latest | Android 调试桥 |
| [tidevice](https://github.com/alibaba/tidevice) | Latest | iOS 设备通信 |
| [aiomysql](https://aiomysql.readthedocs.io/) | Latest | 异步 MySQL |
| [PyJWT](https://pyjwt.readthedocs.io/) | Latest | JWT 认证 |
| [Pydantic](https://pydantic-docs.helpmanual.io/) | Latest | 数据验证 |

### 前端

| 技术 | 版本 | 描述 |
|------|------|------|
| [Vue 3](https://vuejs.org/) | 3.2+ | 渐进式 JavaScript 框架 |
| [Vite](https://vitejs.dev/) | 4.2+ | 下一代前端构建工具 |
| [ECharts](https://echarts.apache.org/) | 5.4+ | 数据可视化图表库 |
| [Axios](https://axios-http.com/) | 1.3+ | HTTP 客户端 |

---

## 🏗️ 项目结构

```
MobiPerf/
├── backend/                    # Python 后端服务
│   ├── core/                   # 核心功能模块
│   │   ├── android_collector.py    # Android 数据采集
│   │   ├── ios_collector.py        # iOS 数据采集
│   │   ├── performance_analyzer.py # 性能分析器
│   │   ├── notification_service.py # 通知服务
│   │   └── report_generator.py     # 报告生成器
│   ├── database/               # 数据库模块
│   │   ├── db_manager.py          # 数据库管理
│   │   ├── schema.sql             # 数据库结构
│   │   └── collaboration_*.py     # 协作功能
│   ├── routes/                 # API 路由
│   │   ├── auth.py                # 认证 API
│   │   ├── notifications.py       # 通知 API
│   │   └── collaboration.py       # 协作 API
│   ├── middleware/             # 中间件
│   │   └── error_handler.py       # 错误处理
│   ├── models/                 # 数据模型
│   │   └── schemas.py             # Pydantic 模型
│   ├── templates/              # 报告模板
│   ├── reports/                # 生成的报告
│   ├── main.py                 # 后端入口
│   ├── config.py               # 配置文件
│   ├── init_db.py              # 数据库初始化
│   ├── init_admin.py           # 管理员初始化
│   └── requirements.txt        # Python 依赖
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   │   ├── MonitorChart.vue        # 监控图表
│   │   │   ├── PerformanceAnalysis.vue # 性能分析
│   │   │   ├── NotificationCenter.vue  # 通知中心
│   │   │   ├── MultiDeviceMonitor.vue  # 多设备监控
│   │   │   └── HistoryView.vue         # 历史记录
│   │   ├── styles/             # 样式文件
│   │   ├── App.vue             # 主应用
│   │   └── main.js             # 入口文件
│   ├── index.html
│   ├── vite.config.js          # Vite 配置
│   └── package.json
├── .github/
│   └── workflows/
│       └── ci.yml              # CI 配置
├── docs/                       # 文档
├── run.sh                      # 启动脚本
└── README.md                   # 项目说明
```

---

## 🚀 快速开始

### 前置要求

| 工具 | 版本要求 | 检查命令 |
|------|----------|----------|
| Python | 3.8+ | `python --version` |
| Node.js | 16+ | `node --version` |
| ADB | Latest | `adb version` |
| MySQL | 5.7+ (可选) | `mysql --version` |

#### 安装 ADB

**macOS:**
```bash
brew install android-platform-tools
```

**Windows:**
下载 [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)

**Linux:**
```bash
sudo apt-get install android-tools-adb
```

### 方式一：一键启动（推荐）

```bash
git clone https://github.com/yourusername/MobiPerf.git
cd MobiPerf
chmod +x run.sh
./run.sh
```

启动脚本会自动：
1. 创建 Python 虚拟环境
2. 安装所有依赖
3. 初始化默认管理员账户
4. 启动后端服务 (端口 8000)
5. 启动前端服务 (端口 3000)

### 方式二：手动启动

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/MobiPerf.git
cd MobiPerf
```

#### 2. 配置数据库（可选）

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=mobiperf

SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
```

#### 3. 安装后端依赖

```bash
cd backend
python -m venv venv

source venv/bin/activate
pip install -r requirements.txt
```

#### 4. 初始化数据库和管理员

```bash
python init_db.py
python init_admin.py
```

#### 5. 安装前端依赖

```bash
cd ../frontend
npm install
```

#### 6. 启动服务

**终端 1 - 后端：**
```bash
cd backend
source venv/bin/activate
python main.py
```

**终端 2 - 前端：**
```bash
cd frontend
npm run dev
```

#### 7. 访问应用

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

**默认账户：**

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 测试用户 | test | test123 |

> ⚠️ 首次登录后请及时修改默认密码！

---

## 📖 使用指南

### 1. 连接设备

#### Android 设备

1. **开启开发者选项**
   - 进入 设置 → 关于手机
   - 连续点击"版本号" 7 次

2. **开启 USB 调试**
   - 进入 设置 → 开发者选项
   - 开启"USB 调试"

3. **连接设备**
   - USB 连接设备到电脑
   - 在设备上允许 USB 调试授权
   - 设备将自动识别并显示

#### iOS 设备

1. **安装依赖工具**
   ```bash
   brew install libimobiledevice ideviceinstaller
   ```

2. **连接设备**
   - USB 连接设备到电脑
   - 在设备上信任此电脑
   - 输入设备密码确认信任

3. **验证连接**
   ```bash
   idevice_id -l
   ```

4. **开始测试**
   - 在设备列表中选择 iOS 设备
   - 从应用列表中选择要测试的应用
   - 点击 **"开始测试"** 按钮

### 2. 开始测试

1. 在设备列表中选择目标设备
2. 输入要测试的应用包名（如：`com.example.app`）
3. 点击 **"开始测试"** 按钮
4. 实时查看性能数据

### 3. 性能分析

| 功能 | 说明 |
|------|------|
| 实时监控 | 查看 FPS、CPU、内存等实时曲线 |
| 性能评分 | 查看综合性能评分和优化建议 |
| 打点标记 | 在关键操作时刻添加标记 |

### 4. 生成报告

1. 测试完成后点击 **"生成 HTML 报告"**
2. 等待报告生成完成
3. 点击 **"下载报告"** 保存到本地

### 5. 历史记录

- 查看历史测试记录
- 对比不同测试的性能数据
- 导出历史数据为 CSV

---

## ⚙️ 配置说明

### 环境变量配置

创建 `backend/.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=mobiperf

SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO

ANALYSIS_INTERVAL=1
MAX_METRICS_PER_SESSION=10000
```

### 配置项说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DB_HOST` | localhost | 数据库主机 |
| `DB_PORT` | 3306 | 数据库端口 |
| `DB_USER` | root | 数据库用户 |
| `DB_PASSWORD` | - | 数据库密码 |
| `DB_NAME` | mobiperf | 数据库名称 |
| `SECRET_KEY` | - | JWT 密钥 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `ANALYSIS_INTERVAL` | 1 | 分析间隔(秒) |
| `MAX_METRICS_PER_SESSION` | 10000 | 单次会话最大指标数 |

---

## 📚 API 文档

### RESTful API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/devices` | 获取设备列表 |
| POST | `/api/sessions` | 创建测试会话 |
| GET | `/api/sessions` | 获取历史记录 |
| GET | `/api/sessions/{id}` | 获取会话详情 |
| POST | `/api/notifications/config` | 配置通知 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/register` | 用户注册 |

### WebSocket 接口

```
WS /ws/{device_serial}
```

实时推送性能数据，消息格式：

```json
{
  "timestamp": 1234567890,
  "fps": 60,
  "cpu": 25.5,
  "memory": 512.3,
  "gpu": 30.2,
  "battery": {
    "level": 85,
    "temperature": 35.5
  },
  "network": {
    "upload": 1024,
    "download": 2048
  }
}
```

### 在线文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐛 常见问题

### 设备连接问题

<details>
<summary><b>设备列表为空</b></summary>

**解决方案：**
1. 检查 USB 线连接是否正常
2. 确认 USB 调试已开启
3. 执行 `adb devices` 验证设备是否识别
4. 重新授权 USB 调试

```bash
adb kill-server
adb start-server
adb devices
```
</details>

<details>
<summary><b>iOS 设备无法识别</b></summary>

**解决方案：**
1. 确认已信任此电脑
2. 检查 tidevice 是否正确安装
3. 手动输入 Bundle ID

```bash
pip install tidevice
tidevice list
```
</details>

### 性能问题

<details>
<summary><b>数据采集延迟</b></summary>

**解决方案：**
1. 检查 USB 连接质量
2. 关闭不必要的后台应用
3. 降低采集频率
</details>

<details>
<summary><b>前端卡顿</b></summary>

**解决方案：**
1. 清除浏览器缓存
2. 检查网络连接
3. 减少同时监控的设备数量
</details>

### 数据库问题

<details>
<summary><b>历史记录为空</b></summary>

**解决方案：**
1. 检查数据库连接配置
2. 确认数据库服务已启动
3. 查看 `.env` 配置是否正确

```bash
mysql -u root -p -e "SHOW DATABASES;"
```
</details>

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本仓库
2. 创建特性分支
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. 提交更改
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. 推送到分支
   ```bash
   git push origin feature/AmazingFeature
   ```
5. 开启 Pull Request

### 代码规范

- Python: 遵循 PEP 8 规范
- JavaScript: 使用 ESLint 规范
- 提交信息: 遵循 Conventional Commits

---

## 📄 开源协议

本项目采用 [MIT](LICENSE) 协议开源。

---

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代高性能 Web 框架
- [Vue 3](https://vuejs.org/) - 渐进式 JavaScript 框架
- [ECharts](https://echarts.apache.org/) - 数据可视化图表库
- [adbutils](https://github.com/openatx/adbutils) - Android 调试桥工具库
- [tidevice](https://github.com/alibaba/tidevice) - iOS 设备通信库

---

## 🗺️ 开发路线图

### ✅ 已完成功能

- [x] 实时性能监控（FPS、CPU、内存、GPU、电池、网络）
- [x] iOS 设备完整支持
- [x] 性能评分系统
- [x] HTML 报告生成
- [x] 历史记录查看
- [x] 详细指标图表
- [x] 数据导出（CSV）
- [x] 多设备监控
- [x] 用户认证系统
- [x] 通知中心
- [x] 打点标记功能

### 🚧 开发中功能

- [ ] 性能对比功能（多次测试对比）
- [ ] 自定义告警阈值配置界面
- [ ] 测试报告 PDF 导出

### 📋 计划中功能

#### 数据分析增强
- [ ] 内存泄漏智能检测
- [ ] 启动时间分析
- [ ] 电量消耗分析
- [ ] 网络请求详情分析
- [ ] 卡顿根因分析

#### 团队协作
- [ ] 测试报告分享
- [ ] 团队项目管理
- [ ] 测试任务分配
- [ ] 评论与讨论
- [ ] API 密钥管理

#### 平台扩展
- [ ] 鸿蒙系统支持
- [ ] 远程设备测试
- [ ] 云端数据存储
- [ ] 移动端 App

#### 用户体验
- [ ] 暗黑模式
- [ ] 多语言支持（i18n）
- [ ] 自定义仪表盘
- [ ] 快捷键操作
- [ ] 操作录制回放

#### 集成与扩展
- [ ] CI/CD 集成
- [ ] Jenkins 插件
- [ ] Jira 集成
- [ ] 钉钉/飞书通知
- [ ] Webhook 支持

---

## 📮 联系方式

- 项目主页：https://github.com/yourusername/MobiPerf
- 问题反馈：https://github.com/yourusername/MobiPerf/issues

---

<p align="center">
  <strong>MobiPerf</strong> - 让移动端性能测试更简单 🚀
</p>
