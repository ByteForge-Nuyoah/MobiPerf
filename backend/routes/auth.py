from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
from pydantic import BaseModel, EmailStr
from core.auth import (
    AuthService,
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    get_current_user,
    get_current_active_user
)
from database.collaboration_repository import CollaborationRepository
from database.db_manager import DatabaseManager
from core.config_loader import config

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()

db_manager = DatabaseManager(config.DATABASE_CONFIG)
collab_repo = CollaborationRepository(db_manager)

in_memory_users = {}
in_memory_users["admin"] = {
    "id": 1,
    "username": "admin",
    "email": "admin@mobiperf.com",
    "password_hash": AuthService.hash_password("admin123"),
    "full_name": "System Administrator",
    "role": "admin",
    "is_active": True,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


async def get_user_by_username(username: str) -> Optional[Dict]:
    if collab_repo.db.pool:
        return await collab_repo.get_user_by_username(username)
    return in_memory_users.get(username)


async def create_user_in_db(user_data: Dict) -> Optional[Dict]:
    if collab_repo.db.pool:
        return await collab_repo.create_user(user_data)
    
    user_id = len(in_memory_users) + 1
    user = {
        "id": user_id,
        "username": user_data["username"],
        "email": user_data["email"],
        "password_hash": user_data["password_hash"],
        "full_name": user_data.get("full_name"),
        "role": user_data.get("role", "viewer"),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    in_memory_users[user_data["username"]] = user
    logger.info(f"Created user in memory: {user_data['username']}")
    return user


async def update_last_login_in_db(user_id: int):
    if collab_repo.db.pool:
        await collab_repo.update_last_login(user_id)
    logger.info(f"Updated last login for user {user_id}")


@router.post(
    "/register",
    response_model=Token,
    summary="用户注册",
    description="创建新用户账户"
)
async def register(user_data: UserCreate):
    """用户注册
    
    Args:
        user_data: 用户注册信息
        
    Returns:
        访问令牌和刷新令牌
        
    Raises:
        HTTPException: 用户名或邮箱已存在
    """
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    if collab_repo.db.pool:
        existing_email = await collab_repo.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    hashed_password = AuthService.hash_password(user_data.password)
    
    user = await create_user_in_db({
        'username': user_data.username,
        'email': user_data.email,
        'password_hash': hashed_password,
        'full_name': user_data.full_name,
        'role': 'viewer'
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user['id']), "username": user['username'], "role": user['role']}
    )
    refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user['id'])}
    )
    
    logger.info(f"New user registered: {user_data.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post(
    "/login",
    response_model=Token,
    summary="用户登录",
    description="用户登录获取访问令牌"
)
async def login(credentials: UserLogin):
    """用户登录
    
    Args:
        credentials: 登录凭证
        
    Returns:
        访问令牌和刷新令牌
        
    Raises:
        HTTPException: 用户名或密码错误
    """
    user = await get_user_by_username(credentials.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not AuthService.verify_password(credentials.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    await update_last_login_in_db(user['id'])
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user['id']), "username": user['username'], "role": user['role']}
    )
    refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user['id'])}
    )
    
    logger.info(f"User logged in: {credentials.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post(
    "/refresh",
    response_model=Token,
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌"
)
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌
    
    Args:
        request: 刷新令牌请求
        
    Returns:
        新的访问令牌和刷新令牌
        
    Raises:
        HTTPException: 刷新令牌无效
    """
    payload = AuthService.decode_token(request.refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    user_id = payload.get("sub")
    user = await collab_repo.get_user_by_id(int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user['id']), "username": user['username'], "role": user['role']}
    )
    new_refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user['id'])}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息"
)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """获取当前用户信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        用户详细信息
    """
    user_id = current_user['user_id']
    
    if collab_repo.db.pool:
        user = await collab_repo.get_user_by_id(user_id)
    else:
        user = None
        for u in in_memory_users.values():
            if u['id'] == user_id:
                user = u
                break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "full_name": user.get('full_name'),
        "avatar_url": user.get('avatar_url'),
        "role": user['role'],
        "created_at": user['created_at']
    }


@router.post(
    "/change-password",
    summary="修改密码",
    description="修改当前用户密码"
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """修改密码
    
    Args:
        request: 修改密码请求
        current_user: 当前用户
        
    Returns:
        成功消息
        
    Raises:
        HTTPException: 旧密码错误
    """
    user = await collab_repo.get_user_by_id(current_user['user_id'])
    
    if not AuthService.verify_password(request.old_password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    new_hashed_password = AuthService.hash_password(request.new_password)
    await collab_repo.update_user_password(user['id'], new_hashed_password)
    
    logger.info(f"User changed password: {user['username']}")
    
    return {"message": "密码修改成功"}


@router.post(
    "/logout",
    summary="用户登出",
    description="用户登出（客户端应删除令牌）"
)
async def logout(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """用户登出
    
    Args:
        current_user: 当前用户
        
    Returns:
        成功消息
    """
    logger.info(f"User logged out: {current_user['username']}")
    return {"message": "登出成功"}
