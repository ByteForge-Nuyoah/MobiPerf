-- 团队协作功能数据库表

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    full_name VARCHAR(100) COMMENT '全名',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    role ENUM('admin', 'manager', 'developer', 'viewer') DEFAULT 'developer' COMMENT '角色',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP COMMENT '最后登录时间',
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 团队表
CREATE TABLE IF NOT EXISTS teams (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '团队名称',
    description TEXT COMMENT '团队描述',
    owner_id BIGINT NOT NULL COMMENT '团队所有者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_owner_id (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='团队表';

-- 团队成员表
CREATE TABLE IF NOT EXISTS team_members (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    team_id BIGINT NOT NULL COMMENT '团队ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role ENUM('owner', 'admin', 'member') DEFAULT 'member' COMMENT '团队角色',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_team_member (team_id, user_id),
    INDEX idx_team_id (team_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='团队成员表';

-- 项目表
CREATE TABLE IF NOT EXISTS projects (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL COMMENT '项目名称',
    description TEXT COMMENT '项目描述',
    team_id BIGINT COMMENT '所属团队ID',
    owner_id BIGINT NOT NULL COMMENT '项目所有者ID',
    app_package VARCHAR(255) COMMENT '应用包名',
    platform ENUM('android', 'ios', 'both') DEFAULT 'both' COMMENT '平台',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    status ENUM('active', 'archived', 'deleted') DEFAULT 'active' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_team_id (team_id),
    INDEX idx_owner_id (owner_id),
    INDEX idx_app_package (app_package),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目表';

-- 项目成员表
CREATE TABLE IF NOT EXISTS project_members (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role ENUM('owner', 'admin', 'developer', 'viewer') DEFAULT 'viewer' COMMENT '项目角色',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_project_member (project_id, user_id),
    INDEX idx_project_id (project_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目成员表';

-- 更新测试会话表，添加项目和用户关联
ALTER TABLE test_sessions 
ADD COLUMN project_id BIGINT COMMENT '项目ID',
ADD COLUMN user_id BIGINT COMMENT '用户ID',
ADD FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
ADD INDEX idx_project_id (project_id),
ADD INDEX idx_user_id (user_id);

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL COMMENT '测试会话ID',
    user_id BIGINT NOT NULL COMMENT '评论用户ID',
    content TEXT NOT NULL COMMENT '评论内容',
    parent_id BIGINT COMMENT '父评论ID（用于回复）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论表';

-- 通知表
CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '接收通知的用户ID',
    type ENUM('session_shared', 'comment', 'mention', 'project_invite', 'system') NOT NULL COMMENT '通知类型',
    title VARCHAR(255) NOT NULL COMMENT '通知标题',
    content TEXT COMMENT '通知内容',
    data JSON COMMENT '附加数据',
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知表';

-- 会话分享表
CREATE TABLE IF NOT EXISTS session_shares (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL COMMENT '测试会话ID',
    shared_by_user_id BIGINT NOT NULL COMMENT '分享者ID',
    shared_with_user_id BIGINT COMMENT '分享给用户ID',
    shared_with_team_id BIGINT COMMENT '分享给团队ID',
    permission ENUM('view', 'comment', 'edit') DEFAULT 'view' COMMENT '权限',
    share_link VARCHAR(100) UNIQUE COMMENT '分享链接',
    expires_at TIMESTAMP COMMENT '过期时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_with_team_id) REFERENCES teams(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_shared_with_user (shared_with_user_id),
    INDEX idx_shared_with_team (shared_with_team_id),
    INDEX idx_share_link (share_link)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话分享表';

-- API 密钥表
CREATE TABLE IF NOT EXISTS api_keys (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    name VARCHAR(100) NOT NULL COMMENT '密钥名称',
    key_hash VARCHAR(255) NOT NULL UNIQUE COMMENT '密钥哈希',
    permissions JSON COMMENT '权限列表',
    last_used_at TIMESTAMP COMMENT '最后使用时间',
    expires_at TIMESTAMP COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_key_hash (key_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API密钥表';

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT COMMENT '用户ID',
    action VARCHAR(100) NOT NULL COMMENT '操作类型',
    resource_type VARCHAR(50) NOT NULL COMMENT '资源类型',
    resource_id BIGINT COMMENT '资源ID',
    details JSON COMMENT '详细信息',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志表';
