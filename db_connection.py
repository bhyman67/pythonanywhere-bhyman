"""
MySQL Database Connection Module

This module provides a centralized database connection for both Flask app
and scheduled tasks. Uses environment variables for configuration.

Environment variables required (PythonAnywhere):
- MYSQL_HOST: Database host
- MYSQL_USER: Database username
- MYSQL_PASSWORD: Database password
- MYSQL_DATABASE: Database name

Environment variables required (Local with SSH tunnel):
- SSH_HOST: SSH hostname for PythonAnywhere
- SSH_USERNAME: PythonAnywhere username
- SSH_PASSWORD: PythonAnywhere login password
- MYSQL_USER: Database username
- MYSQL_PASSWORD: Database password
- MYSQL_DATABASE: Database name
- MYSQL_REMOTE_HOST: Remote database hostname (e.g., username.mysql.pythonanywhere-services.com)
"""

import os
from sqlalchemy import create_engine

# Global variable to track SSH tunnel
_ssh_tunnel = None

def _is_running_on_pythonanywhere():
    """Check if code is running on PythonAnywhere or locally."""
    # PythonAnywhere sets MYSQL_HOST in environment
    return os.getenv('MYSQL_HOST') is not None

def get_db_engine():
    """
    Get MySQL database engine using environment variables.
    
    On PythonAnywhere: Uses direct connection via MYSQL_HOST
    On local machine: Uses SSH tunnel to connect to PythonAnywhere database
    
    Returns:
        sqlalchemy.engine.Engine: Database engine with connection pooling
        
    Raises:
        ValueError: If required environment variables are missing
    """
    global _ssh_tunnel
    
    mysql_user = os.getenv('MYSQL_USER')
    mysql_password = os.getenv('MYSQL_PASSWORD')
    mysql_database = os.getenv('MYSQL_DATABASE')
    
    if not all([mysql_user, mysql_password, mysql_database]):
        raise ValueError("Missing required MySQL environment variables: MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
    
    if _is_running_on_pythonanywhere():
        # Direct connection on PythonAnywhere
        mysql_host = os.getenv('MYSQL_HOST')
        if not mysql_host:
            raise ValueError("Missing MYSQL_HOST environment variable")
        
        connection_string = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_database}'
        print("Using direct database connection (PythonAnywhere)")
    else:
        # SSH tunnel connection for local development
        try:
            import sshtunnel
        except ImportError:
            raise ImportError("sshtunnel package required for local connections. Install with: pip install sshtunnel")
        
        ssh_host = os.getenv('SSH_HOST')
        ssh_username = os.getenv('SSH_USERNAME')
        ssh_password = os.getenv('SSH_PASSWORD')
        mysql_remote_host = os.getenv('MYSQL_REMOTE_HOST')
        
        if not all([ssh_host, ssh_username, ssh_password, mysql_remote_host]):
            raise ValueError("Missing SSH tunnel environment variables: SSH_HOST, SSH_USERNAME, SSH_PASSWORD, MYSQL_REMOTE_HOST")
        
        # Configure SSH tunnel timeouts
        sshtunnel.SSH_TIMEOUT = 10.0
        sshtunnel.TUNNEL_TIMEOUT = 10.0
        
        # Create SSH tunnel if not already established
        if _ssh_tunnel is None:
            _ssh_tunnel = sshtunnel.SSHTunnelForwarder(
                ssh_host,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                remote_bind_address=(mysql_remote_host, 3306)
            )
            _ssh_tunnel.start()
            print(f"SSH tunnel established on local port {_ssh_tunnel.local_bind_port}")
        
        # Connection string using localhost and tunnel port
        connection_string = f'mysql+pymysql://{mysql_user}:{mysql_password}@127.0.0.1:{_ssh_tunnel.local_bind_port}/{mysql_database}'
        print("Using SSH tunnel connection (local machine)")
    
    # pool_pre_ping=True ensures connections are checked before use
    return create_engine(connection_string, pool_pre_ping=True)

def is_database_available():
    """
    Check if database environment variables are configured.
    
    Returns:
        bool: True if all required environment variables are set, False otherwise
    """
    # Check common required variables
    common_vars = [
        os.getenv('MYSQL_USER'),
        os.getenv('MYSQL_PASSWORD'),
        os.getenv('MYSQL_DATABASE')
    ]
    
    if not all(common_vars):
        return False
    
    # Check environment-specific variables
    if _is_running_on_pythonanywhere():
        return os.getenv('MYSQL_HOST') is not None
    else:
        # Local requires SSH tunnel vars
        return all([
            os.getenv('SSH_HOST'),
            os.getenv('SSH_USERNAME'),
            os.getenv('SSH_PASSWORD'),
            os.getenv('MYSQL_REMOTE_HOST')
        ])

def close_ssh_tunnel():
    """
    Close the SSH tunnel if it's open.
    Call this when shutting down your application (local only).
    """
    global _ssh_tunnel
    if _ssh_tunnel is not None:
        _ssh_tunnel.stop()
        _ssh_tunnel = None
        print("SSH tunnel closed")
