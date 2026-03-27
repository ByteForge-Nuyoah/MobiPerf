from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from database.db_manager import DatabaseManager
from core.auth import AuthService


class CollaborationRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict]:
        if not self.db.pool:
            logger.warning("Database not available, skipping user creation")
            return None
        
        try:
            query = """
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            user_id = await self.db.execute_insert(query, (
                user_data['username'],
                user_data['email'],
                user_data['password_hash'],
                user_data.get('full_name'),
                user_data.get('role', 'viewer')
            ))
            
            logger.info(f"Created user: {user_data['username']}")
            
            return await self.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        if not self.db.pool:
            return None
        
        try:
            query = "SELECT * FROM users WHERE username = %s AND is_active = TRUE"
            users = await self.db.execute_query(query, (username,))
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        if not self.db.pool:
            return None
        
        try:
            query = "SELECT * FROM users WHERE id = %s"
            users = await self.db.execute_query(query, (user_id,))
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Failed to get user by id: {e}")
            return None
    
    async def update_last_login(self, user_id: int) -> bool:
        if not self.db.pool:
            return False
        
        try:
            query = "UPDATE users SET last_login_at = %s WHERE id = %s"
            await self.db.execute_update(query, (datetime.now(), user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update last login: {e}")
            return False
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        if not self.db.pool:
            return None
        
        try:
            query = "SELECT * FROM users WHERE email = %s AND is_active = TRUE"
            users = await self.db.execute_query(query, (email,))
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    async def update_user_password(self, user_id: int, password_hash: str) -> bool:
        if not self.db.pool:
            return False
        
        try:
            query = "UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s"
            await self.db.execute_update(query, (password_hash, datetime.now(), user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update user password: {e}")
            return False
    
    async def create_team(self, team_data: Dict[str, Any]) -> Optional[int]:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO teams (name, description, owner_id)
            VALUES (%s, %s, %s)
            """
            
            team_id = await self.db.execute_insert(query, (
                team_data['name'],
                team_data.get('description'),
                team_data['owner_id']
            ))
            
            await self.add_team_member(team_id, team_data['owner_id'], 'owner')
            
            logger.info(f"Created team: {team_data['name']}")
            return team_id
        except Exception as e:
            logger.error(f"Failed to create team: {e}")
            return None
    
    async def add_team_member(self, team_id: int, user_id: int, role: str = 'member') -> bool:
        if not self.db.pool:
            return False
        
        try:
            query = """
            INSERT INTO team_members (team_id, user_id, role)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE role = %s
            """
            
            await self.db.execute_insert(query, (team_id, user_id, role, role))
            logger.info(f"Added user {user_id} to team {team_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add team member: {e}")
            return False
    
    async def get_team_members(self, team_id: int) -> List[Dict]:
        if not self.db.pool:
            return []
        
        try:
            query = """
            SELECT u.id, u.username, u.email, u.full_name, u.avatar_url, tm.role, tm.joined_at
            FROM team_members tm
            JOIN users u ON tm.user_id = u.id
            WHERE tm.team_id = %s
            ORDER BY tm.joined_at ASC
            """
            
            members = await self.db.execute_query(query, (team_id,))
            return members
        except Exception as e:
            logger.error(f"Failed to get team members: {e}")
            return []
    
    async def create_project(self, project_data: Dict[str, Any]) -> Optional[int]:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO projects (name, description, team_id, owner_id, app_package, platform, is_public)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            project_id = await self.db.execute_insert(query, (
                project_data['name'],
                project_data.get('description'),
                project_data.get('team_id'),
                project_data['owner_id'],
                project_data.get('app_package'),
                project_data.get('platform', 'both'),
                project_data.get('is_public', False)
            ))
            
            await self.add_project_member(project_id, project_data['owner_id'], 'owner')
            
            logger.info(f"Created project: {project_data['name']}")
            return project_id
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None
    
    async def add_project_member(self, project_id: int, user_id: int, role: str = 'viewer') -> bool:
        if not self.db.pool:
            return False
        
        try:
            query = """
            INSERT INTO project_members (project_id, user_id, role)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE role = %s
            """
            
            await self.db.execute_insert(query, (project_id, user_id, role, role))
            logger.info(f"Added user {user_id} to project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add project member: {e}")
            return False
    
    async def get_user_projects(self, user_id: int) -> List[Dict]:
        if not self.db.pool:
            return []
        
        try:
            query = """
            SELECT p.*, pm.role as user_role
            FROM projects p
            JOIN project_members pm ON p.id = pm.project_id
            WHERE pm.user_id = %s AND p.status = 'active'
            ORDER BY p.created_at DESC
            """
            
            projects = await self.db.execute_query(query, (user_id,))
            return projects
        except Exception as e:
            logger.error(f"Failed to get user projects: {e}")
            return []
    
    async def create_comment(self, comment_data: Dict[str, Any]) -> Optional[int]:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO comments (session_id, user_id, content, parent_id)
            VALUES (%s, %s, %s, %s)
            """
            
            comment_id = await self.db.execute_insert(query, (
                comment_data['session_id'],
                comment_data['user_id'],
                comment_data['content'],
                comment_data.get('parent_id')
            ))
            
            logger.info(f"Created comment on session {comment_data['session_id']}")
            return comment_id
        except Exception as e:
            logger.error(f"Failed to create comment: {e}")
            return None
    
    async def get_session_comments(self, session_id: int) -> List[Dict]:
        if not self.db.pool:
            return []
        
        try:
            query = """
            SELECT c.*, u.username, u.avatar_url
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.session_id = %s
            ORDER BY c.created_at ASC
            """
            
            comments = await self.db.execute_query(query, (session_id,))
            return comments
        except Exception as e:
            logger.error(f"Failed to get session comments: {e}")
            return []
    
    async def create_notification(self, notification_data: Dict[str, Any]) -> Optional[int]:
        if not self.db.pool:
            return None
        
        try:
            query = """
            INSERT INTO notifications (user_id, type, title, content, data)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            import json
            notification_id = await self.db.execute_insert(query, (
                notification_data['user_id'],
                notification_data['type'],
                notification_data['title'],
                notification_data.get('content'),
                json.dumps(notification_data.get('data', {}))
            ))
            
            return notification_id
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    async def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[Dict]:
        if not self.db.pool:
            return []
        
        try:
            if unread_only:
                query = """
                SELECT * FROM notifications
                WHERE user_id = %s AND is_read = FALSE
                ORDER BY created_at DESC
                LIMIT 50
                """
            else:
                query = """
                SELECT * FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
                """
            
            notifications = await self.db.execute_query(query, (user_id,))
            return notifications
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        if not self.db.pool:
            return False
        
        try:
            query = """
            UPDATE notifications
            SET is_read = TRUE
            WHERE id = %s AND user_id = %s
            """
            
            await self.db.execute_update(query, (notification_id, user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    async def share_session(self, share_data: Dict[str, Any]) -> Optional[int]:
        if not self.db.pool:
            return None
        
        try:
            import secrets
            share_link = secrets.token_urlsafe(16)
            
            query = """
            INSERT INTO session_shares 
            (session_id, shared_by_user_id, shared_with_user_id, shared_with_team_id, permission, share_link, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            share_id = await self.db.execute_insert(query, (
                share_data['session_id'],
                share_data['shared_by_user_id'],
                share_data.get('shared_with_user_id'),
                share_data.get('shared_with_team_id'),
                share_data.get('permission', 'view'),
                share_link,
                share_data.get('expires_at')
            ))
            
            logger.info(f"Shared session {share_data['session_id']}")
            return share_id
        except Exception as e:
            logger.error(f"Failed to share session: {e}")
            return None
    
    async def create_audit_log(self, log_data: Dict[str, Any]) -> bool:
        if not self.db.pool:
            return False
        
        try:
            import json
            query = """
            INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            await self.db.execute_insert(query, (
                log_data.get('user_id'),
                log_data['action'],
                log_data['resource_type'],
                log_data.get('resource_id'),
                json.dumps(log_data.get('details', {})),
                log_data.get('ip_address'),
                log_data.get('user_agent')
            ))
            
            return True
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return False
