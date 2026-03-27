from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from loguru import logger

from core.auth import (
    AuthService, UserCreate, UserLogin, Token, UserResponse,
    get_current_active_user, check_permission
)
from database.collaboration_repository import CollaborationRepository
from database.db_manager import db_manager

router = APIRouter(prefix="/api/auth", tags=["authentication"])
collab_repo = None


def get_collab_repo():
    global collab_repo
    if collab_repo is None:
        collab_repo = CollaborationRepository(db_manager)
    return collab_repo


class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    team_id: Optional[int] = None
    app_package: Optional[str] = None
    platform: Optional[str] = "both"
    is_public: Optional[bool] = False


class CommentCreate(BaseModel):
    session_id: int
    content: str
    parent_id: Optional[int] = None


class ShareCreate(BaseModel):
    session_id: int
    shared_with_user_id: Optional[int] = None
    shared_with_team_id: Optional[int] = None
    permission: Optional[str] = "view"


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request):
    repo = get_collab_repo()
    
    existing_user = await repo.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user_id = await repo.create_user({
        'username': user_data.username,
        'email': user_data.email,
        'password': user_data.password,
        'full_name': user_data.full_name
    })
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    await repo.create_audit_log({
        'user_id': user_id,
        'action': 'user_register',
        'resource_type': 'user',
        'resource_id': user_id,
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent')
    })
    
    user = await repo.get_user_by_id(user_id)
    return UserResponse(**user)


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, request: Request):
    repo = get_collab_repo()
    
    user = await repo.get_user_by_username(user_data.username)
    if not user or not AuthService.verify_password(user_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    await repo.update_last_login(user['id'])
    
    await repo.create_audit_log({
        'user_id': user['id'],
        'action': 'user_login',
        'resource_type': 'user',
        'resource_id': user['id'],
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent')
    })
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user['id']), "username": user['username'], "role": user['role']}
    )
    refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user['id'])}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    repo = get_collab_repo()
    user = await repo.get_user_by_id(current_user['user_id'])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)


@router.post("/teams", response_model=dict)
async def create_team(
    team_data: TeamCreate,
    current_user: dict = Depends(get_current_active_user)
):
    repo = get_collab_repo()
    
    team_id = await repo.create_team({
        'name': team_data.name,
        'description': team_data.description,
        'owner_id': current_user['user_id']
    })
    
    if not team_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create team"
        )
    
    return {"team_id": team_id, "message": "Team created successfully"}


@router.get("/teams/{team_id}/members")
async def get_team_members(
    team_id: int,
    current_user: dict = Depends(get_current_active_user)
):
    repo = get_collab_repo()
    members = await repo.get_team_members(team_id)
    return {"members": members}


@router.post("/projects", response_model=dict)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_active_user)
):
    repo = get_collab_repo()
    
    project_id = await repo.create_project({
        'name': project_data.name,
        'description': project_data.description,
        'team_id': project_data.team_id,
        'owner_id': current_user['user_id'],
        'app_package': project_data.app_package,
        'platform': project_data.platform,
        'is_public': project_data.is_public
    })
    
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )
    
    return {"project_id": project_id, "message": "Project created successfully"}


@router.get("/projects")
async def get_user_projects(current_user: dict = Depends(get_current_active_user)):
    repo = get_collab_repo()
    projects = await repo.get_user_projects(current_user['user_id'])
    return {"projects": projects}


@router.post("/comments", response_model=dict)
async def create_comment(
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_active_user)
):
    repo = get_collab_repo()
    
    comment_id = await repo.create_comment({
        'session_id': comment_data.session_id,
        'user_id': current_user['user_id'],
        'content': comment_data.content,
        'parent_id': comment_data.parent_id
    })
    
    if not comment_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment"
        )
    
    return {"comment_id": comment_id, "message": "Comment created successfully"}


@router.get("/sessions/{session_id}/comments")
async def get_session_comments(
    session_id: int,
    current_user: dict = Depends(get_current_active_user)
):
    repo = get_collab_repo()
    comments = await repo.get_session_comments(session_id)
    return {"comments": comments}


@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    current_user: dict = Depends(get_current_active_user)
):
    repo = get_collab_repo()
    notifications = await repo.get_user_notifications(
        current_user['user_id'],
        unread_only
    )
    return {"notifications": notifications}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_active_user)
):
    repo = get_collab_repo()
    success = await repo.mark_notification_read(
        notification_id,
        current_user['user_id']
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification marked as read"}


@router.post("/sessions/share", response_model=dict)
async def share_session(
    share_data: ShareCreate,
    current_user: dict = Depends(get_current_active_user)
):
    repo = get_collab_repo()
    
    share_id = await repo.share_session({
        'session_id': share_data.session_id,
        'shared_by_user_id': current_user['user_id'],
        'shared_with_user_id': share_data.shared_with_user_id,
        'shared_with_team_id': share_data.shared_with_team_id,
        'permission': share_data.permission
    })
    
    if not share_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share session"
        )
    
    if share_data.shared_with_user_id:
        await repo.create_notification({
            'user_id': share_data.shared_with_user_id,
            'type': 'session_shared',
            'title': '测试会话已分享给您',
            'content': f'用户 {current_user["username"]} 分享了一个测试会话给您',
            'data': {'session_id': share_data.session_id}
        })
    
    return {"share_id": share_id, "message": "Session shared successfully"}
