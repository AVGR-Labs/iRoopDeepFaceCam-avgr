import ssl
import platform

# monkey patch ssl for mac
if platform.system().lower() == 'darwin':
    ssl._create_default_https_context = ssl._create_unverified_context

