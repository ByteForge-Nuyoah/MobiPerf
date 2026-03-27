import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
import aiomysql
from contextlib import asynccontextmanager


class DatabaseManager:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'db': os.getenv('DB_NAME', 'veloperf'),
            'charset': 'utf8mb4',
            'autocommit': True
        }
        self.pool = None
        
    async def init_pool(self):
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                db=self.config['db'],
                charset=self.config['charset'],
                autocommit=self.config['autocommit'],
                minsize=5,
                maxsize=20,
                pool_recycle=3600
            )
            logger.info("Database connection pool initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            return False
    
    async def close_pool(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        if not self.pool:
            success = await self.init_pool()
            if not success:
                raise RuntimeError("Database connection pool not initialized")
        
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            self.pool.release(conn)
    
    async def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                result = await cursor.fetchall()
                return result
    
    async def execute_insert(self, query: str, params: tuple = None) -> int:
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.lastrowid
    
    async def execute_update(self, query: str, params: tuple = None) -> int:
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.rowcount
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.executemany(query, params_list)
                return cursor.rowcount


class PerformanceDataRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_test_session(self, session_data: Dict[str, Any]) -> str:
        if not self.db.pool:
            logger.warning("Database not available, skipping session creation")
            return None
        
        try:
            query = """
            INSERT INTO test_sessions 
            (session_id, device_model, device_serial, app_package, app_version, start_time, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            session_id = session_data.get('session_id')
            await self.db.execute_insert(query, (
                session_id,
                session_data.get('device_model'),
                session_data.get('device_serial'),
                session_data.get('app_package'),
                session_data.get('app_version'),
                session_data.get('start_time', datetime.now()),
                'running'
            ))
            
            logger.info(f"Created test session: {session_id}")
            return session_id
        except Exception as e:
            logger.error(f"Failed to create test session: {e}")
            return None
    
    async def update_test_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        if not self.db.pool:
            logger.warning("Database not available, skipping session update")
            return False
        
        try:
            set_clauses = []
            params = []
            
            for key, value in update_data.items():
                set_clauses.append(f"{key} = %s")
                params.append(value)
            
            params.append(session_id)
            
            query = f"""
            UPDATE test_sessions 
            SET {', '.join(set_clauses)}
            WHERE session_id = %s
            """
            
            rows_affected = await self.db.execute_update(query, tuple(params))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Failed to update test session: {e}")
            return False
    
    async def save_performance_metrics(self, session_id: str, metrics: Dict[str, Any]) -> int:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO performance_metrics
            (session_id, timestamp, fps, jank, cpu_usage, memory_usage, gpu_usage,
             battery_level, battery_temp, battery_voltage, battery_current, network_rx, network_tx)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            metric_id = await self.db.execute_insert(query, (
                session_id,
                metrics.get('timestamp'),
                metrics.get('fps'),
                metrics.get('jank'),
                metrics.get('cpu'),
                metrics.get('memory'),
                metrics.get('gpu'),
                metrics.get('battery', {}).get('level'),
                metrics.get('battery', {}).get('temp'),
                metrics.get('battery', {}).get('voltage'),
                metrics.get('battery', {}).get('current'),
                metrics.get('network', {}).get('rx'),
                metrics.get('network', {}).get('tx')
            ))
            
            return metric_id
        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")
            return None
    
    async def save_fps_analysis(self, session_id: str, fps_data: Dict[str, Any]) -> int:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO fps_analysis
            (session_id, analysis_time, fps_avg, fps_min, fps_max, fps_std, fps_variance,
             jank_rate, stutter_rate, big_jank_count, stability_score, stability_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            analysis_id = await self.db.execute_insert(query, (
                session_id,
                datetime.now(),
                fps_data.get('fps_avg'),
                fps_data.get('fps_min'),
                fps_data.get('fps_max'),
                fps_data.get('fps_std'),
                fps_data.get('fps_variance'),
                fps_data.get('jank_rate'),
                fps_data.get('stutter_rate'),
                fps_data.get('big_jank_count'),
                fps_data.get('stability_score'),
                fps_data.get('stability_level')
            ))
            
            return analysis_id
        except Exception as e:
            logger.error(f"Failed to save FPS analysis: {e}")
            return None
    
    async def save_memory_analysis(self, session_id: str, memory_data: Dict[str, Any]) -> int:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO memory_analysis
            (session_id, analysis_time, memory_avg, memory_min, memory_max, memory_current,
             memory_growth_rate, memory_trend, leak_risk, memory_spike_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            analysis_id = await self.db.execute_insert(query, (
                session_id,
                datetime.now(),
                memory_data.get('memory_avg'),
                memory_data.get('memory_min'),
                memory_data.get('memory_max'),
                memory_data.get('memory_current'),
                memory_data.get('memory_growth_rate'),
                memory_data.get('memory_trend'),
                memory_data.get('leak_risk'),
                memory_data.get('memory_spike_count')
            ))
            
            return analysis_id
        except Exception as e:
            logger.error(f"Failed to save memory analysis: {e}")
            return None
    
    async def save_comprehensive_analysis(self, session_id: str, analysis_data: Dict[str, Any]) -> int:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO comprehensive_analysis
            (session_id, analysis_time, overall_score, fps_stability_level, 
             memory_leak_risk, thermal_throttle_risk, recommendations)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            analysis_id = await self.db.execute_insert(query, (
                session_id,
                datetime.now(),
                analysis_data.get('overall_score'),
                analysis_data.get('fps', {}).get('stability_level'),
                analysis_data.get('memory', {}).get('leak_risk'),
                analysis_data.get('battery_temp', {}).get('thermal_throttle_risk'),
                json.dumps(analysis_data.get('recommendations', []), ensure_ascii=False)
            ))
            
            return analysis_id
        except Exception as e:
            logger.error(f"Failed to save comprehensive analysis: {e}")
            return None
    
    async def save_report_record(self, session_id: str, report_data: Dict[str, Any]) -> int:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO reports
            (session_id, report_type, report_path, report_size, generated_at)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            report_id = await self.db.execute_insert(query, (
                session_id,
                report_data.get('report_type', 'html'),
                report_data.get('report_path'),
                report_data.get('report_size'),
                report_data.get('generated_at', datetime.now())
            ))
            
            return report_id
        except Exception as e:
            logger.error(f"Failed to save report record: {e}")
            return None
    
    async def get_test_sessions(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        if not self.db.pool:
            return []
        
        try:
            query = """
            SELECT * FROM test_sessions
            ORDER BY start_time DESC
            LIMIT %s OFFSET %s
            """
            
            sessions = await self.db.execute_query(query, (limit, offset))
            return sessions
        except Exception as e:
            logger.error(f"Failed to get test sessions: {e}")
            return []
    
    async def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        if not self.db.pool:
            return None
        
        try:
            query = "SELECT * FROM test_sessions WHERE session_id = %s"
            sessions = await self.db.execute_query(query, (session_id,))
            return sessions[0] if sessions else None
        except Exception as e:
            logger.error(f"Failed to get session by id: {e}")
            return None
    
    async def get_performance_metrics(self, session_id: str, limit: int = 1000) -> List[Dict]:
        if not self.db.pool:
            return []
        
        try:
            query = """
            SELECT * FROM performance_metrics
            WHERE session_id = %s
            ORDER BY timestamp ASC
            LIMIT %s
            """
            
            metrics = await self.db.execute_query(query, (session_id, limit))
            return metrics
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return []
    
    async def get_comprehensive_analysis(self, session_id: str) -> Optional[Dict]:
        if not self.db.pool:
            return None
        
        try:
            query = """
            SELECT * FROM comprehensive_analysis
            WHERE session_id = %s
            ORDER BY analysis_time DESC
            LIMIT 1
            """
            
            analyses = await self.db.execute_query(query, (session_id,))
            if analyses:
                analysis = analyses[0]
                analysis['recommendations'] = json.loads(analysis['recommendations'])
                return analysis
            return None
        except Exception as e:
            logger.error(f"Failed to get comprehensive analysis: {e}")
            return None
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        if not self.db.pool:
            return {}
        
        try:
            query = """
            SELECT 
                COUNT(*) as total_metrics,
                MIN(timestamp) as start_timestamp,
                MAX(timestamp) as end_timestamp,
                AVG(fps) as avg_fps,
                AVG(cpu_usage) as avg_cpu,
                AVG(memory_usage) as avg_memory,
                AVG(gpu_usage) as avg_gpu,
                AVG(battery_temp) as avg_temp
            FROM performance_metrics
            WHERE session_id = %s
            """
            
            stats = await self.db.execute_query(query, (session_id,))
            return stats[0] if stats else {}
        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            return {}
    
    async def search_sessions(self, filters: Dict[str, Any]) -> List[Dict]:
        if not self.db.pool:
            return []
        
        try:
            conditions = []
            params = []
            
            if filters.get('device_serial'):
                conditions.append("device_serial = %s")
                params.append(filters['device_serial'])
            
            if filters.get('app_package'):
                conditions.append("app_package = %s")
                params.append(filters['app_package'])
            
            if filters.get('start_date'):
                conditions.append("start_time >= %s")
                params.append(filters['start_date'])
            
            if filters.get('end_date'):
                conditions.append("start_time <= %s")
                params.append(filters['end_date'])
            
            if filters.get('status'):
                conditions.append("status = %s")
                params.append(filters['status'])
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
            SELECT * FROM test_sessions
            WHERE {where_clause}
            ORDER BY start_time DESC
            LIMIT %s OFFSET %s
            """
            
            params.extend([filters.get('limit', 50), filters.get('offset', 0)])
            
            sessions = await self.db.execute_query(query, tuple(params))
            return sessions
        except Exception as e:
            logger.error(f"Failed to search sessions: {e}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        if not self.db.pool:
            return False
        
        try:
            query = "DELETE FROM test_sessions WHERE session_id = %s"
            rows_affected = await self.db.execute_update(query, (session_id,))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

db_manager = DatabaseManager()
