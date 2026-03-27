import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from loguru import logger

CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 53306
    user: str = "root"
    password: str = ""
    name: str = "mobiperf"
    charset: str = "utf8mb4"
    pool_size: int = 10
    max_overflow: int = 20
    autocommit: bool = True

@dataclass
class RedisConfig:
    enabled: bool = True
    host: str = "localhost"
    port: int = 56379
    password: str = ""
    db: int = 0
    prefix: str = "mobiperf:"
    pool_size: int = 10

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "json"
    file_enabled: bool = True
    file_path: str = "logs"
    file_max_size: str = "10MB"
    file_retention: str = "7 days"
    console_enabled: bool = True
    console_colorize: bool = True

@dataclass
class CacheKeyConfig:
    key: str = ""
    ttl: int = 60

@dataclass
class CacheConfig:
    enabled: bool = True
    backend: str = "redis"
    default_ttl: int = 60
    keys: Dict[str, CacheKeyConfig] = field(default_factory=dict)

@dataclass
class RateLimitEndpointConfig:
    requests: int = 100
    window: int = 60

@dataclass
class RateLimitConfig:
    enabled: bool = True
    backend: str = "redis"
    default: RateLimitEndpointConfig = field(default_factory=RateLimitEndpointConfig)
    endpoints: Dict[str, Dict[str, RateLimitEndpointConfig]] = field(default_factory=dict)

@dataclass
class SecurityConfig:
    secret_key: str = "your-secret-key-here"
    access_token_expire: int = 3600
    refresh_token_expire: int = 604800
    algorithm: str = "HS256"

@dataclass
class PerformanceConfig:
    analysis_interval: int = 1
    max_metrics_per_session: int = 10000
    screenshot_dir: str = "static/screenshots"
    record_dir: str = "static/records"
    report_dir: str = "reports"

@dataclass
class AppConfig:
    name: str = "MobiPerf"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

class Config:
    _instance = None
    _config: Dict[str, Any] = {}
    
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    logging: LoggingConfig = LoggingConfig()
    cache: CacheConfig = CacheConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()
    security: SecurityConfig = SecurityConfig()
    performance: PerformanceConfig = PerformanceConfig()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        config_path = os.environ.get("MOBIPERF_CONFIG", CONFIG_FILE)
        
        if not Path(config_path).exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            
            self._parse_app_config()
            self._parse_database_config()
            self._parse_redis_config()
            self._parse_logging_config()
            self._parse_cache_config()
            self._parse_rate_limit_config()
            self._parse_security_config()
            self._parse_performance_config()
            
            logger.info(f"Configuration loaded from: {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    
    def _parse_app_config(self):
        if "app" in self._config:
            app = self._config["app"]
            self.app = AppConfig(
                name=app.get("name", "MobiPerf"),
                version=app.get("version", "1.0.0"),
                debug=app.get("debug", False),
                host=app.get("host", "0.0.0.0"),
                port=app.get("port", 8000)
            )
    
    def _parse_database_config(self):
        if "database" in self._config:
            db = self._config["database"]
            self.database = DatabaseConfig(
                host=db.get("host", "localhost"),
                port=int(db.get("port", 3306)),
                user=db.get("user", "root"),
                password=db.get("password", ""),
                name=db.get("name", "mobiperf"),
                charset=db.get("charset", "utf8mb4"),
                pool_size=db.get("pool_size", 10),
                max_overflow=db.get("max_overflow", 20),
                autocommit=db.get("autocommit", True)
            )
    
    def _parse_redis_config(self):
        if "redis" in self._config:
            rd = self._config["redis"]
            self.redis = RedisConfig(
                enabled=rd.get("enabled", True),
                host=rd.get("host", "localhost"),
                port=int(rd.get("port", 56379)),
                password=rd.get("password", ""),
                db=rd.get("db", 0),
                prefix=rd.get("prefix", "mobiperf:"),
                pool_size=rd.get("pool_size", 10)
            )
    
    def _parse_logging_config(self):
        if "logging" in self._config:
            log = self._config["logging"]
            file_cfg = log.get("file", {})
            console_cfg = log.get("console", {})
            self.logging = LoggingConfig(
                level=os.environ.get("LOG_LEVEL", log.get("level", "INFO")),
                format=log.get("format", "json"),
                file_enabled=file_cfg.get("enabled", True),
                file_path=file_cfg.get("path", "logs"),
                file_max_size=file_cfg.get("max_size", "10MB"),
                file_retention=file_cfg.get("retention", "30 days"),
                console_enabled=console_cfg.get("enabled", True),
                console_colorize=console_cfg.get("colorize", True)
            )
    
    def _parse_cache_config(self):
        if "cache" in self._config:
            cache = self._config["cache"]
            keys = {}
            for key_name, key_cfg in cache.get("keys", {}).items():
                keys[key_name] = CacheKeyConfig(
                    key=key_cfg.get("key", ""),
                    ttl=key_cfg.get("ttl", 60)
                )
            self.cache = CacheConfig(
                enabled=cache.get("enabled", True),
                backend=cache.get("backend", "redis"),
                default_ttl=cache.get("default_ttl", 60),
                keys=keys
            )
    
    def _parse_rate_limit_config(self):
        if "rate_limit" in self._config:
            rl = self._config["rate_limit"]
            default = rl.get("default", {})
            endpoints = {}
            for group_name, group_cfg in rl.get("endpoints", {}).items():
                endpoints[group_name] = {}
                for endpoint_name, endpoint_cfg in group_cfg.items():
                    endpoints[group_name][endpoint_name] = RateLimitEndpointConfig(
                        requests=endpoint_cfg.get("requests", 100),
                        window=endpoint_cfg.get("window", 60)
                    )
            self.rate_limit = RateLimitConfig(
                enabled=rl.get("enabled", True),
                backend=rl.get("backend", "redis"),
                default=RateLimitEndpointConfig(
                    requests=default.get("requests", 100),
                    window=default.get("window", 60)
                ),
                endpoints=endpoints
            )
    
    def _parse_security_config(self):
        if "security" in self._config:
            sec = self._config["security"]
            self.security = SecurityConfig(
                secret_key=os.environ.get("SECRET_KEY", sec.get("secret_key", "your-secret-key-here")),
                access_token_expire=sec.get("access_token_expire", 3600),
                refresh_token_expire=sec.get("refresh_token_expire", 604800),
                algorithm=sec.get("algorithm", "HS256")
            )
    
    def _parse_performance_config(self):
        if "performance" in self._config:
            perf = self._config["performance"]
            self.performance = PerformanceConfig(
                analysis_interval=perf.get("analysis_interval", 1),
                max_metrics_per_session=perf.get("max_metrics_per_session", 10000),
                screenshot_dir=perf.get("screenshot_dir", "static/screenshots"),
                record_dir=perf.get("record_dir", "static/records"),
                report_dir=perf.get("report_dir", "reports")
            )
    
    def get_rate_limit(self, group: str, endpoint: str) -> RateLimitEndpointConfig:
        if group in self.rate_limit.endpoints:
            if endpoint in self.rate_limit.endpoints[group]:
                return self.rate_limit.endpoints[group][endpoint]
        return self.rate_limit.default
    
    def get_cache_key(self, name: str) -> CacheKeyConfig:
        return self.cache.keys.get(name, CacheKeyConfig(key=name, ttl=self.cache.default_ttl))
    
    @property
    def DATABASE_CONFIG(self) -> dict:
        return {
            "host": self.database.host,
            "port": self.database.port,
            "user": self.database.user,
            "password": self.database.password,
            "db": self.database.name,
            "charset": self.database.charset,
            "autocommit": self.database.autocommit,
        }
    
    @property
    def SECRET_KEY(self) -> str:
        return self.security.secret_key
    
    @property
    def LOG_LEVEL(self) -> str:
        return self.logging.level

config = Config()
