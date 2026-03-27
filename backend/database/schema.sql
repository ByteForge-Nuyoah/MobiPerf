-- MobiPerf 数据库表结构设计
-- 创建数据库
CREATE DATABASE IF NOT EXISTS mobiperf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE mobiperf;

-- 测试会话表
CREATE TABLE IF NOT EXISTS test_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL UNIQUE COMMENT '会话唯一标识',
    device_model VARCHAR(128) COMMENT '设备型号',
    device_serial VARCHAR(64) COMMENT '设备序列号',
    app_package VARCHAR(255) COMMENT '应用包名',
    app_version VARCHAR(64) COMMENT '应用版本',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    duration INT COMMENT '测试时长(秒)',
    overall_score DECIMAL(5,2) COMMENT '综合评分',
    status ENUM('running', 'completed', 'error') DEFAULT 'running' COMMENT '会话状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_device_serial (device_serial),
    INDEX idx_app_package (app_package),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试会话表';

-- 性能指标原始数据表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    timestamp BIGINT NOT NULL COMMENT '时间戳(毫秒)',
    fps DECIMAL(6,2) COMMENT '帧率',
    jank INT COMMENT '卡顿帧数',
    cpu_usage DECIMAL(5,2) COMMENT 'CPU使用率(%)',
    memory_usage DECIMAL(10,2) COMMENT '内存使用(MB)',
    gpu_usage DECIMAL(5,2) COMMENT 'GPU使用率(%)',
    battery_level INT COMMENT '电池电量(%)',
    battery_temp DECIMAL(5,2) COMMENT '电池温度(℃)',
    battery_voltage INT COMMENT '电池电压(mV)',
    battery_current INT COMMENT '电池电流(mA)',
    network_rx DECIMAL(10,2) COMMENT '网络接收(KB/s)',
    network_tx DECIMAL(10,2) COMMENT '网络发送(KB/s)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='性能指标原始数据表';

-- FPS 稳定性分析结果表
CREATE TABLE IF NOT EXISTS fps_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    analysis_time DATETIME NOT NULL COMMENT '分析时间',
    fps_avg DECIMAL(6,2) COMMENT '平均FPS',
    fps_min DECIMAL(6,2) COMMENT '最小FPS',
    fps_max DECIMAL(6,2) COMMENT '最大FPS',
    fps_std DECIMAL(6,2) COMMENT 'FPS标准差',
    fps_variance DECIMAL(10,2) COMMENT 'FPS方差',
    jank_rate DECIMAL(6,2) COMMENT '卡顿率(%)',
    stutter_rate DECIMAL(6,2) COMMENT '掉帧率(%)',
    big_jank_count INT COMMENT '严重卡顿次数',
    stability_score DECIMAL(5,2) COMMENT '稳定性评分',
    stability_level ENUM('excellent', 'good', 'fair', 'poor') COMMENT '稳定性等级',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_analysis_time (analysis_time),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='FPS稳定性分析结果表';

-- 内存趋势分析结果表
CREATE TABLE IF NOT EXISTS memory_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    analysis_time DATETIME NOT NULL COMMENT '分析时间',
    memory_avg DECIMAL(10,2) COMMENT '平均内存(MB)',
    memory_min DECIMAL(10,2) COMMENT '最小内存(MB)',
    memory_max DECIMAL(10,2) COMMENT '最大内存(MB)',
    memory_current DECIMAL(10,2) COMMENT '当前内存(MB)',
    memory_growth_rate DECIMAL(8,2) COMMENT '内存增长率(MB/s)',
    memory_trend ENUM('increasing_fast', 'increasing', 'stable', 'decreasing', 'decreasing_fast') COMMENT '内存趋势',
    leak_risk ENUM('high', 'medium', 'low') COMMENT '泄漏风险',
    memory_spike_count INT COMMENT '内存峰值次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_analysis_time (analysis_time),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='内存趋势分析结果表';

-- CPU 使用分析结果表
CREATE TABLE IF NOT EXISTS cpu_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    analysis_time DATETIME NOT NULL COMMENT '分析时间',
    cpu_avg DECIMAL(5,2) COMMENT '平均CPU(%)',
    cpu_min DECIMAL(5,2) COMMENT '最小CPU(%)',
    cpu_max DECIMAL(5,2) COMMENT '最大CPU(%)',
    cpu_current DECIMAL(5,2) COMMENT '当前CPU(%)',
    cpu_trend ENUM('increasing_fast', 'increasing', 'stable', 'decreasing', 'decreasing_fast') COMMENT 'CPU趋势',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_analysis_time (analysis_time),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CPU使用分析结果表';

-- GPU 使用分析结果表
CREATE TABLE IF NOT EXISTS gpu_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    analysis_time DATETIME NOT NULL COMMENT '分析时间',
    gpu_avg DECIMAL(5,2) COMMENT '平均GPU(%)',
    gpu_min DECIMAL(5,2) COMMENT '最小GPU(%)',
    gpu_max DECIMAL(5,2) COMMENT '最大GPU(%)',
    gpu_current DECIMAL(5,2) COMMENT '当前GPU(%)',
    gpu_trend ENUM('increasing_fast', 'increasing', 'stable', 'decreasing', 'decreasing_fast') COMMENT 'GPU趋势',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_analysis_time (analysis_time),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='GPU使用分析结果表';

-- 电池温度分析结果表
CREATE TABLE IF NOT EXISTS battery_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    analysis_time DATETIME NOT NULL COMMENT '分析时间',
    temp_avg DECIMAL(5,2) COMMENT '平均温度(℃)',
    temp_min DECIMAL(5,2) COMMENT '最小温度(℃)',
    temp_max DECIMAL(5,2) COMMENT '最大温度(℃)',
    temp_current DECIMAL(5,2) COMMENT '当前温度(℃)',
    temp_trend ENUM('increasing_fast', 'increasing', 'stable', 'decreasing', 'decreasing_fast') COMMENT '温度趋势',
    thermal_throttle_risk ENUM('high', 'medium', 'low') COMMENT '热节流风险',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_analysis_time (analysis_time),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='电池温度分析结果表';

-- 综合分析结果表
CREATE TABLE IF NOT EXISTS comprehensive_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    analysis_time DATETIME NOT NULL COMMENT '分析时间',
    overall_score DECIMAL(5,2) COMMENT '综合评分',
    fps_stability_level ENUM('excellent', 'good', 'fair', 'poor') COMMENT 'FPS稳定性等级',
    memory_leak_risk ENUM('high', 'medium', 'low') COMMENT '内存泄漏风险',
    thermal_throttle_risk ENUM('high', 'medium', 'low') COMMENT '热节流风险',
    recommendations TEXT COMMENT '优化建议(JSON数组)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_analysis_time (analysis_time),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='综合分析结果表';

-- 报告记录表
CREATE TABLE IF NOT EXISTS reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    report_type ENUM('html', 'pdf', 'json') DEFAULT 'html' COMMENT '报告类型',
    report_path VARCHAR(512) NOT NULL COMMENT '报告文件路径',
    report_size INT COMMENT '报告文件大小(字节)',
    generated_at DATETIME NOT NULL COMMENT '生成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_generated_at (generated_at),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告记录表';
