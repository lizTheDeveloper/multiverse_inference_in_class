"""Session-based authentication integration with Multiverse School.

This module provides authentication by reading Flask session cookies from
the main themultiverse.school application's Firestore session store.
"""

import datetime
import os
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException, status
from google.cloud import firestore
import psycopg2

from app.utils.logger import get_logger
from app.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class SessionAuthenticator:
    """Handles session-based authentication with Firestore."""
    
    def __init__(self):
        """Initialize Firestore client for session validation."""
        self.firestore_client = None
        self.postgres_conn_string = None
        
        # Initialize Firestore client if credentials are available
        try:
            # Use the same project and database as main multiverse school app
            self.firestore_client = firestore.Client(
                project='multiverseschool',
                database='multiverse-sessions'
            )
            logger.info("Firestore session client initialized")
        except Exception as error:
            logger.warning(f"Firestore client not available: {error}")
            
        # Get Postgres connection string from environment
        self.postgres_conn_string = os.environ.get('POSTGRES_CONNECTION_STRING')
        if not self.postgres_conn_string:
            logger.warning("POSTGRES_CONNECTION_STRING not set, session auth will not work")
    
    def get_session_cookie(self, request: Request) -> Optional[str]:
        """Extract Flask session cookie from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Session ID if found, None otherwise
        """
        # Flask default session cookie name is 'session'
        return request.cookies.get('session')
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session against Firestore and get user data.
        
        Args:
            session_id: Session ID from cookie
            
        Returns:
            Session data dict with user_id if valid, None otherwise
        """
        if not self.firestore_client:
            return None
            
        try:
            # Get session document from Firestore
            doc_ref = self.firestore_client.collection('sessions').document(session_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
                
            data = doc.to_dict()
            
            # Check if session has expired
            expires = data.get('expires')
            if not expires:
                return None
                
            # Ensure timezone-aware comparison
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=datetime.timezone.utc)
            
            if expires <= datetime.datetime.now(datetime.timezone.utc):
                logger.debug(f"Session {session_id[:8]}... has expired")
                return None
            
            # Return session data which includes user_id
            session_data = data.get('data', {})
            if 'user_id' in session_data:
                logger.debug(f"Valid session found for user_id: {session_data['user_id']}")
                return session_data
                
            return None
            
        except Exception as error:
            logger.error(f"Failed to validate session: {error}", exc_info=True)
            return None
    
    async def get_user_from_session(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get user details from Postgres using session data.
        
        Args:
            session_data: Session data containing user_id
            
        Returns:
            User dict with admin status, or None if not found
        """
        if not self.postgres_conn_string:
            return None
            
        user_id = session_data.get('user_id')
        if not user_id:
            return None
            
        try:
            conn = psycopg2.connect(self.postgres_conn_string)
            cursor = conn.cursor()
            
            # Query user from students table
            cursor.execute(
                "SELECT id, email, name, admin FROM students WHERE id = %s",
                (user_id,)
            )
            user_row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not user_row:
                return None
                
            return {
                'id': user_row[0],
                'email': user_row[1],
                'name': user_row[2],
                'admin': user_row[3]
            }
            
        except Exception as error:
            logger.error(f"Failed to get user from database: {error}", exc_info=True)
            return None
    
    async def is_admin(self, request: Request) -> bool:
        """Check if the current request is from an authenticated admin user.
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if user is authenticated admin, False otherwise
        """
        # Get session cookie
        session_id = self.get_session_cookie(request)
        if not session_id:
            return False
            
        # Validate session
        session_data = await self.validate_session(session_id)
        if not session_data:
            return False
            
        # Get user details
        user = await self.get_user_from_session(session_data)
        if not user:
            return False
            
        # Check admin status
        return user.get('admin', False) is True


# Global instance
_session_authenticator = None


def get_session_authenticator() -> SessionAuthenticator:
    """Get the global session authenticator instance.
    
    Returns:
        SessionAuthenticator instance
    """
    global _session_authenticator
    if _session_authenticator is None:
        _session_authenticator = SessionAuthenticator()
    return _session_authenticator


async def get_current_user_from_session(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency to get current user from session cookie.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dict if authenticated, None otherwise
    """
    authenticator = get_session_authenticator()
    
    # Get session cookie
    session_id = authenticator.get_session_cookie(request)
    if not session_id:
        return None
        
    # Validate session
    session_data = await authenticator.validate_session(session_id)
    if not session_data:
        return None
        
    # Get user details
    user = await authenticator.get_user_from_session(session_data)
    return user

