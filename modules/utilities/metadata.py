
import os
def is_docker():
    try:
        # Check if /proc/1/cgroup exists and contains "docker"
        with open('/proc/1/cgroup', 'rt') as f:
            return any('docker' in line for line in f)
    except Exception:
        pass

    # Optional: Check for Docker environment variables, commonly set in Docker containers
    docker_env_vars = [
        'DOCKER_CONTAINER',  # Used in some setups
        'container',         # Used in some systems to denote container environment
    ]
    if any(var in os.environ for var in docker_env_vars):
        return True

    return False
name = 'iRoopDeepFaceCam-AVGR'
if is_docker():
    version = 'Docker'
else:
    
    version = '1.3.0'
edition = 'Cuda-12.2'
