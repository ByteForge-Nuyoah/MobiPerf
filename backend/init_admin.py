import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from database.collaboration_repository import CollaborationRepository
from core.auth import AuthService
from core.config_loader import config
from loguru import logger


async def create_default_admin():
    db_manager = DatabaseManager(config.DATABASE_CONFIG)
    await db_manager.init_pool()
    
    collab_repo = CollaborationRepository(db_manager)
    
    existing_admin = await collab_repo.get_user_by_username('admin')
    
    if existing_admin:
        logger.info("Default admin user already exists")
        logger.info("Username: admin")
        logger.info("Email: admin@mobiperf.com")
        await db_manager.close_pool()
        return
    
    hashed_password = AuthService.hash_password('admin123')
    
    admin_user = await collab_repo.create_user({
        'username': 'admin',
        'email': 'admin@mobiperf.com',
        'password_hash': hashed_password,
        'full_name': 'System Administrator',
        'role': 'admin'
    })
    
    if admin_user:
        logger.success("Default admin user created successfully!")
        logger.info("=" * 50)
        logger.info("Username: admin")
        logger.info("Password: admin123")
        logger.info("Email: admin@mobiperf.com")
        logger.info("=" * 50)
        logger.warning("Please change the default password after first login!")
    else:
        logger.error("Failed to create default admin user")
    
    await db_manager.close_pool()


async def create_test_user():
    db_manager = DatabaseManager(config.DATABASE_CONFIG)
    await db_manager.init_pool()
    
    collab_repo = CollaborationRepository(db_manager)
    
    existing_user = await collab_repo.get_user_by_username('test')
    
    if existing_user:
        logger.info("Test user already exists")
        await db_manager.close_pool()
        return
    
    hashed_password = AuthService.hash_password('test123')
    
    test_user = await collab_repo.create_user({
        'username': 'test',
        'email': 'test@mobiperf.com',
        'password_hash': hashed_password,
        'full_name': 'Test User',
        'role': 'developer'
    })
    
    if test_user:
        logger.success("Test user created successfully!")
        logger.info("Username: test")
        logger.info("Password: test123")
    else:
        logger.error("Failed to create test user")
    
    await db_manager.close_pool()


async def main():
    logger.info("Initializing MobiPerf default users...")
    
    await create_default_admin()
    await create_test_user()
    
    logger.success("User initialization completed!")


if __name__ == "__main__":
    asyncio.run(main())
