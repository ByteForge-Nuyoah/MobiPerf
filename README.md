# MobiPerf 🚀
## ✨ 核心特性
### 🎯 实时性能监控

| 指标         | 描述                |
| ---------- | ----------------- |
| **FPS 监控** | 实时帧率、卡顿检测、掉帧分析    |
| **CPU 监控** | CPU 使用率、趋势分析、峰值检测 |
| **内存监控**   | 内存占用、内存泄漏检测、增长趋势  |
| **GPU 监控** | GPU 使用率、渲染性能分析    |
| **电池监控**   | 电量、温度、电压、电流实时监控   |
| **网络监控**   | 上下行流量统计、网络性能分析    |

### 📊 专业分析功能

- **性能评分**：综合性能评分系统（0-100分）
- **趋势分析**：CPU、内存、温度趋势预测
- **风险预警**：内存泄漏风险、温度过高预警
- **稳定性评估**：FPS稳定性等级（优秀/良好/一般/较差）
- **智能建议**：基于数据的优化建议生成

### 🔔 智能通知系统

- **可配置通知类型**：FPS、CPU、内存、温度、设备状态等
- **多级优先级**：低、中、高、紧急
- **实时推送**：WebSocket 实时通知
- **阈值触发**：自定义告警阈值
- **免打扰时段**：可配置免打扰时间
- **多渠道支持**：应用内、邮件、浏览器通知

### 📈 数据可视化

- **实时曲线图**：多指标实时展示
- **设备截图**：实时屏幕截图功能
- **屏幕录制**：支持录制测试过程
- **历史对比**：历史数据对比分析
- **响应式设计**：完美适配桌面、平板、移动设备

### 📝 报告生成

- **HTML 报告**：专业性能测试报告
- **数据导出**：CSV 格式原始数据
- **图表导出**：PNG 格式图表
- **一键下载**：浏览器直接下载
- **详细指标**：包含所有性能指标和分析结果

### 📱 多设备支持

- **多设备监控**：同时监控多台设备
- **设备管理**：设备热插拔自动识别
- **平台支持**：Android 5.0+、iOS 12.0+
- **实时统计**：多设备平均指标统计
- **独立图表**：每个设备独立性能曲线

### 🎨 现代化UI

- **响应式设计**：自适应桌面、平板、移动设备
- **暗黑模式**：护眼暗黑主题（开发中）
- **流畅动画**：优雅的过渡动画效果
- **直观操作**：简洁明了的操作界面
- **实时反馈**：操作状态实时反馈

🏗️ 项目结构

```
MobiPerf/
├── backend/                    # Python 后端服务
│   ├── core/                   # 核心功能模块
│   │   ├── android_collector.py    # Android 数据采集
│   │   ├── ios_collector.py        # iOS 数据采集
│   │   ├── performance_analyzer.py # 性能分析器
│   │   ├── notification_service.py # 通知服务
│   │   ├── report_generator.py     # 报告生成器
│   │   ├── redis_cache.py          # Redis 缓存
│   │   └── config_loader.py        # 配置加载器
│   ├── database/               # 数据库模块
│   │   ├── db_manager.py          # 数据库管理
│   │   ├── schema.sql             # 数据库结构
│   │   ├── collaboration_*.py     # 协作功能
│   │   └── init_schema.sql        # 初始化脚本
│   ├── routes/                 # API 路由
│   │   ├── auth.py                # 认证 API
│   │   ├── notifications.py       # 通知 API
│   │   └── collaboration.py       # 协作 API
│   ├── middleware/             # 中间件
│   │   ├── error_handler.py       # 错误处理
│   │   ├── rate_limit.py          # 限流中间件
│   │   └── request_id.py          # 请求ID追踪
│   ├── models/                 # 数据模型
│   │   └── schemas.py             # Pydantic 模型
│   ├── templates/              # 报告模板
│   ├── reports/                # 生成的报告
│   ├── clear_test_data.py      # 数据清理脚本
│   ├── main.py                 # 后端入口
│   ├── config.yaml             # 配置文件
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
│   │   ├── composables/        # 组合式函数
│   │   │   ├── useMonitorStore.js      # 监控状态管理
│   │   │   └── useAuthStore.js         # 认证状态管理
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

***

## 🚀 快速开始

### 前置要求

| 工具      | 版本要求        | 检查命令                  |
| ------- | ----------- | --------------------- |
| Python  | 3.8+        | `python --version`    |
| Node.js | 16+         | `node --version`      |
| ADB     | Latest      | `adb version`         |
| MySQL   | 5.7+ (可选)   | `mysql --version`     |
| Redis   | Latest (可选) | `redis-cli --version` |

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
cp config.yaml.example config.yaml
```

编辑 `config.yaml` 文件：

```yaml
database:
  host: "localhost"
  port: 3306
  user: "root"
  password: "your_password"
  name: "mobiperf"
  charset: "utf8mb4"

redis:
  enabled: true
  host: "localhost"
  port: 6379
  password: ""
  db: 0
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

| 服务     | 地址                           |
| ------ | ---------------------------- |
| 前端界面   | <http://localhost:3000>      |
| 后端 API | <http://localhost:8000>      |
| API 文档 | <http://localhost:8000/docs> |

**默认账户：**

| 角色   | 用户名   | 密码       |
| ---- | ----- | -------- |
| 管理员  | admin | admin123 |
| 测试用户 | test  | test123  |

> ⚠️ 首次登录后请及时修改默认密码！

***

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

| 功能   | 说明                 |
| ---- | ------------------ |
| 实时监控 | 查看 FPS、CPU、内存等实时曲线 |
| 性能评分 | 查看综合性能评分和优化建议      |
| 打点标记 | 在关键操作时刻添加标记        |
| 截图录制 | 实时截图和录制测试过程        |

### 4. 多设备监控

1. 点击 **"添加设备"** 按钮
2. 选择要监控的设备
3. 选择要测试的应用
4. 同时监控多台设备的性能
5. 查看平均指标统计

### 5. 生成报告

1. 测试完成后点击 **"生成 HTML 报告"**
2. 等待报告生成完成
3. 点击 **"下载报告"** 保存到本地
4. 报告包含详细的性能分析和优化建议

### 6. 历史记录

- 查看历史测试记录
- 对比不同测试的性能数据
- 导出历史数据为 CSV
- 删除不需要的测试记录

***

## 💡 性能优化建议

基于性能测试数据，系统会自动生成优化建议。以下是常见的性能问题及优化方案：

### 🎮 FPS 优化

#### 问题：FPS 过低或波动大

**可能原因：**

- UI 渲染过于复杂
- 主线程执行耗时操作
- 频繁的布局计算
- 过度绘制

## ⚙️ 配置说明

### 环境变量配置

创建 `backend/config.yaml` 文件：

```yaml
app:
  name: "MobiPerf"
  version: "1.0.0"
  debug: false
  host: "0.0.0.0"
  port: 8000

database:
  host: "localhost"
  port: 3306
  user: "root"
  password: "your_password"
  name: "mobiperf"
  charset: "utf8mb4"
  pool_size: 10
  max_overflow: 20
  autocommit: true

redis:
  enabled: true
  host: "localhost"
  port: 6379
  password: ""
  db: 0
  prefix: "mobiperf:"
  pool_size: 10

logging:
  level: "INFO"
  format: "json"
  file:
    enabled: true
    path: "logs"
    max_size: "10MB"
    retention: "30 days"

cache:
  enabled: true
  backend: "redis"
  default_ttl: 60

security:
  secret_key: "your-secret-key-here"
  access_token_expire: 86400  # 24小时
  refresh_token_expire: 604800  # 7天
  algorithm: "HS256"

performance:
  analysis_interval: 1
  max_metrics_per_session: 10000
  screenshot_dir: "static/screenshots"
  record_dir: "static/records"
  report_dir: "reports"
```

### 配置项说明

| 配置项                                   | 默认值       | 说明          |
| ------------------------------------- | --------- | ----------- |
| `database.host`                       | localhost | 数据库主机       |
| `database.port`                       | 3306      | 数据库端口       |
| `redis.enabled`                       | true      | 是否启用 Redis  |
| `redis.host`                          | localhost | Redis 主机    |
| `security.access_token_expire`        | 86400     | 访问令牌过期时间（秒） |
| `performance.analysis_interval`       | 1         | 分析间隔(秒)     |
| `performance.max_metrics_per_session` | 10000     | 单次会话最大指标数   |

***

## 📚 API 文档

### RESTful API

| 方法     | 路径                          | 描述     |
| ------ | --------------------------- | ------ |
| GET    | `/api/devices`              | 获取设备列表 |
| POST   | `/api/sessions`             | 创建测试会话 |
| GET    | `/api/sessions`             | 获取历史记录 |
| GET    | `/api/sessions/{id}`        | 获取会话详情 |
| DELETE | `/api/sessions/{id}`        | 删除测试会话 |
| POST   | `/api/notifications/config` | 配置通知   |
| GET    | `/api/notifications/`       | 获取通知列表 |
| POST   | `/api/auth/login`           | 用户登录   |
| POST   | `/api/auth/register`        | 用户注册   |
| POST   | `/api/auth/refresh`         | 刷新令牌   |

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

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

***

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

```bash
pip install tidevice
tidevice list
```
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

***

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
- [x] 截图和录制功能
- [x] Redis 缓存支持
- [x] 响应式UI设计
- [x] 性能优化建议生成
- [x] 数据清理脚本

### 🚧 开发中功能

- [ ] 性能对比功能（多次测试对比）
- [ ] 自定义告警阈值配置界面
- [ ] 测试报告 PDF 导出
- [ ] 暗黑模式

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